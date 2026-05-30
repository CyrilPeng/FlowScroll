"""系统托盘管理器：封装托盘图标、菜单构建与预设快速切换逻辑。"""

import os

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction, QActionGroup, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QStyle, QSystemTrayIcon

from FlowScroll.core.config import get_preset_display_name
from FlowScroll.i18n import tr
from FlowScroll.ui.utils import resource_path


class TrayManager(QObject):
    """系统托盘图标与菜单逻辑封装，支持预设快速切换。

    当传入 ``controller`` (ApplicationController) 时，托盘菜单会包含
    预设子菜单，允许用户在不打开主窗口的情况下切换预设。
    """

    show_window = Signal()
    preset_selected = Signal(str)    # 内部预设名
    horizontal_toggled = Signal()    # 请求切换横向滚动

    def __init__(self, parent, icon_name: str, controller=None):
        """初始化托盘管理器，绑定窗口、控制器及预设管理接口。

        参数:
            parent: 父窗口（MainWindow）
            icon_name: 图标文件名
            controller: ApplicationController 实例（可选，用于预设子菜单）
        """
        super().__init__(parent)
        self._controller = controller
        self.tray_icon = QSystemTrayIcon(parent)
        self._init_icon(parent, icon_name)
        self._init_menu(parent)

    # ---- 图标初始化 ----

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

    # ---- 菜单初始化 ----

    def _init_menu(self, parent) -> None:
        self.tray_menu = QMenu()

        # 预设子菜单（仅当 controller 可用时创建）
        self.presets_menu = None
        self._preset_action_group = None
        if self._controller is not None:
            self.presets_menu = self.tray_menu.addMenu(tr("tray.presets"))
            self._preset_action_group = QActionGroup(parent)
            self._preset_action_group.setExclusive(True)
            self._preset_action_group.triggered.connect(
                self._on_preset_action_triggered
            )
            self._rebuild_presets_menu()
            self.tray_menu.addSeparator()

        # 横向滚动切换（可勾选）
        self.action_toggle_horizontal = QAction(parent)
        self.action_toggle_horizontal.setCheckable(True)
        self.action_toggle_horizontal.triggered.connect(
            self.horizontal_toggled.emit
        )
        self.tray_menu.addAction(self.action_toggle_horizontal)

        self.tray_menu.addSeparator()

        # 显示设置
        self.action_show = QAction(parent)
        self.action_show.triggered.connect(self.show_window.emit)
        self.tray_menu.addAction(self.action_show)

        self.tray_menu.addSeparator()

        # 退出
        self.action_quit = QAction(parent)
        self.action_quit.triggered.connect(QApplication.instance().quit)
        self.tray_menu.addAction(self.action_quit)

        self.retranslate_ui()
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self._on_activated)
        self.tray_icon.show()

    # ---- 预设子菜单 ----

    def _rebuild_presets_menu(self) -> None:
        """根据当前预设列表重建子菜单，并勾选当前生效的预设。"""
        if self.presets_menu is None or self._controller is None:
            return
        if self._preset_action_group is None:
            return

        self.presets_menu.clear()
        for action in self._preset_action_group.actions():
            self._preset_action_group.removeAction(action)

        preset_manager = self._controller.preset_manager
        all_names = preset_manager.get_all_names()
        current = preset_manager.current_preset_name

        for internal_name in all_names:
            display = get_preset_display_name(internal_name)
            action = QAction(display, self.presets_menu)
            action.setCheckable(True)
            action.setData(internal_name)
            if internal_name == current:
                action.setChecked(True)
            self._preset_action_group.addAction(action)
            self.presets_menu.addAction(action)

    def _on_preset_action_triggered(self, action) -> None:
        """预设子菜单项被触发：通过 controller 加载预设，并通知主窗口。"""
        internal_name = action.data()
        if not internal_name or self._controller is None:
            return
        self._controller.load_selected_preset(internal_name)
        self.preset_selected.emit(internal_name)

    # ---- 横向滚动状态同步 ----

    def update_horizontal_state(self, enabled: bool) -> None:
        """更新“切换横向滚动”菜单项的勾选状态。

        使用 blockSignals 避免触发 toggle 信号导致的递归回调。
        """
        if hasattr(self, "action_toggle_horizontal"):
            self.action_toggle_horizontal.blockSignals(True)
            self.action_toggle_horizontal.setChecked(enabled)
            self.action_toggle_horizontal.blockSignals(False)

    # ---- i18n ----

    def retranslate_ui(self) -> None:
        """刷新菜单项文本；切换语言后应调用。"""
        self.action_show.setText(tr("tray.show_settings"))
        self.action_quit.setText(tr("tray.quit"))
        self.action_toggle_horizontal.setText(tr("tray.toggle_horizontal"))
        if self.presets_menu is not None:
            self.presets_menu.setTitle(tr("tray.presets"))
            # 预设显示名随语言变化，需完整重建
            self._rebuild_presets_menu()

    # ---- 事件处理 ----

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
