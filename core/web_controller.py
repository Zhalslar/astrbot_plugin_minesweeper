import secrets

from astrbot.api.event import MessageChain
from astrbot.api.star import Context
from astrbot.api.web import error_response, json_response, request, stream_response
from astrbot.core.message.components import Image

from .config import PluginConfig
from .game_service import GameService

PLUGIN_NAME = "astrbot_plugin_minesweeper"


class WebController:
    """Expose the shared Minesweeper service to plugin Pages."""

    def __init__(
        self,
        context: Context,
        cfg: PluginConfig,
        game_service: GameService,
    ):
        self.context = context
        self.cfg = cfg
        self.game_service = game_service
        routes = [
            ("/games", self.list_games, ["GET"], "List Minesweeper games"),
            ("/game", self.get_game, ["GET"], "Get a Minesweeper game"),
            ("/games", self.start_game, ["POST"], "Start a Minesweeper game"),
            (
                "/action",
                self.action,
                ["POST"],
                "Perform a Minesweeper action",
            ),
            (
                "/stop",
                self.stop_game,
                ["POST"],
                "Stop a Minesweeper game",
            ),
            (
                "/push",
                self.push_board,
                ["POST"],
                "Push the current board to its source session",
            ),
            ("/events", self.events, ["GET"], "Subscribe to game events"),
        ]
        for route, handler, methods, description in routes:
            context.register_web_api(
                f"/{PLUGIN_NAME}{route}", handler, methods, description
            )

    async def list_games(self):
        return json_response(
            {
                "games": self.game_service.list_games(),
                "difficulties": self.cfg.level_keys,
            }
        )

    async def get_game(self):
        session_id = request.query.get("session_id", "")
        game = self.game_service.get(session_id)
        if game is None:
            return error_response("game not found", status_code=404)
        return json_response(
            {
                "session_id": session_id,
                "can_push": game.can_push,
                **game.snapshot(),
            }
        )

    async def start_game(self):
        payload = await request.json(default={})
        if not payload:
            return error_response("payload is required")
        session_id = payload.get("session_id")
        if session_id is None:
            session_id = str(secrets.randbelow(90_000_000) + 10_000_000)
            while self.game_service.is_running(session_id):
                session_id = str(secrets.randbelow(90_000_000) + 10_000_000)
        elif not isinstance(session_id, str) or not session_id.strip():
            return error_response("invalid session_id")
        elif (existing_game := self.game_service.get(session_id)) is not None:
            if not existing_game.is_over:
                return error_response("game already exists", status_code=409)
            existing_game.reset()
            return json_response(
                {
                    "session_id": session_id,
                    "can_push": existing_game.can_push,
                    **existing_game.snapshot(),
                }
            )
        difficulty = payload.get("difficulty") or self.cfg.level_keys[0]
        if not isinstance(difficulty, str) or not self.cfg.is_supported_level(
            difficulty
        ):
            return error_response("invalid difficulty")
        spec = self.cfg.get_spec(difficulty)
        display_name = payload.get("display_name") or session_id
        game = self.game_service.start(
            session_id,
            spec,
            skin_index=None,
            display_name=display_name,
            can_push=False,
        )
        return json_response(
            {"session_id": session_id, "can_push": False, **game.snapshot()},
            status_code=201,
        )

    async def action(self):
        payload = await request.json(default={})
        if not payload:
            return error_response("payload is required")
        session_id = payload.get("session_id", "")
        if not payload:
            return error_response("payload is required")
        action = payload.get("action")
        if action not in {"open", "mark", "sweep"}:
            return error_response("action must be open, mark, or sweep")
        if not isinstance(payload.get("row"), int) or not isinstance(
            payload.get("col"), int
        ):
            return error_response("row and col must be integers")
        game = self.game_service.get(session_id)
        if game is None:
            return error_response("game not found", status_code=404)
        result = self.game_service.apply(
            session_id, action, payload["row"], payload["col"]
        )
        current = self.game_service.get(session_id)
        snapshot = current.snapshot() if current else game.snapshot()
        return json_response(
            {
                "session_id": session_id,
                "result": result.name.lower() if result else None,
                "can_push": game.can_push,
                **snapshot,
            }
        )

    async def stop_game(self):
        payload = await request.json(default={})
        if not payload:
            return error_response("payload is required")
        session_id = payload.get("session_id", "")
        if not self.game_service.stop(session_id):
            return error_response("game not found", status_code=404)
        return json_response({"stopped": True, "session_id": session_id})

    async def push_board(self):
        payload = await request.json(default={})
        if not payload:
            return error_response("payload is required")
        session_id = payload.get("session_id", "")
        game = self.game_service.get(session_id)
        if game is None:
            return error_response("game not found", status_code=404)
        sent = await self.context.send_message(
            session_id, MessageChain([Image.fromBytes(game.draw())])
        )
        if not sent:
            return error_response("message platform not found", status_code=502)
        return json_response({"sent": True, "session_id": session_id})

    async def events(self):
        session_id = request.query.get("session_id", "")
        if not session_id or self.game_service.get(session_id) is None:
            return error_response("game not found", status_code=404)

        async def stream():
            async for event in self.game_service.subscribe(session_id):
                yield event

        return stream_response(stream())
