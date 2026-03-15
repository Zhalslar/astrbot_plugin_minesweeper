import asyncio
from collections.abc import Callable

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent
from astrbot.core.message.components import Image, Plain
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)

from .game import GameManager, MineSweeper
from .model import GameSpec, MarkResult, OpenResult, SweepResult
from .renderer import MineSweeperRenderer
from .skin import SkinManager
from .config import PluginConfig
from .image_service import ImageService
from .gui_launcher import GuiLauncher
from .utils import parse_position, parse_position_tokens, set_group_ban


class GameInitializer:
    """游戏初始化器 - 处理参数解析与游戏创建"""

    def __init__(
        self,
        cfg: PluginConfig,
        skin_mgr: SkinManager,
    ):
        self.cfg = cfg
        self.skin_mgr = skin_mgr

    @staticmethod
    def _parse_int(value: str) -> int | None:
        if value and value.isdigit():
            return int(value)
        return None

    @staticmethod
    def _build_custom_spec(
        rows: int, cols: int, mines: int
    ) -> tuple[GameSpec | None, str | None]:
        if rows <= 0 or cols <= 0:
            return None, "行数和列数必须大于 0"
        if mines <= 0:
            return None, "雷数必须大于 0"
        if mines >= rows * cols:
            return None, "雷数必须小于格子总数"
        return GameSpec(rows, cols, mines), None

    def parse_args(
        self, args: list[str]
    ) -> tuple[GameSpec | None, int | None, str | None]:
        """
        解析扫雷命令参数
        返回：(spec, skin_index, error_message)
        """
        if not args:
            return (
                None,
                None,
                "用法：扫雷 <难度> <皮肤序号> 或 扫雷 <行> <列> <雷数> <皮肤序号>",
            )

        spec: GameSpec | None = None
        skin_index: int | None = None

        if self.cfg.is_supported_level(args[0]):
            spec = self.cfg.get_spec(args[0])
            if len(args) > 1:
                skin_index = self._parse_int(args[1])
            return spec, skin_index, None

        custom_values: tuple[int, int, int] | None = None

        if len(args) >= 3:
            row = self._parse_int(args[0])
            col = self._parse_int(args[1])
            mines = self._parse_int(args[2])

            if row is not None and col is not None and mines is not None:
                custom_values = (row, col, mines)
                if len(args) > 3:
                    skin_index = self._parse_int(args[3])
            elif args[0] == "自定义" and len(args) >= 4:
                row = self._parse_int(args[1])
                col = self._parse_int(args[2])
                mines = self._parse_int(args[3])
                if row is not None and col is not None and mines is not None:
                    custom_values = (row, col, mines)
                    if len(args) > 4:
                        skin_index = self._parse_int(args[4])

        if custom_values is None:
            return (
                None,
                None,
                "用法：扫雷 <难度> <皮肤序号> 或 扫雷 <行> <列> <雷数> <皮肤序号>",
            )

        spec, err = self._build_custom_spec(*custom_values)
        if err:
            return None, None, err

        return spec, skin_index, None

    def create_game(
        self, spec: GameSpec, skin_index: int | None, renderer_font_path: str
    ) -> MineSweeper:
        """创建游戏实例"""
        skin_name = (
            self.skin_mgr.get_skin_by_index(skin_index - 1)
            if skin_index
            else self.cfg.default_skin
        )
        skin = self.skin_mgr.load(skin_name, spec)

        renderer = MineSweeperRenderer(
            spec=spec,
            skin=skin,
            font_path=renderer_font_path,
        )

        return MineSweeper(spec, renderer)


class GameActionHandler:
    """游戏操作处理器 - 处理挖开/标记等操作的公共逻辑"""

    def __init__(
        self,
        game_mgr: GameManager,
        image_service: ImageService,
        ban_time: int,
    ):
        self.game_mgr = game_mgr
        self.image_service = image_service
        self.ban_time = ban_time

    async def handle_positions(
        self,
        event: AstrMessageEvent,
        tokens: list[str],
        action: Callable,
        result_handler: Callable,
        *,
        send_msgs: bool = True,
        send_board: bool = True,
    ) -> tuple[bool, MineSweeper | None, list[str]]:

        game = self.game_mgr.get(event.session_id)
        if not game:
            return False, None, []

        positions, invalid_tokens = parse_position_tokens(tokens)
        msgs: list[str] = []
        changed = False

        if invalid_tokens:
            msgs.append("不支持的坐标表达式：" + " ".join(invalid_tokens))

        for pos in positions:
            xy = parse_position(pos)
            if not xy:
                msgs.append(f"位置 {pos} 不合法")
                continue

            res = action(game, *xy)
            error_msg = result_handler(res, pos)

            if res is None:
                changed = True
            elif isinstance(res, OpenResult):
                if res in (OpenResult.FAIL, OpenResult.WIN):
                    changed = True
            elif isinstance(res, MarkResult):
                if res == MarkResult.WIN:
                    changed = True
            elif isinstance(res, SweepResult) and res in (
                SweepResult.SUCCESS,
                SweepResult.WIN,
                SweepResult.FAIL,
            ):
                changed = True

            if error_msg:
                msgs.append(error_msg)

            if game.is_over:
                self.game_mgr.stop(event.session_id)
                break

        if msgs and send_msgs:
            await event.send(event.plain_result("\n".join(msgs)))

        if changed and send_board:
            img_path = self.image_service.save_cache(event, game.draw())
            await self.image_service.send_with_replace(event, img_path)

        return changed, game, msgs

    @staticmethod
    def open_result_handler(res: OpenResult, pos: str) -> str | None:
        """挖开操作结果处理"""
        if res == OpenResult.OUT:
            return f"{pos} 超出边界"
        if res == OpenResult.FAIL:
            return "很遗憾，游戏失败"
        if res == OpenResult.WIN:
            return "恭喜你获得游戏胜利！"
        return None

    @staticmethod
    def mark_result_handler(res: MarkResult, pos: str) -> str | None:
        """标记操作结果处理"""
        if res == MarkResult.OUT:
            return f"{pos} 超出边界"
        if res == MarkResult.OPENED:
            return None  # 已挖开不提示（防刷屏）
        if res == MarkResult.WIN:
            return "恭喜你获得游戏胜利！"
        return None

    @staticmethod
    def sweep_result_handler(res: SweepResult, pos: str) -> str | None:
        """清扫操作结果处理"""
        if res == SweepResult.OUT:
            return f"{pos} 超出边界"
        if res == SweepResult.NOT_OPENED:
            return f"{pos} 未挖开，无法清扫"
        if res == SweepResult.CONDITION_NOT_MET:
            return f"{pos} 不满足清扫条件"
        if res == SweepResult.FAIL:
            return "很遗憾，游戏失败"
        if res == SweepResult.WIN:
            return "恭喜你获得游戏胜利！"
        return None  # SUCCESS


class CommandHandler:
    """命令处理器 - 整合游戏初始化和操作处理"""

    def __init__(
        self,
        cfg: PluginConfig,
        skin_mgr: SkinManager,
        game_mgr: GameManager,
        image_service: ImageService,
        gui_launcher: GuiLauncher,
        loop: asyncio.AbstractEventLoop,
    ):
        self.cfg = cfg
        self.game_mgr = game_mgr
        self.image_service = image_service
        self.gui_launcher = gui_launcher
        self.loop = loop

        self.initializer = GameInitializer(cfg, skin_mgr)
        self.action_handler = GameActionHandler(game_mgr, image_service, cfg.ban_time)

    async def start_game(self, event: AstrMessageEvent, args: list[str]):
        """处理开始游戏命令"""
        sid = event.session_id
        uid = event.get_sender_id()

        if self.game_mgr.is_running(sid):
            logger.debug(f"[扫雷] 用户 {uid} 已在使用游戏中，拒绝新请求")
            yield event.plain_result("你已经在进行扫雷游戏了")
            return

        spec, skin_index, err = self.initializer.parse_args(args)
        if err:
            logger.debug(f"[扫雷] 用户 {uid} 参数解析失败：{err}")
            yield event.plain_result(err)
            return

        if spec is None:
            yield event.plain_result("无法解析游戏参数")
            return

        game = self.initializer.create_game(spec, skin_index, str(self.cfg.font_path))
        self.game_mgr.create(sid, game)
        logger.info(
            f"[扫雷] 用户 {uid} 开始游戏 {spec.rows}x{spec.cols} {spec.mines}雷"
        )

        def send_board():
            img_bytes = game.draw()
            img_path = self.image_service.save_cache(event, img_bytes)
            asyncio.run_coroutine_threadsafe(
                self.image_service.send_with_replace(event, img_path),
                self.loop,
            )

        game.on_send_board(send_board)

        if self.gui_launcher.should_launch():
            self.gui_launcher.launch(game)

        # 动态生成快捷键帮助文本
        mark_examples = " ".join(f"{s}a1" for s in self.cfg.mark_shortcuts)
        sweep_examples = " ".join(f"{s}a1" for s in self.cfg.sweep_shortcuts)

        yield event.chain_result(
            [
                Plain("扫雷游戏开始！"),
                Image.fromBytes(game.draw()),
                Plain(
                    f"a1 a-c5 a1-5 —— 挖开格子\n"
                    f"{mark_examples} —— 标记地雷\n"
                    f"{sweep_examples} —— 清扫周围（标记数=数字时自动挖开）\n"
                    f"雷盘 —— 查看棋盘\n"
                    f"结束扫雷 —— 结束游戏"
                ),
            ]
        )

    def stop_game(self, event: AstrMessageEvent):
        """处理结束游戏命令"""
        uid = event.get_sender_id()
        if not self.game_mgr.is_running(event.session_id):
            logger.debug(f"[扫雷] 用户 {uid} 尝试结束不存在的游戏")
            return "当前没有进行中的扫雷游戏"
        self.game_mgr.stop(event.session_id)
        logger.info(f"[扫雷] 用户 {uid} 结束游戏")
        return "已结束扫雷游戏"

    async def show_board(self, event: AstrMessageEvent):
        """处理查看棋盘命令"""
        game = self.game_mgr.get(event.session_id)
        if not game:
            logger.debug(f"[扫雷] 用户 {event.get_sender_id()} 查看不存在的棋盘")
            return None
        logger.debug(f"[扫雷] 用户 {event.get_sender_id()} 查看棋盘")
        return event.chain_result([Image.fromBytes(game.draw())])

    async def open_positions(
        self,
        event: AstrMessageEvent,
        tokens: list[str],
        *,
        defer_output: bool = False,
    ) -> tuple[bool, MineSweeper | None, list[str]]:
        """处理挖开格子操作"""
        uid = event.get_sender_id()
        logger.debug(f"[扫雷] 用户 {uid} 挖开位置：{tokens}")

        changed, game, msgs = await self.action_handler.handle_positions(
            event,
            tokens,
            lambda g, x, y: g.open(x, y),
            self.action_handler.open_result_handler,
            send_msgs=not defer_output,
            send_board=not defer_output,
        )

        if (
            not defer_output
            and changed
            and game
            and game.is_fail
            and isinstance(event, AiocqhttpMessageEvent)
        ):
            if self.cfg.ban_time > 0:
                logger.info(f"[扫雷] 用户 {uid} 游戏失败，禁言 {self.cfg.ban_time} 秒")
                await set_group_ban(event, ban_time=self.cfg.ban_time)
            else:
                logger.info(f"[扫雷] 用户 {uid} 游戏失败")

        return changed, game, msgs

    async def mark_positions(
        self,
        event: AstrMessageEvent,
        tokens: list[str],
        *,
        defer_output: bool = False,
    ) -> tuple[bool, MineSweeper | None, list[str]]:
        uid = event.get_sender_id()
        logger.debug(f"[扫雷] 用户 {uid} 标记位置：{tokens}")

        changed, game, msgs = await self.action_handler.handle_positions(
            event,
            tokens,
            lambda g, x, y: g.mark(x, y),
            self.action_handler.mark_result_handler,
            send_msgs=not defer_output,
            send_board=not defer_output,
        )
        return changed, game, msgs

    async def sweep_positions(
        self,
        event: AstrMessageEvent,
        tokens: list[str],
        *,
        defer_output: bool = False,
    ) -> tuple[bool, MineSweeper | None, list[str]]:
        uid = event.get_sender_id()
        logger.debug(f"[扫雷] 用户 {uid} 清扫位置：{tokens}")

        changed, game, msgs = await self.action_handler.handle_positions(
            event,
            tokens,
            lambda g, x, y: g.sweep(x, y),
            self.action_handler.sweep_result_handler,
            send_msgs=not defer_output,
            send_board=not defer_output,
        )
        return changed, game, msgs

    async def send_board(
        self, event: AstrMessageEvent, game: MineSweeper | None = None
    ) -> bool:
        if game is None:
            game = self.game_mgr.get(event.session_id)
        if not game:
            return False
        img_path = self.image_service.save_cache(event, game.draw())
        await self.image_service.send_with_replace(event, img_path)
        return True
