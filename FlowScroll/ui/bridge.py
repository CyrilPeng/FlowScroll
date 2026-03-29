from PySide6.QtCore import Signal, QObject


class LogicBridge(QObject):
    """逻辑信号桥接对象，用于在不同组件之间转发事件。"""

    show_overlay = Signal()
    hide_overlay = Signal()
    update_direction = Signal(str)
    update_size = Signal(int)
    preview_size = Signal()
    toggle_horizontal = Signal()
