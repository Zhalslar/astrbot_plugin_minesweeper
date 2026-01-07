import random
import time
from collections.abc import Iterator

from .model import GameState, MarkResult, OpenResult, Tile
from .renderer import MineSweeperRenderer


class MineSweeper:
    def __init__(
        self,
        row: int,
        column: int,
        mine_num: int,
        renderer: MineSweeperRenderer,
    ):
        self.row = row
        self.column = column
        self.mine_num = mine_num
        self.renderer = renderer

        self.start_time = time.time()
        self.state = GameState.PREPARE
        self.tiles = [[Tile() for _ in range(column)] for _ in range(row)]


    @property
    def fail(self):
        return self.state == GameState.FAIL


    # ========= 对外 =========

    def draw(self) -> bytes:
        return self.renderer.render(
            tiles=self.tiles,
            state=self.state,
            start_time=self.start_time,
        )

    # ========= 游戏逻辑 =========

    def all_tiles(self) -> Iterator[Tile]:
        for row in self.tiles:
            yield from row

    def set_mines(self):
        count = 0
        while count < self.mine_num:
            i = random.randint(0, self.row - 1)
            j = random.randint(0, self.column - 1)
            t = self.tiles[i][j]
            if t.is_mine or t.is_open:
                continue
            t.is_mine = True
            count += 1

        for i in range(self.row):
            for j in range(self.column):
                self.tiles[i][j].count = self.count_around(i, j)

        self.state = GameState.GAMING

    def open(self, x: int, y: int) -> OpenResult | None:
        if not self.is_valid(x, y):
            return OpenResult.OUT

        t = self.tiles[x][y]
        if t.is_open:
            return OpenResult.DUP

        t.is_open = True

        if self.state == GameState.PREPARE:
            self.set_mines()

        if t.is_mine:
            self.state = GameState.FAIL
            t.boom = True
            self.show_mines()
            return OpenResult.FAIL

        if t.count == 0:
            for dx, dy in self.neighbors():
                self.spread_around(x + dx, y + dy)

        opened = sum(1 for t in self.all_tiles() if t.is_open)
        if opened + self.mine_num >= self.row * self.column:
            self.state = GameState.WIN
            self.show_mines()
            return OpenResult.WIN

    def mark(self, x: int, y: int) -> MarkResult | None:
        if not self.is_valid(x, y):
            return MarkResult.OUT

        t = self.tiles[x][y]
        if t.is_open:
            return MarkResult.OPENED

        t.marked = not t.marked

        marks = [t for t in self.all_tiles() if t.marked]
        if len(marks) == self.mine_num and all(t.is_mine for t in marks):
            self.state = GameState.WIN
            self.show_mines()
            return MarkResult.WIN

    # ========= 工具 =========

    def show_mines(self):
        for t in self.all_tiles():
            if (t.is_mine and not t.marked) or (not t.is_mine and t.marked):
                t.is_open = True

    def is_valid(self, x: int, y: int) -> bool:
        return 0 <= x < self.row and 0 <= y < self.column

    @staticmethod
    def neighbors():
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

    def count_around(self, x: int, y: int) -> int:
        return sum(
            1
            for dx, dy in self.neighbors()
            if self.is_valid(x + dx, y + dy) and self.tiles[x + dx][y + dy].is_mine
        )

    def spread_around(self, x: int, y: int):
        if not self.is_valid(x, y):
            return

        t = self.tiles[x][y]
        if t.is_open or t.is_mine:
            return

        t.is_open = True
        t.marked = False

        if t.count == 0:
            for dx, dy in self.neighbors():
                self.spread_around(x + dx, y + dy)
