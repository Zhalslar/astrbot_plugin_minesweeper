import threading

from .game import MineSweeper
from .utils import detect_desktop


class GuiLauncher:
    """
    GUI 启动器
    - 判断是否满足 GUI 启动条件
    - 在独立线程中启动 GUI 窗口
    """

    def __init__(self, use_gui: bool):
        self.use_gui = use_gui

    def should_launch(self) -> bool:
        """检查是否应该启动 GUI"""
        return self.use_gui and detect_desktop()

    def launch(self, game: MineSweeper):
        """在独立线程中启动 GUI"""
        from .gui import start_gui

        threading.Thread(
            target=start_gui,
            args=(game,),
            daemon=True,
        ).start()
