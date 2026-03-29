import os

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QStyle, QSystemTrayIcon

from FlowScroll.i18n import tr
from FlowScroll.ui.utils import resource_path


class TrayManager(QObject):
    """系统托盘图标与菜单逻辑封装。"""

    show_window = Signal()

    def __init__(self, parent, icon_name: str):
        super().__init__(parent)
        self.tray_icon = QSystemTrayIcon(parent)
        self._init_icon(parent, icon_name)
        self._init_menu(parent)

    def _init_icon(self, parent, icon_name: str) -> None:
        if not parent.windowIcon().isNull():
            self.tray_icon.setIcon(parent.windowIcon())
            return

        icon_path = resource_path(icon_name)
        if os.path.exists(icon_path):
            tray_icon = QIcon(icon_path)
            if not tray_icon.isNull():
                self.tray_icon.setIcon(tray_icon)
                return

        self.tray_icon.setIcon(
            parent.style().standardIcon(QStyle.SP_MessageBoxInformation)
        )

    def _init_menu(self, parent) -> None:
        self.tray_menu = QMenu()

        self.action_show = QAction(parent)
        self.action_show.triggered.connect(self.show_window.emit)

        self.action_quit = QAction(parent)
        self.action_quit.triggered.connect(QApplication.instance().quit)

        self.tray_menu.addAction(self.action_show)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.action_quit)

        self.retranslate_ui()
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self._on_activated)
        self.tray_icon.show()

    def retranslate_ui(self) -> None:
        self.action_show.setText(tr("tray.show_settings"))
        self.action_quit.setText(tr("tray.quit"))

    def _on_activated(self, reason) -> None:
        if reason in (QSystemTrayIcon.DoubleClick, QSystemTrayIcon.Trigger):
            self.show_window.emit()

    def show_message(self, title: str, message: str, duration: int = 1500) -> None:
        if self.tray_icon.isVisible():
            self.tray_icon.showMessage(
                title,
                message,
                QSystemTrayIcon.Information,
                duration,
            )

    def is_visible(self) -> bool:
        return self.tray_icon.isVisible()
