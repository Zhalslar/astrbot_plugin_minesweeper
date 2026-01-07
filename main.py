import asyncio
import re
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

LEVEL_PRESET = {
    "初级": {"rows": 8, "cols": 8, "nums": 10},
    "中级": {"rows": 16, "cols": 16, "nums": 40},
    "高级": {"rows": 16, "cols": 30, "nums": 99},
}


class MinesweeperPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

        self.data_dir = StarTools.get_data_dir()
        self.cache_dir = self.data_dir / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.skins_dir = Path(__file__).parent / "skins"
        self.skin_mgr = SkinManager(self.skins_dir)

        self.game_mgr = GameManager()
        self._cleanup_task: asyncio.Task | None = None
        self.sender = MessageSender(config)

    async def initialize(self):
        """插件加载时"""
        logger.info("[扫雷] 插件已加载")

    async def terminate(self):
        """插件卸载时"""
        logger.info("[扫雷] 插件已卸载")

    def _save_img_bytes(self, sid: str, img_bytes: bytes) -> str:
        """把图片 bytes 落盘，返回绝对路径"""
        fname = f"{sid}.png"
        fpath = self.cache_dir / fname
        fpath.write_bytes(img_bytes)
        return str(fpath.absolute())

    @filter.command("扫雷", alias={"开始扫雷"})
    async def start_minesweeper(
        self,
        event: AstrMessageEvent,
        level: str = "初级",
        skin_index: int | None = None,
    ):
        """开始扫雷 <初级/中级/高级> <皮肤序号>"""
        sid = event.session_id

        if self.game_mgr.is_running(sid):
            yield event.plain_result("你已经在进行扫雷游戏了")
            return

        preset = LEVEL_PRESET.get(level)
        if not preset:
            yield event.plain_result("难度仅支持：初级 / 中级 / 高级")
            return

        skin_name = (
            self.skin_mgr.get_skin_by_index(skin_index + 1)
            if skin_index
            else self.config["default_skin"]
        )
        rows = preset["rows"]
        cols = preset["cols"]
        nums = preset["nums"]
        skin = self.skin_mgr.load(skin_name, rows, cols)

        renderer = MineSweeperRenderer(
            row=rows,
            column=cols,
            mine_num=nums,
            skin=skin,
        )
        mine_sweeper = MineSweeper(rows, cols, nums, renderer)

        session = self.game_mgr.create(sid, mine_sweeper)

        yield event.chain_result(
            [
                Plain("扫雷游戏开始！"),
                Image.fromBytes(session.game.draw()),
                Plain(
                    "a1 —— 挖开格子(无需前缀)\n"
                    "标雷 b2  —— 标记地雷\n"
                    "雷盘 —— 查看当前雷盘\n"
                    "结束扫雷  —— 强制扫雷游戏\n"
                ),
            ]
        )

    @filter.regex(r"^结束扫雷$")
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
            yield event.plain_result("当前没有进行中的扫雷游戏")
            return
        img = session.game.draw()
        yield event.chain_result([Image.fromBytes(img)])

    @filter.regex(r"^([a-zA-Z][0-9]+)(\s+[a-zA-Z][0-9]+)*$")
    async def open_minesweeper(self, event: AstrMessageEvent):
        """挖雷命令：支持批量 <A1 B2 C3>"""
        session = self.game_mgr.get(event.session_id)
        if not session:
            yield event.plain_result("请先使用“扫雷”开始游戏")
            return

        msg = event.message_str.strip()

        positions = re.findall(r"[a-zA-Z][0-9]+", msg)
        if not positions:
            return

        game_over = False
        last_message = None

        for pos in positions:
            result = session.open(pos)
            if result.message:
                last_message = result.message

            if result.game_over:
                game_over = True
                break

        if last_message:
            yield event.plain_result(last_message)

        img = session.game.draw()
        img_path = self._save_img_bytes(event.session_id, img)
        await self.sender.send_img_replace_last(event, img_path)

        if game_over:
            self.game_mgr.stop(event.session_id)

        if (
            session.game.fail
            and isinstance(event, AiocqhttpMessageEvent)
            and self.config["ban_time"] > 0
        ):
            await set_group_ban(event, ban_time=self.config["ban_time"])

    @filter.regex(r"^标雷(\s+[a-zA-Z][0-9]+)+$")
    async def mark_minesweeper(self, event: AstrMessageEvent):
        session = self.game_mgr.get(event.session_id)
        if not session:
            yield event.plain_result("请先使用“扫雷”开始游戏")
            return

        # 提取所有坐标
        positions = re.findall(r"[a-zA-Z][0-9]+", event.message_str)
        if not positions:
            return

        game_over = False
        last_message = None

        for pos in positions:
            result = session.mark(pos)

            if result.message:
                last_message = result.message

            if result.game_over:
                game_over = True
                break

        if last_message:
            yield event.plain_result(last_message)

        img = session.game.draw()
        img_path = self._save_img_bytes(event.session_id, img)
        await self.sender.send_img_replace_last(event, img_path)

        if game_over:
            self.game_mgr.stop(event.session_id)
