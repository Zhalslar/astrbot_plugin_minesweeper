import re
import shutil

from astrbot.api.event import filter
from astrbot.api.star import Context, Star
from astrbot.core import AstrBotConfig
from astrbot.core.platform.astr_message_event import AstrMessageEvent

from .core.command_handler import CommandHandler
from .core.config import PluginConfig
from .core.game_service import GameService
from .core.sender import MessageSender
from .core.skin import SkinManager
from .core.web_controller import WebController


class MinesweeperPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.cfg = PluginConfig(config, context)

        self.skin_mgr = SkinManager(self.cfg)
        self.sender = MessageSender(self.cfg.cache_dir)
        self.game_service = GameService(self.cfg, self.skin_mgr)
        self.web_controller = WebController(
            context=context,
            cfg=self.cfg,
            game_service=self.game_service,
        )
        self.cmd_handler = CommandHandler(
            cfg=self.cfg,
            game_service=self.game_service,
            sender=self.sender,
        )

    async def initialize(self):
        await self.skin_mgr.initialize()

    async def terminate(self):
        if self.cfg.cache_dir.exists():
            shutil.rmtree(self.cfg.cache_dir)

    @filter.command("扫雷", alias={"开始扫雷"})
    async def start_minesweeper(
        self,
        event: AstrMessageEvent,
        difficulty: str = "",
        skin_index: int | None = None,
    ):
        """扫雷 [难度] [皮肤序号]"""
        async for result in self.cmd_handler.start_game(event, difficulty, skin_index):
            yield result

    @filter.command("新建扫雷难度")
    async def start_custom_minesweeper(
        self,
        event: AstrMessageEvent,
        name: str = "",
        rows: int | str | None = None,
        cols: int | str | None = None,
        mines: int | str | None = None,
    ):
        """新建扫雷难度 <名称> <行> <列> <雷数>"""
        error = await self.cfg.add_level(name, rows, cols, mines)
        if error:
            yield event.plain_result(error)
            return
        yield event.plain_result(
            f"已新增难度 {name}：{rows}x{cols} {mines}雷\n使用 “扫雷 {name}” 开始游戏"
        )

    @filter.command("结束扫雷")
    async def stop_minesweeper(self, event: AstrMessageEvent):
        """结束当前群聊的扫雷游戏"""
        result = self.cmd_handler.stop_game(event)
        yield event.plain_result(result)

    @filter.command("雷盘", alias={"查看雷盘"})
    async def show_minesweeper(self, event: AstrMessageEvent):
        """查看当前群聊的扫雷游戏"""
        result = await self.cmd_handler.show_board(event)
        if result:
            yield result

    @filter.regex(r"^[\s\S]*\n[\s\S]*$")
    async def multiline_minesweeper(self, event: AstrMessageEvent):
        """匹配扫雷命令"""
        text = event.message_str
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return

        all_msgs: list[str] = []
        any_changed = False
        game = None

        for line in lines:
            if self.cfg._mark_regex.match(line):
                changed, game, msgs = await self.cmd_handler.mark_positions(
                    event, line, defer_output=True
                )
            elif self.cfg._sweep_regex.match(line):
                changed, game, msgs = await self.cmd_handler.sweep_positions(
                    event, line, defer_output=True
                )
            elif re.match(r"^[a-zA-Z]", line):
                changed, game, msgs = await self.cmd_handler.open_positions(
                    event, line, defer_output=True
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
            await self.cmd_handler.send_board(event, game)

    @filter.regex(r"^[a-zA-Z].*$")
    async def open_minesweeper(self, event: AstrMessageEvent):
        """挖开棋盘上的格子"""
        text = event.message_str.strip()
        if self.cfg._mark_regex.match(text):
            return
        await self.cmd_handler.open_positions(event, text)

    @filter.regex(r"^(标雷|[^\w\s]).*$")
    async def mark_minesweeper(self, event: AstrMessageEvent):
        """标记棋盘上的雷"""
        text = event.message_str.strip()
        if self.cfg._mark_regex.match(text):
            await self.cmd_handler.mark_positions(event, text)

    @filter.regex(r"^(清扫|[^\w\s]).*$")
    async def sweep_minesweeper(self, event: AstrMessageEvent):
        """清扫周围的雷"""
        text = event.message_str.strip()
        if self.cfg._sweep_regex.match(text):
            await self.cmd_handler.sweep_positions(event, text)
