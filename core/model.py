from dataclasses import dataclass
from enum import Enum


class GameState(Enum):
    PREPARE = 0
    GAMING = 1
    WIN = 2
    FAIL = 3


class OpenResult(Enum):
    OUT = 0
    DUP = 1
    WIN = 2
    FAIL = 3


class MarkResult(Enum):
    OUT = 0
    OPENED = 1
    WIN = 2


class SweepResult(Enum):
    OUT = 0
    NOT_OPENED = 1
    CONDITION_NOT_MET = 2
    SUCCESS = 3
    WIN = 4
    FAIL = 5


@dataclass
class Tile:
    is_mine: bool = False
    is_open: bool = False
    marked: bool = False
    boom: bool = False
    count: int = 0


@dataclass(frozen=True, slots=True)
class GameSpec:
    rows: int
    cols: int
    mines: int
