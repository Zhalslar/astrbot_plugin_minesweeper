import random
from dataclasses import dataclass
from pathlib import Path

from PIL import Image
from PIL.Image import Image as IMG

from .model import GameSpec


@dataclass
class Skin:
    numbers: list[IMG]
    icons: list[IMG]
    digits: list[IMG]
    faces: list[IMG]
    background: IMG


class SkinManager:
    def __init__(self, skins_dir: Path):
        self.skins_dir = skins_dir

        self._skin_names = []
        self._skin_cache: dict[tuple[str, int, int], Skin] = {}

    async def initialize(self):
        """初始化"""
        names = self._scan_skins()
        self._skin_names.extend(names)

    def _scan_skins(self) -> list[str]:
        """皮肤发现"""
        if not self.skins_dir.exists():
            return []
        return [
            f.stem
            for f in self.skins_dir.iterdir()
            if f.is_file() and f.suffix == ".bmp"
        ]

    @property
    def skin_list(self) -> list[str]:
        """皮肤列表"""
        return self._skin_names

    def get_skin_by_index(self, index: int) -> str:
        """皮肤索引 (超出范围时取第一个)"""
        if index < 0 or index >= len(self._skin_names):
            return self._skin_names[0]
        return self._skin_names[index]

    def get_random_skin(self) -> str:
        """随机皮肤"""
        return random.choice(self._skin_names)

    def load(self, skin_name: str, spec: GameSpec) -> Skin:
        """皮肤加载（带缓存）"""
        key = (skin_name, spec.rows, spec.cols)
        if key in self._skin_cache:
            return self._skin_cache[key]

        skin = self._load_skin_impl(skin_name, spec)
        self._skin_cache[key] = skin
        return skin

    def _load_skin_impl(self, skin_name: str, spec: GameSpec) -> Skin:
        image = Image.open(self.skins_dir / f"{skin_name}.bmp").convert("RGBA")

        def cut(box):
            return image.crop(box)

        numbers = [cut((i * 16, 0, i * 16 + 16, 16)) for i in range(9)]
        icons = [cut((i * 16, 16, i * 16 + 16, 32)) for i in range(8)]
        digits = [cut((i * 12, 33, i * 12 + 11, 54)) for i in range(11)]
        faces = [cut((i * 27, 55, i * 27 + 26, 81)) for i in range(5)]

        background = self._build_background(image, spec)

        return Skin(numbers, icons, digits, faces, background)

    def _build_background(self, image: Image.Image, spec: GameSpec) -> Image.Image:
        """背景拼接"""
        w, h = spec.cols, spec.rows
        background = Image.new("RGBA", (w * 16 + 24, h * 16 + 66), "silver")

        blocks = [
            ((0, 82, 12, 93), (0, 0, 12, 11)),
            ((13, 82, 14, 93), (12, 0, 12 + w * 16, 11)),
            ((15, 82, 27, 93), (12 + w * 16, 0, 24 + w * 16, 11)),
            ((0, 94, 12, 95), (0, 11, 12, 44)),
            ((15, 94, 27, 95), (12 + w * 16, 11, 24 + w * 16, 44)),
            ((0, 96, 12, 107), (0, 44, 12, 55)),
            ((13, 96, 14, 107), (12, 44, 12 + w * 16, 55)),
            ((15, 96, 27, 107), (12 + w * 16, 44, 24 + w * 16, 55)),
            ((0, 108, 12, 109), (0, 55, 12, 55 + h * 16)),
            ((15, 108, 27, 109), (12 + w * 16, 55, 24 + w * 16, 55 + h * 16)),
            ((0, 110, 12, 121), (0, 55 + h * 16, 12, 66 + h * 16)),
            ((13, 110, 14, 121), (12, 55 + h * 16, 12 + w * 16, 66 + h * 16)),
            ((15, 110, 27, 121), (12 + w * 16, 55 + h * 16, 24 + w * 16, 66 + h * 16)),
            ((28, 82, 69, 107), (16, 15, 57, 40)),
            ((28, 82, 69, 107), (w * 16 - 33, 15, 8 + w * 16, 40)),
        ]

        for src, dst in blocks:
            part = image.crop(src).resize((dst[2] - dst[0], dst[3] - dst[1]))
            background.paste(part, dst)

        return background
