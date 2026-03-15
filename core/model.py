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
    """清扫操作结果"""

    OUT = 0  # 超出边界
    NOT_OPENED = 1  # 格子未挖开
    CONDITION_NOT_MET = 2  # 不满足清扫条件
    SUCCESS = 3  # 成功清扫
    WIN = 4  # 清扫后胜利
    FAIL = 5  # 清扫后踩雷


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
