import asyncio
import re
import shutil
from pathlib import Path

from astrbot.api import logger
from astrbot.api.event import filter
from astrbot.api.star import Context, Star
from astrbot.core import AstrBotConfig
from astrbot.core.message.components import Image, Plain
from astrbot.core.platform import AstrMessageEvent
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)
from astrbot.core.star.star_tools import StarTools

from .core.game import GameManager
from .core.mine_sweeper import MineSweeper
from .core.renderer import MineSweeperRenderer
from .core.skin import SkinManager
from .core.utils import set_group_ban
from .sender import MessageSender


class MinesweeperPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

        self.level_preset = self._parse_difficulty_level(config)
        self.level_keys = list(self.level_preset.keys())
        if len(self.level_keys) == 0:
            raise ValueError("没有配置扫雷难度")
        self.default_level = self.level_keys[0]

        self.data_dir = StarTools.get_data_dir()
        self.cache_dir = self.data_dir / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.skins_dir = Path(__file__).parent / "skins"
        self.skin_mgr = SkinManager(self.skins_dir)
        asyncio.create_task(self.skin_mgr.initialize())

        self.font_path = Path(__file__).parent / "font.ttf"

        self.game_mgr = GameManager()
        self._cleanup_task: asyncio.Task | None = None
        self.sender = MessageSender(config)

    async def initialize(self):
        """插件加载时"""
        logger.info("[扫雷] 插件已加载")

    async def terminate(self):
        """插件卸载时"""
        # 重新创建缓存目录
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info("[扫雷] 插件已卸载")

    def _parse_difficulty_level(self, conf: dict) -> dict[str, dict[str, int]]:
        result = {}

        for item in conf.get("difficulty_level", []):
            name, rows, cols, nums = item.split()
            result[name] = {
                "rows": int(rows),
                "cols": int(cols),
                "nums": int(nums),
            }

        return result

    def _save_img_bytes(self, event: AstrMessageEvent, img_bytes: bytes) -> str:
        """把图片 bytes 落盘，返回绝对路径"""
        sid = event.session_id
        uid = event.get_sender_id()
        fname = f"{sid}_{uid}.png"
        fpath = self.cache_dir / fname
        fpath.write_bytes(img_bytes)
        return str(fpath.absolute())

    @filter.command("扫雷", alias={"开始扫雷"})
    async def start_minesweeper(
        self,
        event: AstrMessageEvent,
        level: str | None = None,
        skin_index: int | None = None,
    ):
        """开始扫雷 <初级/中级/高级> <皮肤序号>"""
        sid = event.session_id

        if self.game_mgr.is_running(sid):
            yield event.plain_result("你已经在进行扫雷游戏了")
            return
        level = level or self.default_level
        preset = self.level_preset.get(level)
        if not preset:
            yield event.plain_result(f"难度仅支持：{list(self.level_preset.keys())}")
            return
        rows = preset["rows"]
        cols = preset["cols"]
        nums = preset["nums"]
        skin_name = (
            self.skin_mgr.get_skin_by_index(skin_index - 1)
            if skin_index
            else self.config["default_skin"]
        )
        skin = self.skin_mgr.load(skin_name, rows, cols)

        renderer = MineSweeperRenderer(
            row=rows,
            column=cols,
            mine_num=nums,
            skin=skin,
            font_path=str(self.font_path),
        )
        mine_sweeper = MineSweeper(rows, cols, nums, renderer)

        session = self.game_mgr.create(sid, mine_sweeper)

        yield event.chain_result(
            [
                Plain("扫雷游戏开始！"),
                Image.fromBytes(session.game.draw()),
                Plain(
                    "a1b2c3 —— 挖开格子(无需前缀)\n"
                    "标雷c4  —— 标记地雷\n"
                    "雷盘 —— 查看当前雷盘\n"
                    "结束扫雷  —— 结束扫雷游戏"
                ),
            ]
        )

    @filter.command("结束扫雷")
    async def stop_minesweeper(self, event: AstrMessageEvent):
        if not self.game_mgr.is_running(event.session_id):
            yield event.plain_result("当前没有进行中的扫雷游戏")
            return
        self.game_mgr.stop(event.session_id)
        yield event.plain_result("已结束扫雷游戏")

    @filter.regex(r"^雷盘$")
    async def show_minesweeper(self, event: AstrMessageEvent):
        """查看当前扫雷棋盘"""
        session = self.game_mgr.get(event.session_id)
        if not session:
            return
        img = session.game.draw()
        yield event.chain_result([Image.fromBytes(img)])

    @filter.regex(r"^([a-zA-Z][0-9]+)(\s*[a-zA-Z][0-9]+)*$")
    async def open_minesweeper(self, event: AstrMessageEvent):
        """挖雷命令：支持批量 <A1B2C3>"""
        session = self.game_mgr.get(event.session_id)
        if not session:
            return

        positions = re.findall(r"[a-zA-Z][0-9]+", event.message_str)
        if not positions:
            return

        msgs = []
        for pos in positions:
            result = session.open(pos)
            if result.game_over:
                self.game_mgr.stop(event.session_id)
                break
        if len(msgs) > 0:
            yield event.plain_result("\n".join(msgs))

        img = session.game.draw()
        img_path = self._save_img_bytes(event ,img)
        await self.sender.send_img_replace_last(event, img_path)

        if (
            session.game.fail
            and isinstance(event, AiocqhttpMessageEvent)
            and self.config["ban_time"] > 0
        ):
            await set_group_ban(event, ban_time=self.config["ban_time"])

    @filter.regex(r"^标雷(\s*[a-zA-Z][0-9]+)+$")
    async def mark_minesweeper(self, event: AstrMessageEvent):
        session = self.game_mgr.get(event.session_id)
        if not session:
            return

        positions = re.findall(r"[a-zA-Z][0-9]+", event.message_str)
        if not positions:
            return

        msgs = []
        for pos in positions:
            result = session.mark(pos)
            if result.message:
                msgs.append(result.message)
        if len(msgs) > 0:
            yield event.plain_result("\n".join(msgs))

        img = session.game.draw()
        img_path = self._save_img_bytes(event, img)
        await self.sender.send_img_replace_last(event, img_path)
