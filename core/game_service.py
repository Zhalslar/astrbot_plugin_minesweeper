import asyncio
import json
from collections.abc import AsyncIterator

from .config import PluginConfig
from .game import MineSweeper
from .model import GameSpec, MarkResult, OpenResult, SweepResult
from .renderer import MineSweeperRenderer
from .skin import SkinManager


class GameService:
    """Manage shared game instances and real-time board updates."""

    def __init__(self, cfg: PluginConfig, skin_mgr: SkinManager):
        self.cfg = cfg
        self.skin_mgr = skin_mgr
        self.games: dict[str, MineSweeper] = {}
        self.loop = asyncio.get_running_loop()
        self._subscribers: dict[str, set[asyncio.Queue[str | None]]] = {}

    def start(
        self,
        session_id: str,
        spec: GameSpec,
        skin_index: int | None = None,
        display_name: str | None = None,
        can_push: bool = False,
    ) -> MineSweeper:
        display_name = display_name or session_id
        skin_name = (
            self.skin_mgr.get_skin_by_index(skin_index - 1)
            if skin_index is not None
            else self.cfg.default_skin
        )
        renderer = MineSweeperRenderer(
            spec=spec,
            skin=self.skin_mgr.load(skin_name, spec),
            font_path=str(self.cfg.font_path),
        )
        game = MineSweeper(spec, renderer, display_name, can_push)
        self.games[session_id] = game
        game.add_listener(lambda: self._publish(session_id, game))
        self._publish(session_id, game)
        return game

    def get(self, session_id: str) -> MineSweeper | None:
        return self.games.get(session_id)

    def is_running(self, session_id: str) -> bool:
        return session_id in self.games

    def list_games(self) -> list[dict]:
        return [
            {
                "session_id": session_id,
                "can_push": game.can_push,
                **game.snapshot(),
            }
            for session_id, game in self.games.items()
        ]

    def stop(self, session_id: str) -> bool:
        game = self.games.pop(session_id, None)
        if game is None:
            return False
        self._publish(session_id, game, event_type="stopped")
        for queue in self._subscribers.pop(session_id, set()):
            self.loop.call_soon_threadsafe(queue.put_nowait, None)
        return True

    def apply(
        self, session_id: str, action: str, row: int, col: int
    ) -> OpenResult | MarkResult | SweepResult | None:
        game = self.get(session_id)
        if game is None or game.is_over:
            return None
        result = getattr(game, action)(row, col)
        if game.is_over:
            self._publish(session_id, game)
        return result

    async def subscribe(self, session_id: str) -> AsyncIterator[str]:
        queue: asyncio.Queue[str | None] = asyncio.Queue()
        self._subscribers.setdefault(session_id, set()).add(queue)
        game = self.get(session_id)
        if game is not None:
            yield self._encode(session_id, game)
        try:
            while True:
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=15)
                except TimeoutError:
                    yield ": keep-alive\n\n"
                    continue
                if payload is None:
                    return
                yield payload
        finally:
            self._subscribers.get(session_id, set()).discard(queue)

    def _publish(
        self, session_id: str, game: MineSweeper, event_type: str = "snapshot"
    ) -> None:
        payload = self._encode(session_id, game, event_type)
        for queue in self._subscribers.get(session_id, set()):
            self.loop.call_soon_threadsafe(queue.put_nowait, payload)

    def _encode(
        self,
        session_id: str,
        game: MineSweeper,
        event_type: str = "snapshot",
    ) -> str:
        data = {
            "type": event_type,
            "session_id": session_id,
            "can_push": game.can_push,
            **game.snapshot(),
        }
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
