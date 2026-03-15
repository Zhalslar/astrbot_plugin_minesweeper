from __future__ import annotations


import asyncio

from core.command_handler import GameActionHandler
from core.game import GameManager
from core.model import SweepResult


class DummyEvent:
    def __init__(self, session_id: str = "s"):
        self.session_id = session_id
        self.sent: list[str] = []

    def plain_result(self, text: str) -> str:
        return text

    async def send(self, payload: str):
        self.sent.append(payload)


class DummyImageService:
    def __init__(self):
        self.saved = 0
        self.sent = 0

    def save_cache(self, event, img_bytes: bytes) -> str:
        self.saved += 1
        return "/tmp/x.png"

    async def send_with_replace(self, event, image_path: str):
        self.sent += 1


class DummyGame:
    is_over = False

    def draw(self) -> bytes:
        return b"img"


async def _run(handler: GameActionHandler, event: DummyEvent, tokens, action, rh, **kw):
    return await handler.handle_positions(event, tokens, action, rh, **kw)


def test_handle_positions_changed_on_open_success():
    mgr = GameManager()
    mgr.create("s", DummyGame())
    img = DummyImageService()
    h = GameActionHandler(mgr, img, ban_time=0)
    event = DummyEvent("s")

    async def run():
        changed, game, msgs = await _run(
            h,
            event,
            ["a1"],
            lambda g, x, y: None,
            lambda res, pos: None,
            send_msgs=False,
            send_board=False,
        )
        assert changed is True
        assert game is not None
        assert msgs == []
        assert img.sent == 0

    asyncio.run(run())


def test_handle_positions_changed_on_sweep_success():
    mgr = GameManager()
    mgr.create("s", DummyGame())
    img = DummyImageService()
    h = GameActionHandler(mgr, img, ban_time=0)
    event = DummyEvent("s")

    async def run():
        changed, game, msgs = await _run(
            h,
            event,
            ["a1"],
            lambda g, x, y: SweepResult.SUCCESS,
            lambda res, pos: None,
            send_msgs=False,
            send_board=False,
        )
        assert changed is True
        assert game is not None
        assert msgs == []
        assert img.sent == 0

    asyncio.run(run())


def test_handle_positions_not_changed_on_sweep_condition_not_met():
    mgr = GameManager()
    mgr.create("s", DummyGame())
    img = DummyImageService()
    h = GameActionHandler(mgr, img, ban_time=0)
    event = DummyEvent("s")

    async def run():
        changed, game, msgs = await _run(
            h,
            event,
            ["a1"],
            lambda g, x, y: SweepResult.CONDITION_NOT_MET,
            lambda res, pos: f"{pos} 不满足清扫条件",
            send_msgs=False,
            send_board=False,
        )
        assert changed is False
        assert msgs == ["a1 不满足清扫条件"]
        assert img.sent == 0

    asyncio.run(run())


def test_python_regex_matches_multiline():
    import re

    multiline_re = re.compile(r"^[\s\S]*\n[\s\S]*$")
    assert multiline_re.match("a1\nb2")
    assert multiline_re.match("'a1\n#b2")
    assert not multiline_re.match("a1 b2")
