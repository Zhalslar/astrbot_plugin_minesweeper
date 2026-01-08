"""
Windows GUI for Minesweeper (View + Controller only)
窗口缩放时棋盘等比缩放（修复首帧灰屏）
"""

import tkinter as tk
from io import BytesIO
from tkinter import messagebox

from PIL import Image, ImageTk
from PIL.Image import Resampling

from .game import MineSweeper
from .model import GameState


class MineSweeperGUI:
    def __init__(self, game: MineSweeper):
        self.game = game
        self.spec = game.spec

        # ========= Window =========
        self.root = tk.Tk()
        self.root.title("扫雷游戏 - Minesweeper")
        self.root.resizable(True, True)

        # ========= Top Bar =========
        top = tk.Frame(self.root)
        top.pack(side=tk.TOP, fill=tk.X)

        tk.Button(
            top,
            text="发送界面",
            command=self._on_send_board_clicked,
        ).pack(padx=6, pady=4)

        # ========= Canvas =========
        self.canvas = tk.Canvas(self.root, bg="gray")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<Button-1>", self._on_left_click)
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        # ========= Render Cache =========
        self.original_img: Image.Image | None = None
        self.current_photo: ImageTk.PhotoImage | None = None

        # ========= Scale Info =========
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0

        # ========= Click Mapping =========
        self.tile_size = game.renderer.tile_size
        self.board_offset_x = game.renderer.board_offset_x
        self.board_offset_y = game.renderer.board_offset_y

        # ========= Listener =========
        self.game.add_listener(self._on_game_changed)

        # ⚠️ 关键修复：等窗口布局完成再渲染
        self.root.after_idle(self._update_display)

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ================= Events =================

    def _on_game_changed(self):
        self.root.after(0, self._update_display)

    def _on_send_board_clicked(self):
        self.game.request_send_board()

    def _on_canvas_resize(self, event):
        if self.original_img is not None:
            self._render_scaled()

    # ================= Rendering =================

    def _update_display(self):
        img_bytes = self.game.draw()
        self.original_img = Image.open(BytesIO(img_bytes))
        self._render_scaled()

    def _render_scaled(self):
        if self.original_img is None:
            return

        canvas_w = max(self.canvas.winfo_width(), 1)
        canvas_h = max(self.canvas.winfo_height(), 1)

        img_w, img_h = self.original_img.size
        self.scale = min(canvas_w / img_w, canvas_h / img_h)

        new_w = max(1, int(img_w * self.scale))
        new_h = max(1, int(img_h * self.scale))

        resized = self.original_img.resize(
            (new_w, new_h),
            Resampling.NEAREST,
        )
        self.current_photo = ImageTk.PhotoImage(resized)

        self.offset_x = (canvas_w - new_w) // 2
        self.offset_y = (canvas_h - new_h) // 2

        self.canvas.delete("all")
        self.canvas.create_image(
            self.offset_x,
            self.offset_y,
            anchor=tk.NW,
            image=self.current_photo,
        )

    # ================= Input =================

    def _get_tile_position(self, x: int, y: int):
        ox = x - self.offset_x
        oy = y - self.offset_y

        if ox < 0 or oy < 0:
            return None

        rx = int(ox / self.scale)
        ry = int(oy / self.scale)

        tx = rx - self.board_offset_x
        ty = ry - self.board_offset_y
        if tx < 0 or ty < 0:
            return None

        col = tx // self.tile_size
        row = ty // self.tile_size

        if 0 <= row < self.spec.rows and 0 <= col < self.spec.cols:
            return row, col
        return None

    def _on_left_click(self, event):
        if self.game.is_over:
            return
        pos = self._get_tile_position(event.x, event.y)
        if not pos:
            return
        row, col = pos
        res = self.game.open(row, col)
        self._update_display()

        if res and self.game.is_over:
            messagebox.showinfo(
                "游戏结束",
                "恭喜你获得游戏胜利！"
                if self.game.state == GameState.WIN
                else "很遗憾，游戏失败",
            )

    def _on_right_click(self, event):
        if self.game.is_over:
            return
        pos = self._get_tile_position(event.x, event.y)
        if not pos:
            return
        row, col = pos
        self.game.mark(row, col)
        self._update_display()

        if self.game.state == GameState.WIN:
            messagebox.showinfo("游戏结束", "恭喜你获得游戏胜利！")

    # ================= Run =================

    def run(self):
        try:
            self.root.mainloop()
        finally:
            self.game.remove_listener(self._on_game_changed)

    def _on_close(self):
        self.game.remove_listener(self._on_game_changed)
        self.root.destroy()


def start_gui(game: MineSweeper):
    gui = MineSweeperGUI(game)
    gui.run()
