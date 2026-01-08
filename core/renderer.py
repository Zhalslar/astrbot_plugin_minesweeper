# renderer.py
import time
from collections.abc import Iterator
from io import BytesIO

from PIL import ImageDraw, ImageFont
from PIL.Image import Image as IMG
from PIL.Image import Resampling

from .model import GameSpec, GameState, Tile
from .skin import Skin


class MineSweeperRenderer:
    def __init__(
        self,
        spec: GameSpec,
        skin: Skin,
        font_path: str,
        scale: int = 4,
    ):
        self.spec = spec
        self.scale = scale
        self.skin = skin
        self.font = ImageFont.truetype(
            font=font_path,
            size=7 * self.scale,
            encoding="utf-8",
        )
        # GUI
        self.tile_size = skin.numbers[0].width * 4  # scale = 4
        self.board_offset_x = int(12 * 4)  # 12 pixels offset * scale
        self.board_offset_y = int(55 * 4)  # 55 pixels offset * scale

    # ========= 对外唯一入口 =========
    def render(
        self,
        *,
        tiles: list[list[Tile]],
        state: GameState,
        start_time: float,
    ) -> bytes:

        bg = self.skin.background.copy()

        self._draw_face(bg, state)
        self._draw_counts(bg, tiles)
        self._draw_time(bg, start_time)
        self._draw_tiles(bg, tiles)

        bg = bg.resize(
            (bg.width * self.scale, bg.height * self.scale),
            Resampling.NEAREST,
        )

        self._draw_label(bg, tiles)

        output = BytesIO()
        bg.save(output, format="PNG")
        output.seek(0)
        return output.getvalue()

    # ========= 基础工具 =========

    @staticmethod
    def _all_tiles(tiles: list[list[Tile]]) -> Iterator[Tile]:
        for row in tiles:
            yield from row



    # ========= 具体绘制 =========

    def _draw_face(self, bg: IMG, state: GameState):
        if state == GameState.WIN:
            num = 3
        elif state == GameState.FAIL:
            num = 2
        else:
            num = 0

        face = self.skin.faces[num]
        x = (bg.width - face.width) // 2
        y = 15
        bg.paste(face, (x, y))

    def _draw_counts(self, bg: IMG, tiles: list[list[Tile]]):
        marked = sum(1 for t in self._all_tiles(tiles) if t.marked)
        mine_left = self.spec.mines - marked
        nums = f"{mine_left:03d}"[:3]

        def digit_img(ch: str):
            return self.skin.digits[10 if ch == "-" else int(ch)]

        for i, ch in enumerate(nums):
            img = digit_img(ch)
            x = 18 + i * (img.width + 2)
            y = 17
            bg.paste(img, (x, y))

    def _draw_time(self, bg: IMG, start_time: float):
        passed = int(time.time() - start_time)
        nums = f"{passed:03d}"[-3:]

        for i, ch in enumerate(reversed(nums)):
            img = self.skin.digits[int(ch)]
            x = bg.width - 16 - (i + 1) * (img.width + 2)
            y = 17
            bg.paste(img, (x, y))

    def _draw_tiles(self, bg: IMG, tiles: list[list[Tile]]):
        for i in range(self.spec.rows):
            for j in range(self.spec.cols):
                t = tiles[i][j]

                if t.is_open:
                    if t.is_mine:
                        img = self.skin.icons[5 if t.boom else 2]
                    else:
                        if t.marked:
                            img = self.skin.icons[4]
                        else:
                            img = self.skin.numbers[t.count]
                else:
                    img = self.skin.icons[3 if t.marked else 0]

                x = 12 + img.width * j
                y = 55 + img.height * i
                bg.paste(img, (x, y))

    def _draw_label(self, bg: IMG, tiles: list[list[Tile]]):


        tile_w = self.skin.numbers[0].width * self.scale
        tile_h = self.skin.numbers[0].height * self.scale

        dx = 12.5 * self.scale
        dy = 54.5 * self.scale

        draw = ImageDraw.Draw(bg)

        for i in range(self.spec.rows):
            for j in range(self.spec.cols):
                t = tiles[i][j]
                if t.is_open or t.marked:
                    continue

                text = chr(i + 65) + str(j + 1)
                _, _, w, h = self.font.getbbox(text)

                x = dx + tile_w * j + (tile_w - w) / 2
                y = dy + tile_h * i + (tile_h - h) / 2

                draw.text((x, y), text, font=self.font, fill="black")
