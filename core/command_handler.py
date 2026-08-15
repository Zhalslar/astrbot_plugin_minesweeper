import re

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent
from astrbot.core.message.components import Image, Plain
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)

from .config import PluginConfig
from .game import MineSweeper
from .game_service import GameService
from .model import MarkResult, OpenResult, SweepResult
from .sender import MessageSender

_POSITION_PATTERN = re.compile(
    r"[a-zA-Z]\d+-[a-zA-Z]\d+|[a-zA-Z](?:-[a-zA-Z])?\d+(?:-\d+)?|[a-zA-Z]-[a-zA-Z]\d+"
)
_SINGLE_POS_RE = re.compile(r"^([a-z])(\d+)$", re.I)
_ROW_RANGE_RE = re.compile(r"^([a-z])-([a-z])(\d+)$", re.I)
_COL_RANGE_RE = re.compile(r"^([a-z])(\d+)-(\d+)$", re.I)
_RECT_RANGE_RE = re.compile(r"^([a-z])(\d+)-([a-z])(\d+)$", re.I)


async def _get_group_name(event: AstrMessageEvent, fallback: str) -> str:
    if not isinstance(event, AiocqhttpMessageEvent):
        return fallback
    group_id = event.get_group_id()
    if not group_id:
        return fallback
    try:
        group_info = await event.bot.call_action(
            "get_group_info", group_id=int(group_id)
        )
    except Exception:
        return fallback
    return group_info.get("group_name") or fallback


def _expand_position_token(token: str) -> list[str] | None:
    token = token.strip()
    match = _SINGLE_POS_RE.match(token)
    if match:
        return [f"{match.group(1).lower()}{int(match.group(2))}"]

    match = _RECT_RANGE_RE.match(token)
    if match:
        start_row = ord(match.group(1).lower())
        start_col = int(match.group(2))
        end_row = ord(match.group(3).lower())
        end_col = int(match.group(4))
        row_step = 1 if end_row >= start_row else -1
        col_step = 1 if end_col >= start_col else -1
        return [
            f"{chr(row)}{col}"
            for row in range(start_row, end_row + row_step, row_step)
            for col in range(start_col, end_col + col_step, col_step)
        ]

    match = _ROW_RANGE_RE.match(token)
    if match:
        start = ord(match.group(1).lower())
        end = ord(match.group(2).lower())
        col = int(match.group(3))
        step = 1 if end >= start else -1
        return [f"{chr(row)}{col}" for row in range(start, end + step, step)]

    match = _COL_RANGE_RE.match(token)
    if match:
        row = match.group(1).lower()
        start = int(match.group(2))
        end = int(match.group(3))
        step = 1 if end >= start else -1
        return [f"{row}{col}" for col in range(start, end + step, step)]

    return None


class CommandHandler:
    def __init__(
        self,
        cfg: PluginConfig,
        sender: MessageSender,
        game_service: GameService,
    ):
        self.cfg = cfg
        self.game_service = game_service
        self.sender = sender

    @staticmethod
    def _game_key(event: AstrMessageEvent) -> str:
        return event.unified_msg_origin

    async def start_game(
        self,
        event: AstrMessageEvent,
        difficulty: str,
        skin_index: int | None,
    ):
        umo = self._game_key(event)
        uid = event.get_sender_id()
        show_level = not difficulty
        difficulty = difficulty or self.cfg.default_difficulty

        if (
            existing_game := self.game_service.get(umo)
        ) is not None and not existing_game.is_over:
            logger.debug(f"[扫雷] 用户 {uid} 已在使用游戏中，拒绝新请求")
            yield event.plain_result("你已经在进行扫雷游戏了")
            return

        if existing_game is not None and existing_game.is_over:
            self.game_service.stop(umo)

        if not self.cfg.is_supported_level(difficulty):
            usage = "用法：扫雷 <难度> [皮肤序号]"
            logger.debug(f"[扫雷] 用户 {uid} 参数解析失败：{usage}")
            yield event.plain_result(usage)
            return
        spec = self.cfg.get_spec(difficulty)

        display_name = await _get_group_name(event, umo)
        game = self.game_service.start(
            umo, spec, skin_index, display_name, can_push=True
        )
        logger.info(
            f"[扫雷] 用户 {uid} 开始游戏 {spec.rows}x{spec.cols} {spec.mines}雷"
        )

        separator = "、"
        prompt = (
            f"可选难度：{separator.join(self.cfg.level_keys)}\n" if show_level else ""
        )
        yield event.chain_result(
            [
                Plain(f"扫雷游戏开始！[{difficulty}]"),
                Image.fromBytes(game.draw()),
                Plain(
                    prompt
                    + "a1 a-c5 a1-5 —— 挖开格子\n"
                    + f"{self.cfg.mark_prefix}a1 —— 标记地雷\n"
                    + f"{self.cfg.sweep_prefix}a1 —— 清扫周围\n"
                    + "雷盘 —— 查看棋盘\n"
                    + "结束扫雷 —— 结束游戏"
                ),
            ]
        )

    def stop_game(self, event: AstrMessageEvent):
        uid = event.get_sender_id()
        umo = self._game_key(event)
        if not self.game_service.is_running(umo):
            logger.debug(f"[扫雷] 用户 {uid} 尝试结束不存在的游戏")
            return "当前没有进行中的扫雷游戏"
        self.game_service.stop(umo)
        logger.info(f"[扫雷] 用户 {uid} 结束游戏")
        return "已结束扫雷游戏"

    async def show_board(self, event: AstrMessageEvent):
        game = self.game_service.get(self._game_key(event))
        if not game:
            logger.debug(f"[扫雷] 用户 {event.get_sender_id()} 查看不存在的棋盘")
            return None
        logger.debug(f"[扫雷] 用户 {event.get_sender_id()} 查看棋盘")
        return event.chain_result([Image.fromBytes(game.draw())])

    async def send_board(
        self, event: AstrMessageEvent, game: MineSweeper | None = None
    ) -> bool:
        if game is None:
            game = self.game_service.get(self._game_key(event))
        if not game:
            return False
        img_path = self.sender.save_cache(event, game.draw())
        await self.sender.send_img_replace_last(event, img_path)
        return True

    async def _handle_positions(
        self,
        event: AstrMessageEvent,
        text: str,
        action: str,
        *,
        defer_output: bool = False,
    ) -> tuple[bool, MineSweeper | None, list[str]]:
        game = self.game_service.get(self._game_key(event))
        if not game:
            return False, None, []

        prefix = None
        if action == "mark":
            prefix = self.cfg._get_mark_prefix(text)
        elif action == "sweep":
            prefix = self.cfg._get_sweep_prefix(text)
        if prefix:
            text = text[len(prefix) :].strip()

        msgs = []
        changed = False
        for token in _POSITION_PATTERN.findall(text):
            for pos in _expand_position_token(token) or []:
                x = ord(pos[0]) - ord("a")
                y = int(pos[1:]) - 1
                result = self.game_service.apply(self._game_key(event), action, x, y)
                message = None

                match result:
                    case None:
                        changed = True
                    case OpenResult.OUT | MarkResult.OUT | SweepResult.OUT:
                        message = f"{pos} 超出边界"
                    case OpenResult.FAIL | SweepResult.FAIL:
                        changed = True
                        message = "很遗憾，游戏失败"
                    case OpenResult.WIN | MarkResult.WIN | SweepResult.WIN:
                        changed = True
                        message = "恭喜你获得游戏胜利！"
                    case SweepResult.NOT_OPENED:
                        message = f"{pos} 未挖开，无法清扫"
                    case SweepResult.CONDITION_NOT_MET:
                        message = f"{pos} 不满足清扫条件"
                    case SweepResult.SUCCESS:
                        changed = True

                if message:
                    msgs.append(message)
                if game.is_over:
                    break
            if game.is_over:
                break

        if msgs and not defer_output:
            await event.send(event.plain_result("\n".join(msgs)))
        if changed and not defer_output:
            await self.send_board(event, game)
        if changed and game.is_fail and isinstance(event, AiocqhttpMessageEvent):
            if self.cfg.ban_time > 0:
                logger.info(
                    f"[扫雷] 用户 {event.get_sender_id()} 游戏失败，禁言 {self.cfg.ban_time} 秒"
                )
                try:
                    await event.bot.set_group_ban(
                        group_id=int(event.get_group_id()),
                        user_id=int(event.get_sender_id()),
                        duration=self.cfg.ban_time,
                    )
                except Exception:
                    logger.error(f"bot在群{event.get_group_id()}权限不足，禁言失败")
            else:
                logger.info(f"[扫雷] 用户 {event.get_sender_id()} 游戏失败")

        return changed, game, msgs

    async def open_positions(
        self,
        event: AstrMessageEvent,
        text: str,
        *,
        defer_output: bool = False,
    ) -> tuple[bool, MineSweeper | None, list[str]]:
        uid = event.get_sender_id()
        logger.debug(f"[扫雷] 用户 {uid} 挖开位置：{text}")

        changed, game, msgs = await self._handle_positions(
            event,
            text,
            "open",
            defer_output=defer_output,
        )

        return changed, game, msgs

    async def mark_positions(
        self,
        event: AstrMessageEvent,
        text: str,
        *,
        defer_output: bool = False,
    ) -> tuple[bool, MineSweeper | None, list[str]]:
        uid = event.get_sender_id()
        logger.debug(f"[扫雷] 用户 {uid} 标记位置：{text}")
        changed, game, msgs = await self._handle_positions(
            event,
            text,
            "mark",
            defer_output=defer_output,
        )
        return changed, game, msgs

    async def sweep_positions(
        self,
        event: AstrMessageEvent,
        text: str,
        *,
        defer_output: bool = False,
    ) -> tuple[bool, MineSweeper | None, list[str]]:
        uid = event.get_sender_id()
        logger.debug(f"[扫雷] 用户 {uid} 清扫位置：{text}")

        changed, game, msgs = await self._handle_positions(
            event,
            text,
            "sweep",
            defer_output=defer_output,
        )
        return changed, game, msgs
