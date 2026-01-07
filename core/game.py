# game.py

from dataclasses import dataclass

from .mine_sweeper import MineSweeper
from .model import (
    GameState,
    MarkResult,
    OpenResult,
)
from .utils import parse_position


@dataclass
class GameActionResult:
    """
    一次操作后的结果
    """

    message: str = ""
    need_render: bool = True
    game_over: bool = False


class GameSession:
    """
    单个扫雷游戏实例
    """

    def __init__(self, game: MineSweeper):
        self.game = game


    # ---------- 对外 API ----------

    def open(self, pos_str: str) -> GameActionResult:
        pos = parse_position(pos_str)
        if not pos:
            return GameActionResult(f"位置 {pos_str} 不合法")

        res = self.game.open(*pos)

        if res == OpenResult.OUT:
            return GameActionResult(f"位置 {pos_str} 超出边界")

        if res == OpenResult.DUP:
            return GameActionResult(f"位置 {pos_str} 已被挖开")

        if res in (OpenResult.WIN, OpenResult.FAIL):
            msg = (
                "恭喜你获得游戏胜利！"
                if self.game.state == GameState.WIN
                else "很遗憾，游戏失败"
            )
            return GameActionResult(msg, game_over=True)

        return GameActionResult()

    def mark(self, pos_str: str) -> GameActionResult:
        pos = parse_position(pos_str)
        if not pos:
            return GameActionResult(f"位置 {pos_str} 不合法")

        res = self.game.mark(*pos)

        if res == MarkResult.OUT:
            return GameActionResult(f"位置 {pos_str} 超出边界")

        if res == MarkResult.OPENED:
            return GameActionResult(f"位置 {pos_str} 已被挖开，不能标记")

        if res == MarkResult.WIN:
            return GameActionResult("恭喜你获得游戏胜利！", game_over=True)

        return GameActionResult()


class GameManager:
    """
    统一管理多个游戏会话
    key 一般为 user_id / session_id
    """

    def __init__(self):
        self.sessions: dict[str, GameSession] = {}


    # ---------- 生命周期 ----------

    def create(self, key: str, game: MineSweeper) -> GameSession:
        session = GameSession(game)
        self.sessions[key] = session
        return session

    def get(self, key: str) -> GameSession | None:
        return self.sessions.get(key)

    def stop(self, key: str):
        self.sessions.pop(key, None)

    # ---------- 状态 ----------

    def is_running(self, key: str) -> bool:
        return key in self.sessions
