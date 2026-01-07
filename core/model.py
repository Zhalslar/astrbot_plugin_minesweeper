
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


@dataclass
class Tile:
    is_mine: bool = False
    is_open: bool = False
    marked: bool = False
    boom: bool = False
    count: int = 0
