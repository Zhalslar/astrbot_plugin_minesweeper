from __future__ import annotations

import re
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any, get_type_hints

from astrbot.api import logger
from astrbot.core.config.astrbot_config import AstrBotConfig
from astrbot.core.star.context import Context
from astrbot.core.utils.astrbot_path import (
    get_astrbot_plugin_data_path,
    get_astrbot_plugin_path,
)

from .model import GameSpec


class ConfigNode:
    _SCHEMA_CACHE: dict[type, dict[str, type]] = {}

    @classmethod
    def _schema(cls) -> dict[str, type]:
        return cls._SCHEMA_CACHE.setdefault(cls, get_type_hints(cls))

    def __init__(self, data: MutableMapping[str, Any]):
        object.__setattr__(self, "_data", data)
        for key in self._schema():
            if key in data:
                continue
            if hasattr(self.__class__, key):
                continue
            logger.warning(f"[config:{self.__class__.__name__}] miss key: {key}")

    def __getattr__(self, key: str) -> Any:
        if key in self._schema():
            return self._data.get(key)
        raise AttributeError(key)

    def __setattr__(self, key: str, value: Any) -> None:
        if key in self._schema():
            self._data[key] = value
            return
        object.__setattr__(self, key, value)


class PluginConfig(ConfigNode):
    default_skin: str
    difficulty_level: list[str]
    ban_time: int
    mark_prefix: str
    sweep_prefix: str

    _plugin_name = "astrbot_plugin_minesweeper"

    def __init__(self, cfg: AstrBotConfig, context: Context):
        super().__init__(cfg)
        self.context = context
        self.astrbot_config = cfg

        self.data_dir = Path(get_astrbot_plugin_data_path()) / self._plugin_name
        self.plugin_dir = Path(get_astrbot_plugin_path()) / self._plugin_name
        self.cache_dir = self.data_dir / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.skins_dir = self.plugin_dir / "skins"
        self.font_path = self.plugin_dir / "font.ttf"

        self.level_mapping: dict[str, GameSpec] = self._parse_difficulty_level()
        self.level_keys = list(self.level_mapping.keys())
        self.default_difficulty =  self.level_keys[0]
        self.default_preset = self.level_mapping[self.default_difficulty]

        self._mark_regex = re.compile(rf"^{re.escape(self.mark_prefix)}\s*[a-zA-Z]")
        self._sweep_regex = re.compile(rf"^{re.escape(self.sweep_prefix)}\s*[a-zA-Z]")

    def _parse_difficulty_level(self) -> dict[str, GameSpec]:
        result = {}
        if not self.difficulty_level:
            self.difficulty_level.append("初级 8 8 10")
        for item in self.difficulty_level:
            name, rows, cols, nums = item.split()
            result[name] = GameSpec(int(rows), int(cols), int(nums))
        return result

    def is_supported_level(self, name: str) -> bool:
        return name in self.level_keys

    def get_spec(self, name: str) -> GameSpec:
        return self.level_mapping.get(name) or self.default_preset

    async def add_level(
        self,
        name: str,
        rows: int | str | None,
        cols: int | str | None,
        mines: int | str | None,
    ) -> str | None:
        if not name or any(char.isspace() for char in name):
            return "难度名称不能为空或包含空格"
        if self.is_supported_level(name):
            return f"难度 {name} 已存在"

        if (
            not isinstance(rows, int)
            or not isinstance(cols, int)
            or not isinstance(mines, int)
        ):
            return "行数、列数和雷数必须为整数"
        if rows <= 0 or cols <= 0:
            return "行数和列数必须大于 0"
        if mines <= 0:
            return "雷数必须大于 0"
        if mines >= rows * cols:
            return "雷数必须小于格子总数"

        spec = GameSpec(rows, cols, mines)
        self.difficulty_level.append(f"{name} {rows} {cols} {mines}")
        self.level_mapping[name] = spec
        self.level_keys.append(name)
        await self.astrbot_config.save_config_async()
        return None

    def _get_mark_prefix(self, text: str) -> str | None:
        if self.mark_prefix and text.startswith(self.mark_prefix):
            return self.mark_prefix
        return None

    def _get_sweep_prefix(self, text: str) -> str | None:
        if self.sweep_prefix and text.startswith(self.sweep_prefix):
            return self.sweep_prefix
        return None
