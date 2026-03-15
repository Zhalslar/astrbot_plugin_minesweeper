import asyncio
import re
import shutil

from astrbot.api import logger
from astrbot.api.event import filter
from astrbot.api.star import Context, Star
from astrbot.core import AstrBotConfig
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)

from .core.command_handler import CommandHandler
from .core.config import PluginConfig
from .core.game import GameManager
from .core.gui_launcher import GuiLauncher
from .core.image_service import ImageService
from .core.skin import SkinManager


class MinesweeperPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.cfg = PluginConfig(config, context)
        self.skin_mgr = SkinManager(self.cfg)
        self.game_mgr = GameManager()

        self._cmd_handler: CommandHandler | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._mark_regex = None
        self._sweep_regex = None

    async def initialize(self):
        """插件加载时"""
        self._loop = asyncio.get_running_loop()
        await self.skin_mgr.initialize()

        image_service = ImageService(self.cfg.astrbot_config, self.cfg.cache_dir)
        gui_launcher = GuiLauncher(self.cfg.use_gui)

        self._cmd_handler = CommandHandler(
            cfg=self.cfg,
            skin_mgr=self.skin_mgr,
            game_mgr=self.game_mgr,
            image_service=image_service,
            gui_launcher=gui_launcher,
            loop=self._loop,
        )

        self._build_mark_regex()
        self._build_sweep_regex()
        logger.info("[扫雷] 插件已加载")

    def _build_mark_regex(self):
        """根据配置构建标雷正则"""
        prefix = self.cfg.mark_pattern
        self._mark_regex = re.compile(rf"^{prefix}\s*[a-zA-Z]")

    def _build_sweep_regex(self):
        """根据配置构建清扫正则"""
        prefix = self.cfg.sweep_pattern
        self._sweep_regex = re.compile(rf"^{prefix}\s*[a-zA-Z]")

    async def terminate(self):
        """插件卸载时"""
        if self.cfg.cache_dir.exists():
            shutil.rmtree(self.cfg.cache_dir)

    @filter.command("扫雷", alias={"开始扫雷"})
    async def start_minesweeper(
        self,
        event,
        arg1: str = "",
        arg2: str = "",
        arg3: str = "",
        arg4: str = "",
        arg5: str = "",
    ):
        if not self._cmd_handler:
            logger.error("[扫雷] 命令处理器未初始化")
            return
        args = [arg for arg in [arg1, arg2, arg3, arg4, arg5] if arg]
        logger.debug(f"[扫雷] 开始游戏命令，参数：{args}")
        async for result in self._cmd_handler.start_game(event, args):
            yield result

    @filter.command("结束扫雷")
    async def stop_minesweeper(self, event):
        if not self._cmd_handler:
            return
        logger.debug(f"[扫雷] 结束游戏命令，用户：{event.get_sender_id()}")
        result = self._cmd_handler.stop_game(event)
        yield event.plain_result(result)

    @filter.regex(r"^雷盘$")
    async def show_minesweeper(self, event):
        if not self._cmd_handler:
            return
        logger.debug(f"[扫雷] 查看棋盘命令，用户：{event.get_sender_id()}")
        result = await self._cmd_handler.show_board(event)
        if result:
            yield result

    @filter.regex(r"^[\s\S]*\n[\s\S]*$")
    async def multiline_minesweeper(self, event):
        if not self._cmd_handler or not self._mark_regex or not self._sweep_regex:
            return

        text = event.message_str
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return

        all_msgs: list[str] = []
        any_changed = False
        game = None

        for line in lines:
            if self._mark_regex.match(line):
                prefix = self._get_mark_prefix(line)
                tokens = self._extract_positions(line, prefix)
                changed, game, msgs = await self._cmd_handler.mark_positions(
                    event, tokens, defer_output=True
                )
            elif self._sweep_regex.match(line):
                prefix = self._get_sweep_prefix(line)
                tokens = self._extract_positions(line, prefix)
                changed, game, msgs = await self._cmd_handler.sweep_positions(
                    event, tokens, defer_output=True
                )
            elif re.match(r"^[a-zA-Z]", line):
                tokens = self._extract_positions(line)
                changed, game, msgs = await self._cmd_handler.open_positions(
                    event, tokens, defer_output=True
                )
            else:
                continue

            if msgs:
                all_msgs.extend(msgs)
            if changed:
                any_changed = True
            if game and game.is_over:
                break

        if all_msgs:
            await event.send(event.plain_result("\n".join(all_msgs)))

        if any_changed:
            await self._cmd_handler.send_board(event, game)

        # 多行命令后的禁言检查（与单行命令保持一致）
        if (
            any_changed
            and game
            and game.is_fail
            and isinstance(
                event,
                AiocqhttpMessageEvent,
            )
            and self._cmd_handler.cfg.ban_time > 0
        ):
            logger.info(
                f"[扫雷] 用户 {event.get_sender_id()} 游戏失败，禁言 {self._cmd_handler.cfg.ban_time} 秒"
            )
            from .core.utils import set_group_ban

            await set_group_ban(event, ban_time=self._cmd_handler.cfg.ban_time)

    @filter.regex(r"^[a-zA-Z].*$")
    async def open_minesweeper(self, event):
        if not self._cmd_handler or not self._mark_regex:
            return
        text = event.message_str.strip()
        if "\n" in text:
            return
        if self._mark_regex.match(text):
            return
        tokens = self._extract_positions(text)
        if not tokens:
            return
        logger.debug(f"[扫雷] 挖开命令，原始消息：{event.message_str}")
        await self._cmd_handler.open_positions(event, tokens)

    @filter.regex(r"^(标雷|[^\w\s]).*$")
    async def mark_minesweeper(self, event):
        if not self._cmd_handler or not self._mark_regex:
            return
        text = event.message_str.strip()
        if "\n" in text:
            return
        if not self._mark_regex.match(text):
            return
        prefix = self._get_mark_prefix(text)
        tokens = self._extract_positions(text, prefix)
        logger.debug(f"[扫雷] 标雷命令，原始消息：{event.message_str}, 前缀：{prefix}")
        await self._cmd_handler.mark_positions(event, tokens)

    @filter.regex(r"^(清扫|[^\w\s]).*$")
    async def sweep_minesweeper(self, event):
        if not self._cmd_handler or not self._sweep_regex:
            return
        text = event.message_str.strip()
        if "\n" in text:
            return
        if not self._sweep_regex.match(text):
            return
        prefix = self._get_sweep_prefix(text)
        tokens = self._extract_positions(text, prefix)
        logger.debug(f"[扫雷] 清扫命令，原始消息：{event.message_str}, 前缀：{prefix}")
        await self._cmd_handler.sweep_positions(event, tokens)

    def _get_prefix(self, text: str, shortcuts: list[str], keyword: str) -> str | None:
        """通用：获取操作前缀"""
        for shortcut in shortcuts:
            if text.startswith(shortcut):
                return shortcut
        if text.startswith(keyword):
            return keyword
        return None

    def _get_mark_prefix(self, text: str) -> str | None:
        return self._get_prefix(text, self.cfg.mark_shortcuts, "标雷")

    def _get_sweep_prefix(self, text: str) -> str | None:
        return self._get_prefix(text, self.cfg.sweep_shortcuts, "清扫")

    @staticmethod
    def _extract_positions(text: str, prefix: str | None = None) -> list[str]:
        """通用：从文本中提取坐标列表"""
        from .core.utils import tokenize_positions

        text = text.strip()
        if prefix:
            text = text[len(prefix) :]
        return tokenize_positions(text.strip())
