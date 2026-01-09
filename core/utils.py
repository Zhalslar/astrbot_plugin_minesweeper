


import os
import re
import sys

from astrbot.api import logger
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)


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
    m = re.match(r"^([a-z])(\d+)$", pos, re.I)
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
