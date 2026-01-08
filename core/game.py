# game.py
import random
import threading
import time
from collections.abc import Callable, Iterator

from .model import (
    GameSpec,
    GameState,
    MarkResult,
    OpenResult,
    Tile,
)
from .renderer import MineSweeperRenderer


class MineSweeper:
    """
    扫雷核心逻辑（纯规则 / 纯状态）
    """

    def __init__(
        self,
        spec: GameSpec,
        renderer: MineSweeperRenderer,
    ):
        self.spec = spec
        self.renderer = renderer

        self.start_time = time.time()
        self.state = GameState.PREPARE
        self.tiles = [[Tile() for _ in range(spec.cols)] for _ in range(spec.rows)]

        self._listeners: list[Callable[[], None]] = []
        self._send_board_listeners: list[Callable[[], None]] = []

        self._lock = threading.Lock()

    # ========= 状态 =========

    @property
    def is_win(self) -> bool:
        return self.state == GameState.WIN

    @property
    def is_fail(self) -> bool:
        return self.state == GameState.FAIL

    @property
    def is_over(self) -> bool:
        return self.is_win or self.is_fail

    @property
    def is_gaming(self) -> bool:
        return self.state == GameState.GAMING

    # ========= 监听 =========

    def add_listener(self, cb: Callable[[], None]):
        self._listeners.append(cb)

    def remove_listener(self, cb: Callable[[], None]):
        if cb in self._listeners:
            self._listeners.remove(cb)

    def _notify(self):
        for cb in list(self._listeners):
            cb()

    def on_send_board(self, cb: Callable[[], None]):
        self._send_board_listeners.append(cb)


    def request_send_board(self):
        for cb in list(self._send_board_listeners):
            cb()

    # ========= 对外 =========

    def draw(self) -> bytes:
        """
        渲染当前棋盘
        """
        return self.renderer.render(
            tiles=self.tiles,
            state=self.state,
            start_time=self.start_time,
        )

    # ========= 游戏逻辑 =========

    def open(self, x: int, y: int) -> OpenResult | None:
        with self._lock:
            if not self._is_valid(x, y):
                return OpenResult.OUT

            tile = self.tiles[x][y]

            if tile.is_open:
                return OpenResult.DUP

            tile.is_open = True

            # 首次点击才布雷
            if self.state == GameState.PREPARE:
                self._set_mines(exclude=(x, y))

            if tile.is_mine:
                tile.boom = True
                self.state = GameState.FAIL
                self._reveal_mines()
                return OpenResult.FAIL

            if tile.count == 0:
                self._spread(x, y)

            if self._check_win():
                self.state = GameState.WIN
                self._reveal_mines()
                return OpenResult.WIN
        self._notify()
        return None

    def mark(self, x: int, y: int) -> MarkResult | None:
        with self._lock:
            if not self._is_valid(x, y):
                return MarkResult.OUT

            tile = self.tiles[x][y]

            if tile.is_open:
                return MarkResult.OPENED

            tile.marked = not tile.marked

            if self._check_mark_win():
                self.state = GameState.WIN
                self._reveal_mines()
                return MarkResult.WIN
        self._notify()
        return None

    # ========= 内部实现 =========

    def _all_tiles(self) -> Iterator[Tile]:
        for row in self.tiles:
            yield from row

    def _set_mines(self, exclude: tuple[int, int]):
        """
        布雷，保证首次点击不会踩雷
        """
        ex, ey = exclude
        count = 0

        while count < self.spec.mines:
            x = random.randrange(self.spec.rows)
            y = random.randrange(self.spec.cols)

            if (x, y) == (ex, ey):
                continue

            tile = self.tiles[x][y]
            if tile.is_mine:
                continue

            tile.is_mine = True
            count += 1

        for x in range(self.spec.rows):
            for y in range(self.spec.cols):
                self.tiles[x][y].count = self._count_around(x, y)

        self.state = GameState.GAMING

    def _neighbors(self):
        return (
            (-1, -1),
            (0, -1),
            (1, -1),
            (-1, 0),
            (1, 0),
            (-1, 1),
            (0, 1),
            (1, 1),
        )

    def _count_around(self, x: int, y: int) -> int:
        return sum(
            1
            for dx, dy in self._neighbors()
            if self._is_valid(x + dx, y + dy) and self.tiles[x + dx][y + dy].is_mine
        )

    def _spread(self, x: int, y: int):
        for dx, dy in self._neighbors():
            nx, ny = x + dx, y + dy
            if not self._is_valid(nx, ny):
                continue

            tile = self.tiles[nx][ny]
            if tile.is_open or tile.is_mine:
                continue

            tile.is_open = True
            tile.marked = False

            if tile.count == 0:
                self._spread(nx, ny)

    def _reveal_mines(self):
        for tile in self._all_tiles():
            if tile.is_mine or tile.marked:
                tile.is_open = True

    def _check_win(self) -> bool:
        opened = sum(1 for t in self._all_tiles() if t.is_open)
        return opened + self.spec.mines >= self.spec.rows * self.spec.cols

    def _check_mark_win(self) -> bool:
        marked = [t for t in self._all_tiles() if t.marked]
        return len(marked) == self.spec.mines and all(t.is_mine for t in marked)

    def _is_valid(self, x: int, y: int) -> bool:
        return 0 <= x < self.spec.rows and 0 <= y < self.spec.cols


class GameManager:
    """
    多扫雷实例管理
    """

    def __init__(self):
        self.games: dict[str, MineSweeper] = {}

    def create(self, key: str, game: MineSweeper) -> MineSweeper:
        self.games[key] = game
        return game

    def get(self, key: str) -> MineSweeper | None:
        return self.games.get(key)

    def stop(self, key: str):
        self.games.pop(key, None)

    def is_running(self, key: str) -> bool:
        return key in self.games
