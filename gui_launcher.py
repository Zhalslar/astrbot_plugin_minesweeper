#!/usr/bin/env python
"""
扫雷游戏 - Windows GUI 启动器
Minesweeper Game - Windows GUI Launcher

直接运行此脚本可在 Windows 屏幕上用鼠标玩扫雷游戏
Run this script to play minesweeper with mouse on Windows screen
"""

import sys
from pathlib import Path

# Add parent directory to path if running as script
if __name__ == "__main__":
    parent_dir = Path(__file__).parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))

from core.gui import start_gui


def main():
    """
    启动扫雷游戏 GUI
    Launch Minesweeper GUI
    """
    print("=" * 50)
    print("扫雷游戏 - Minesweeper")
    print("=" * 50)
    print()
    print("游戏说明 / Instructions:")
    print("  - 左键点击: 挖开格子 / Left click: Open tile")
    print("  - 右键点击: 标记地雷 / Right click: Mark mine")
    print("  - 点击笑脸: 重新开始 / Click face: Restart game")
    print()
    print("难度选择 / Difficulty:")
    print("  1. 初级 (9x9, 10雷) / Beginner")
    print("  2. 中级 (16x16, 40雷) / Intermediate")
    print("  3. 高级 (16x30, 99雷) / Expert")
    print("  4. 自定义 / Custom")
    print()

    # Get difficulty choice
    choice = input("请选择难度 (1-4) / Choose difficulty (1-4): ").strip()

    if choice == "1":
        row, col, mines = 9, 9, 10
        print("开始初级游戏... / Starting beginner game...")
    elif choice == "2":
        row, col, mines = 16, 16, 40
        print("开始中级游戏... / Starting intermediate game...")
    elif choice == "3":
        row, col, mines = 16, 30, 99
        print("开始高级游戏... / Starting expert game...")
    elif choice == "4":
        try:
            row = int(input("行数 / Rows: ").strip())
            col = int(input("列数 / Columns: ").strip())
            mines = int(input("地雷数 / Mines: ").strip())
            
            if row < 5 or col < 5:
                print("行列数最小为 5 / Minimum 5 rows/columns")
                return
            if mines >= row * col:
                print("地雷数必须小于格子总数 / Mines must be less than total tiles")
                return
            
            print(f"开始自定义游戏 ({row}x{col}, {mines}雷)...")
            print(f"Starting custom game ({row}x{col}, {mines} mines)...")
        except ValueError:
            print("输入无效 / Invalid input")
            return
    else:
        print("选择无效，使用默认初级难度 / Invalid choice, using beginner difficulty")
        row, col, mines = 9, 9, 10

    print()
    print("启动游戏窗口... / Launching game window...")
    print()

    # Start GUI
    start_gui(row=row, column=col, mine_num=mines, skin_name="default")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n游戏已退出 / Game exited")
    except Exception as e:
        print(f"\n错误 / Error: {e}")
        import traceback
        traceback.print_exc()
