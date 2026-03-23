import os
import sys
from PySide6.QtCore import QObject, Signal

def resource_path(relative_path):
    """
    资源定位：处理打包后的路径与开发环境的路径差异
    """
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        # 指向项目根目录，以便于找到 logo 文件
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    return os.path.join(base_path, relative_path)

class LogicBridge(QObject):
    """
    逻辑信号桥接：跨线程、跨组件的事件总线
    """
    show_overlay = Signal()
    hide_overlay = Signal()
    update_direction = Signal(str)
    update_size = Signal(int)
    preview_size = Signal()
    toggle_horizontal = Signal()
