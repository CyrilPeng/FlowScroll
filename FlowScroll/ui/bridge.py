from PySide6.QtCore import Signal, QObject


class LogicBridge(QObject):
    """逻辑信号桥接，用于跨组件通信"""

    show_overlay = Signal()
    hide_overlay = Signal()
    update_direction = Signal(str)
    update_size = Signal(int)
    preview_size = Signal()
    toggle_horizontal = Signal()
