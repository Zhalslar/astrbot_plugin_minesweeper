"""
Windows GUI for Minesweeper using tkinter
Allows playing the game with mouse clicks directly on screen
"""

import tkinter as tk
from io import BytesIO
from pathlib import Path
from tkinter import messagebox

from PIL import Image, ImageTk

from .game import GameSession
from .mine_sweeper import MineSweeper
from .model import GameState
from .renderer import MineSweeperRenderer
from .skin import SkinManager


class MineSweeperGUI:
    """
    Windows GUI for Minesweeper game with mouse support
    """

    def __init__(
        self,
        row: int = 9,
        column: int = 9,
        mine_num: int = 10,
        skin_name: str = "default",
    ):
        self.row = row
        self.column = column
        self.mine_num = mine_num

        # Initialize window
        self.root = tk.Tk()
        self.root.title("扫雷游戏 - Minesweeper")
        self.root.resizable(False, False)

        # Load skin and font
        skins_dir = Path(__file__).parent.parent / "skins"
        self.skin_mgr = SkinManager(skins_dir)
        # Initialize skin manager synchronously for GUI
        # The async initialize() just calls _scan_skins() internally,
        # so we replicate that behavior synchronously here for tkinter
        if not self.skin_mgr.skin_list:
            # Scan for available skins if not already loaded
            skin_names = self.skin_mgr._scan_skins()
            self.skin_mgr._skin_names.extend(skin_names)
        self.font_path = Path(__file__).parent.parent / "font.ttf"

        # Create canvas for displaying the game
        self.canvas = tk.Canvas(self.root, bg="gray")
        self.canvas.pack()

        # Bind mouse events
        self.canvas.bind("<Button-1>", self._on_left_click)  # Left click
        self.canvas.bind("<Button-3>", self._on_right_click)  # Right click

        # Game state
        self.session: GameSession | None = None
        self.current_photo: ImageTk.PhotoImage | None = None
        self.current_skin_name: str = skin_name
        
        # Cache for click detection
        self.tile_size: int = 0
        self.board_offset_x: int = 0
        self.board_offset_y: int = 0

        # Start new game
        self._new_game(skin_name)

    def _new_game(self, skin_name: str):
        """Start a new game"""
        # Update current skin name
        self.current_skin_name = skin_name
        
        # Load skin
        skin = self.skin_mgr.load(skin_name, self.row, self.column)

        # Create renderer and game
        renderer = MineSweeperRenderer(
            row=self.row,
            column=self.column,
            mine_num=self.mine_num,
            skin=skin,
            font_path=str(self.font_path),
        )
        mine_sweeper = MineSweeper(self.row, self.column, self.mine_num, renderer)

        # Create game session
        self.session = GameSession(mine_sweeper)

        # Calculate tile size and offsets for click detection
        # Based on renderer.py logic
        self.tile_size = skin.numbers[0].width * 4  # scale = 4
        self.board_offset_x = int(12 * 4)  # 12 pixels offset * scale
        self.board_offset_y = int(55 * 4)  # 55 pixels offset * scale

        # Render and display
        self._update_display()

    def _update_display(self):
        """Update the canvas with current game state"""
        if not self.session:
            return

        # Get rendered image bytes
        img_bytes = self.session.game.draw()

        # Convert to PIL Image
        pil_img = Image.open(BytesIO(img_bytes))

        # Convert to PhotoImage for tkinter
        self.current_photo = ImageTk.PhotoImage(pil_img)

        # Update canvas size if needed
        self.canvas.config(width=pil_img.width, height=pil_img.height)

        # Display image
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.current_photo)

    def _get_tile_position(self, x: int, y: int) -> tuple[int, int] | None:
        """Convert canvas coordinates to tile position (row, col)"""
        # Check if click is within the board area
        tile_x = x - self.board_offset_x
        tile_y = y - self.board_offset_y

        if tile_x < 0 or tile_y < 0:
            return None

        col = tile_x // self.tile_size
        row = tile_y // self.tile_size

        if 0 <= row < self.row and 0 <= col < self.column:
            return (row, col)

        return None

    def _position_to_coordinate(self, row: int, col: int) -> str:
        """Convert tile position (row, col) to coordinate string like 'a1'"""
        return f"{chr(row + ord('a'))}{col + 1}"

    def _check_face_button_click(self, x: int, y: int) -> bool:
        """Check if the face button was clicked"""
        # Face button is centered horizontally at y=15*4 (after scaling)
        # Face size is approximately 26x26 pixels (before scaling)
        face_y = 15 * 4
        face_size = 26 * 4
        
        # Get canvas width from current photo
        if not self.current_photo:
            return False
        
        canvas_width = self.current_photo.width()
        face_x = (canvas_width - face_size) // 2

        # Check if click is within face button bounds
        if (face_x <= x <= face_x + face_size and 
            face_y <= y <= face_y + face_size):
            return True
        
        return False

    def _on_left_click(self, event):
        """Handle left mouse click"""
        if not self.session:
            return

        # Check if face button was clicked (restart game)
        if self._check_face_button_click(event.x, event.y):
            self._restart_game()
            return

        # Get tile position
        pos = self._get_tile_position(event.x, event.y)
        if pos is None:
            return

        row, col = pos

        # Open the tile
        result = self.session.open(self._position_to_coordinate(row, col))

        # Update display
        self._update_display()

        # Check if game over
        if result.game_over:
            if self.session.game.state == GameState.WIN:
                messagebox.showinfo("游戏结束", "恭喜你获得游戏胜利！")
            else:
                messagebox.showinfo("游戏结束", "很遗憾，游戏失败")

    def _on_right_click(self, event):
        """Handle right mouse click (mark/unmark mine)"""
        if not self.session:
            return

        # Get tile position
        pos = self._get_tile_position(event.x, event.y)
        if pos is None:
            return

        row, col = pos

        # Mark/unmark the tile
        self.session.mark(self._position_to_coordinate(row, col))

        # Update display
        self._update_display()

        # Check if won by marking all mines
        if self.session.game.state == GameState.WIN:
            messagebox.showinfo("游戏结束", "恭喜你获得游戏胜利！")

    def _restart_game(self):
        """Restart the game with same settings"""
        self._new_game(self.current_skin_name)

    def run(self):
        """Start the GUI main loop"""
        self.root.mainloop()


def start_gui(
    row: int = 9,
    column: int = 9,
    mine_num: int = 10,
    skin_name: str = "default",
):
    """
    Start the Windows GUI for minesweeper
    
    Args:
        row: Number of rows
        column: Number of columns
        mine_num: Number of mines
        skin_name: Name of the skin to use
    """
    gui = MineSweeperGUI(row, column, mine_num, skin_name)
    gui.run()
