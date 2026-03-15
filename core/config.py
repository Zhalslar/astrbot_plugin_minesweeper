# config.py
from __future__ import annotations

import re

from collections.abc import MutableMapping
from pathlib import Path
from typing import Any, get_type_hints

from astrbot.api import logger
from astrbot.core.config.astrbot_config import AstrBotConfig
from astrbot.core.star.context import Context
from astrbot.core.star.star_tools import StarTools
from astrbot.core.utils.astrbot_path import get_astrbot_plugin_path

from .model import GameSpec


class ConfigNode:
    """配置节点：dict → 强类型属性访问（极简版）"""

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
            logger.warning(f"[config:{self.__class__.__name__}] 缺少字段: {key}")

    def __getattr__(self, key: str) -> Any:
        if key in self._schema():
            return self._data.get(key)
        raise AttributeError(key)

    def __setattr__(self, key: str, value: Any) -> None:
        if key in self._schema():
            self._data[key] = value
            return
        object.__setattr__(self, key, value)


# ============ 插件自定义配置 ==================


class PluginConfig(ConfigNode):
    default_skin: str
    difficulty_level: list[str]
    ban_time: int
    use_gui: bool
    mark_shortcuts: list[str]
    sweep_shortcuts: list[str]

    _plugin_name = "astrbot_plugin_minesweeper"

    def __init__(self, cfg: AstrBotConfig, context: Context):
        super().__init__(cfg)
        self.context = context
        self.astrbot_config = cfg

        self.data_dir = StarTools.get_data_dir(self._plugin_name)
        self.plugin_dir = Path(get_astrbot_plugin_path()) / self._plugin_name
        self.cache_dir = self.data_dir / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.skins_dir = self.plugin_dir / "skins"
        self.font_path = self.plugin_dir / "font.ttf"

        logger.debug(f"[扫雷配置] plugin_dir={self.plugin_dir}")
        logger.debug(f"[扫雷配置] skins_dir={self.skins_dir}")
        logger.debug(f"[扫雷配置] skins_dir 存在={self.skins_dir.exists()}")

        self.level_mapping: dict[str, GameSpec] = self._parse_difficulty_level()
        self.level_keys = list(self.level_mapping.keys())
        self.default_preset = self.level_mapping[self.level_keys[0]]

        self.mark_pattern = self._build_mark_pattern()
        self.sweep_pattern = self._build_sweep_pattern()

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

    @staticmethod
    def _build_pattern(shortcuts: list[str], keyword: str) -> str:
        """通用：构建操作前缀正则模式"""
        if not shortcuts:
            return keyword
        escaped = [re.escape(s) for s in shortcuts]
        return f"(?:{'|'.join(escaped)}|{re.escape(keyword)})"

    def _build_mark_pattern(self) -> str:
        return self._build_pattern(self.mark_shortcuts, "标雷")

    def _build_sweep_pattern(self) -> str:
        return self._build_pattern(self.sweep_shortcuts, "清扫")
