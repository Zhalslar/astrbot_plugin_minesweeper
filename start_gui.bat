@echo off
REM Windows batch script to launch the Minesweeper GUI
REM 启动扫雷游戏 GUI 的 Windows 批处理脚本

echo ============================================
echo     扫雷游戏 - Minesweeper GUI
echo ============================================
echo.

python gui_launcher.py

if errorlevel 1 (
    echo.
    echo 错误: Python 未安装或未添加到 PATH
    echo Error: Python is not installed or not in PATH
    echo.
    pause
)
