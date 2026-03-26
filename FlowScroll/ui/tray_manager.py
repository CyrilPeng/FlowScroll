import os

from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QStyle
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QObject, Signal

from FlowScroll.ui.utils import resource_path


class TrayManager(QObject):
    """系统托盘管理器"""

    show_window = Signal()

    def __init__(self, parent, icon_name: str):
        super().__init__(parent)
        self.tray_icon = QSystemTrayIcon(parent)
        self._init_icon(parent, icon_name)
        self._init_menu(parent)

    def _init_icon(self, parent, icon_name: str) -> None:
        """初始化托盘图标"""
        # 先尝试使用父窗口图标
        if not parent.windowIcon().isNull():
            self.tray_icon.setIcon(parent.windowIcon())
            return

        # 尝试加载 ICO 文件
        icon_path = resource_path(icon_name)
        if os.path.exists(icon_path):
            tray_icon = QIcon(icon_path)
            if not tray_icon.isNull():
                self.tray_icon.setIcon(tray_icon)
                return

        # 使用默认图标
        self.tray_icon.setIcon(
            parent.style().standardIcon(QStyle.SP_MessageBoxInformation)
        )

    def _init_menu(self, parent) -> None:
        """初始化托盘菜单"""
        tray_menu = QMenu()

        action_show = QAction("显示设置", parent)
        action_show.triggered.connect(self.show_window.emit)

        action_quit = QAction("退出程序", parent)
        action_quit.triggered.connect(QApplication.instance().quit)

        tray_menu.addAction(action_show)
        tray_menu.addSeparator()
        tray_menu.addAction(action_quit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_activated)
        self.tray_icon.show()

    def _on_activated(self, reason) -> None:
        """处理托盘图标激活事件"""
        if reason in (QSystemTrayIcon.DoubleClick, QSystemTrayIcon.Trigger):
            self.show_window.emit()

    def show_message(self, title: str, message: str, duration: int = 1500) -> None:
        """显示托盘消息"""
        if self.tray_icon.isVisible():
            self.tray_icon.showMessage(
                title,
                message,
                QSystemTrayIcon.Information,
                duration,
            )

    def is_visible(self) -> bool:
        """检查托盘图标是否可见"""
        return self.tray_icon.isVisible()
