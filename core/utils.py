import os
import re
import sys

from astrbot.api import logger
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)


_SINGLE_POS_RE = re.compile(r"^([a-z])(\d+)$", re.I)
_ROW_RANGE_RE = re.compile(r"^([a-z])-([a-z])(\d+)$", re.I)
_COL_RANGE_RE = re.compile(r"^([a-z])(\d+)-(\d+)$", re.I)
_RECT_RANGE_RE = re.compile(r"^([a-z])(\d+)-([a-z])(\d+)$", re.I)
TOKEN_PATTERN = re.compile(
    r"[a-zA-Z]\d+-[a-zA-Z]\d+|[a-zA-Z](?:-[a-zA-Z])?\d+(?:-\d+)?|[a-zA-Z]-[a-zA-Z]\d+"
)


def expand_position_token(token: str) -> list[str] | None:
    token = token.strip()
    m = _SINGLE_POS_RE.match(token)
    if m:
        return [f"{m.group(1).lower()}{int(m.group(2))}"]

    m = _RECT_RANGE_RE.match(token)
    if m:
        # 矩形选区：a1-b2 → a1, a2, b1, b2
        start_row = ord(m.group(1).lower())
        start_col = int(m.group(2))
        end_row = ord(m.group(3).lower())
        end_col = int(m.group(4))

        row_step = 1 if end_row >= start_row else -1
        col_step = 1 if end_col >= start_col else -1

        result = []
        for r in range(start_row, end_row + row_step, row_step):
            for c in range(start_col, end_col + col_step, col_step):
                result.append(f"{chr(r)}{c}")
        return result

    m = _ROW_RANGE_RE.match(token)
    if m:
        start = ord(m.group(1).lower())
        end = ord(m.group(2).lower())
        col = int(m.group(3))
        step = 1 if end >= start else -1
        return [f"{chr(c)}{col}" for c in range(start, end + step, step)]

    m = _COL_RANGE_RE.match(token)
    if m:
        row = m.group(1).lower()
        start = int(m.group(2))
        end = int(m.group(3))
        step = 1 if end >= start else -1
        return [f"{row}{c}" for c in range(start, end + step, step)]

    return None


def tokenize_positions(text: str) -> list[str]:
    """
    从文本中提取位置 token
    支持：
    - 连续无空格：a1b2c3 → ["a1", "b2", "c3"]
    - 空格分隔：a1 b2 c3 → ["a1", "b2", "c3"]
    - 区间：a1-5 b1-3 → ["a1-5", "b1-3"]
    - 混合：a1b-c5d1-3 → ["a1", "b-c5", "d1-3"]
    """
    return TOKEN_PATTERN.findall(text)


def parse_position_tokens(tokens: list[str]) -> tuple[list[str], list[str]]:
    positions: list[str] = []
    invalid_tokens: list[str] = []

    for token in tokens:
        expanded = expand_position_token(token)
        if expanded is None:
            invalid_tokens.append(token)
            continue
        positions.extend(expanded)

    return positions, invalid_tokens


def detect_desktop() -> bool:
    """
    判断是否可用 GUI（tkinter）
    - Windows / macOS：直接尝试 tkinter
    - Linux：先检查 DISPLAY / WAYLAND，再尝试 tkinter
    """

    # ---------- Linux 特判 ----------
    if sys.platform.startswith("linux"):
        if not (os.getenv("DISPLAY") or os.getenv("WAYLAND_DISPLAY")):
            return False

    # ---------- 通用兜底 ----------
    try:
        import tkinter

        root = tkinter.Tk()
        root.withdraw()
        root.update()
        root.destroy()
        return True
    except Exception:
        return False


def parse_position(pos: str) -> tuple[int, int] | None:
    """
    将 A1 / b12 解析为 (x, y)
    """
    m = _SINGLE_POS_RE.match(pos)
    if not m:
        return None
    x = ord(m.group(1).lower()) - ord("a")
    y = int(m.group(2)) - 1
    return x, y


async def set_group_ban(event: AiocqhttpMessageEvent, ban_time: int):
    """检测违禁词并撤回消息"""
    try:
        await event.bot.set_group_ban(
            group_id=int(event.get_group_id()),
            user_id=int(event.get_sender_id()),
            duration=ban_time,
        )
    except Exception:
        logger.error(f"bot在群{event.get_group_id()}权限不足，禁言失败")
        pass
