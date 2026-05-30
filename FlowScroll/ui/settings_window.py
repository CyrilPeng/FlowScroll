import os

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox,
    QDialog,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import (
    QIcon,
    QCursor,
)

from FlowScroll.platform import system_platform
from FlowScroll.core.config import (
    STATE_LOCK,
    cfg,
    runtime,
    set_config_attr,
)
from FlowScroll.i18n import tr

from FlowScroll.ui.app_controller import ApplicationController
from FlowScroll.ui.overlay import ResizableOverlay
from FlowScroll.ui.webdav_dialog import WebDAVSyncDialog
from FlowScroll.core.hotkeys import hotkey_to_display
from FlowScroll.ui.helpers import _flush_all_debounced
from FlowScroll.ui.utils import resource_path
from FlowScroll.ui.styles import (
    get_main_stylesheet,
    get_help_button_style,
)
from FlowScroll.ui.tray_manager import TrayManager

# Mixin 类
from FlowScroll.ui.dialog_manager import DialogMixin
from FlowScroll.ui.preset_mixin import PresetMixin
from FlowScroll.ui.language_mixin import LanguageMixin


class MainWindow(DialogMixin, PresetMixin, LanguageMixin, QMainWindow):
    """主设置窗口：负责 UI 展示、用户交互，业务逻辑委托给 ApplicationController。"""

    def __init__(self):
        """初始化主窗口：创建控制器、overlay、托盘、UI 和后台线程。"""
        super().__init__()

        # 业务逻辑委托给 ApplicationController。
        self.ctrl = ApplicationController()

        icon_name = system_platform.get_icon_name()
        if os.path.exists(resource_path(icon_name)):
            self.setWindowIcon(QIcon(resource_path(icon_name)))

        self.setWindowTitle(f"FlowScroll v{self.ctrl.version_label}")
        self.setMinimumSize(420, 680)
        self.resize(650, 720)

        self.overlay = ResizableOverlay()

        self.ui_widgets = {}
        self.ui_text_widgets = {}

        # 确保窗口图标已经设置好，再初始化系统托盘。
        if self.windowIcon().isNull() and os.path.exists(resource_path(icon_name)):
            self.setWindowIcon(QIcon(resource_path(icon_name)))

        self.tray_manager = TrayManager(self, icon_name, controller=self.ctrl)
        self.tray_manager.show_window.connect(self.show_normal_window)
        self.tray_manager.preset_selected.connect(self._on_tray_preset_selected)
        self.tray_manager.horizontal_toggled.connect(self.on_toggle_horizontal_hotkey)
        # 同步初始横向状态到托盘菜单
        self.tray_manager.update_horizontal_state(cfg.enable_horizontal)
        # 通过 config_bus 订阅 enable_horizontal 变更，确保所有写入路径
        # （UI 复选框、快捷键、托盘菜单、WebDAV 同步等）都能同步托盘状态
        from FlowScroll.core.config import config_bus

        config_bus.subscribe(
            "enable_horizontal",
            lambda v: self.tray_manager.update_horizontal_state(v),
        )

        self.ctrl.bridge.show_overlay.connect(self.on_show_overlay)
        self.ctrl.bridge.hide_overlay.connect(self.on_hide_overlay)
        self.ctrl.bridge.update_direction.connect(self.overlay.set_direction)
        self.ctrl.bridge.update_size.connect(self.overlay.update_geometry)
        self.ctrl.bridge.preview_size.connect(self.overlay.show_preview)
        self.ctrl.bridge.toggle_horizontal.connect(self.on_toggle_horizontal_hotkey)

        self.init_ui()
        self._start_threads()
        self.ctrl.check_for_updates(self._refresh_update_indicator)

    def save_presets_to_file(self) -> None:
        """将当前预设和配置持久化到磁盘。"""
        self.ctrl.save_presets_to_file()

    # ---- 线程启动 ----

    def _start_threads(self) -> None:
        """通过 ApplicationController 启动后台线程，处理 UI 侧的错误提示。"""
        messages = self.ctrl.start_threads(self.overlay)
        if messages:
            for level, title, body in messages:
                if level == "critical":
                    QMessageBox.critical(self, title, body)
                else:
                    QMessageBox.warning(self, title, body)

        # 输入监听完全失败时，禁用相关控件。
        if not self.ctrl.keyboard_hook_available and not self.ctrl.mouse_hook_available:
            if "enable_horizontal" in self.ui_widgets:
                self.ui_widgets["enable_horizontal"].setChecked(False)

        self.refresh_input_hook_status_ui()

    # ---- UI 状态刷新 ----

    def refresh_input_hook_status_ui(self) -> None:
        """根据键盘/鼠标钩子可用状态刷新 UI 提示和控件启用状态。"""
        keyboard_ok = self.ctrl.keyboard_hook_available
        mouse_ok = self.ctrl.mouse_hook_available

        if hasattr(self, "input_hook_status_label"):
            if keyboard_ok and mouse_ok:
                self.input_hook_status_label.setVisible(False)
                self.input_hook_status_label.setText("")
            else:
                if keyboard_ok and not mouse_ok:
                    text = tr("main.input_status.mouse_only_degraded")
                elif mouse_ok and not keyboard_ok:
                    text = tr("main.input_status.keyboard_only_degraded")
                else:
                    text = tr("main.input_status.all_unavailable")
                self.input_hook_status_label.setText(f"{text}\n\n{self.ctrl._get_input_hook_failure_detail()}")
                self.input_hook_status_label.setVisible(True)

        disable_input_controls = not keyboard_ok and not mouse_ok
        for key in (
            "enable_horizontal",
            "horizontal_hotkey_button",
            "work_mode_button",
        ):
            widget = self.ui_widgets.get(key)
            if widget is not None:
                widget.setEnabled(not disable_input_controls)

    def _refresh_update_indicator(self):
        """更新版本徽章和 GitHub 按钮的显示状态。"""
        if not hasattr(self, "btn_new_badge") or not hasattr(self, "btn_github"):
            return

        badge_mode = self.ctrl.update_badge_mode
        latest = self.ctrl.latest_release_version or tr("main.update.unknown")

        if badge_mode == "dev":
            self.btn_new_badge.setText(tr("main.update.dev_badge"))
            self.btn_new_badge.setToolTip(tr("main.update.dev_tooltip", version=latest))
            self.btn_new_badge.setVisible(True)
            self.btn_github.setText(f" {tr('tab.author_dev', version=latest)}")
            return

        if badge_mode == "update":
            self.btn_new_badge.setText(tr("main.update.release_badge"))
            self.btn_new_badge.setToolTip(tr("main.update.release_tooltip", version=latest))
            self.btn_new_badge.setVisible(True)
            self.btn_github.setText(f" {tr('tab.author')}")
            return

        self.btn_new_badge.setVisible(False)
        self.btn_new_badge.setToolTip("")
        self.btn_github.setText(f" {tr('tab.author')}")

    # ---- 配置持久化 (由 PresetMixin 提供) ----

    # ---- 预设管理 (由 PresetMixin 提供) ----

    # ---- 窗口事件 ----

    def show_normal_window(self) -> None:
        """显示并激活主窗口（从托盘恢复时调用）。"""
        self.show()
        self.setWindowState(Qt.WindowNoState)
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event) -> None:
        """关闭事件：配置了最小化到托盘时隐藏而非退出。"""
        if cfg.minimize_to_tray and self.tray_manager.is_visible():
            self.hide()
            event.ignore()
        else:
            # 窗口关闭前刷新所有待执行的防抖回调，
            # 避免最后一次滑块调整因延迟而丢失。
            _flush_all_debounced()
            event.accept()

    # ---- UI 初始化 ----

    def init_ui(self) -> None:
        """构建主界面：头部区域 + 参数/高级标签页。"""
        self.setStyleSheet(get_main_stylesheet())

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(32, 40, 32, 40)
        content_layout.setSpacing(20)

        # 头部区域。
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        logo_label = QLabel()
        logo_path = resource_path(os.path.join("FlowScroll", "resources", "FlowScroll.svg"))
        if os.path.exists(logo_path):
            logo_pixmap = QIcon(logo_path).pixmap(QSize(56, 56))
            logo_label.setPixmap(logo_pixmap)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)

        self.header_title = QLabel("FlowScroll")
        self.header_title.setObjectName("HeaderTitle")

        self.header_subtitle = QLabel(tr("main.subtitle"))
        self.header_subtitle.setObjectName("HeaderSubtitle")

        title_layout.addWidget(self.header_title)
        title_layout.addWidget(self.header_subtitle)

        header_layout.addWidget(logo_label)
        header_layout.addSpacing(12)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        self.btn_language = QPushButton(tr("main.language.button"))
        self.btn_language.setObjectName("BtnIcon")
        self.btn_language.setCursor(Qt.PointingHandCursor)
        self.btn_language.setStyleSheet(get_help_button_style())
        self.btn_language.clicked.connect(self.show_language_menu)
        header_layout.addWidget(self.btn_language)

        self.btn_help = QPushButton("?")
        self.btn_help.setObjectName("BtnIcon")
        self.btn_help.setCursor(Qt.PointingHandCursor)
        self.btn_help.setStyleSheet(get_help_button_style())
        self.btn_help.clicked.connect(self.show_help_dialog)
        header_layout.addWidget(self.btn_help)

        content_layout.addLayout(header_layout)
        content_layout.addSpacing(10)

        # 引入外部 Tab 构建函数。
        from FlowScroll.ui.tabs_builder import build_parameter_tab, build_advanced_tab

        # 标签页容器。
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)

        # 构建各标签页内容。
        tab1_widget = build_parameter_tab(self)
        self.tab_widget.addTab(tab1_widget, tr("main.tab.parameters"))

        tab2_widget = build_advanced_tab(self)
        self.tab_widget.addTab(tab2_widget, tr("main.tab.advanced"))

        self.tab_widget.currentChanged.connect(self.update_tab_height)
        self.update_tab_height(0)

        # 将标签页加入主体布局。
        content_layout.addWidget(self.tab_widget)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        self._build_language_menu()

    def update_tab_height(self, index) -> None:
        """切换标签页时更新各页的尺寸策略，确保当前页正常显示。"""
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if i == index:
                widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
            else:
                widget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.tab_widget.adjustSize()

    # ---- 语言切换 (由 LanguageMixin 提供) ----

    def retranslate_ui(self) -> None:
        """重新翻译所有 UI 文本（语言切换后调用）。

        委托给 LanguageMixin 的 _retranslate_in_place()，避免完整重建标签。
        """
        self._retranslate_in_place()

    # ---- UI 同步 ----

    def sync_ui_from_config(self) -> None:
        """将 cfg 中的值同步到 UI 控件。"""
        with STATE_LOCK:
            sensitivity = cfg.sensitivity
            speed_factor = cfg.speed_factor
            dead_zone = cfg.dead_zone
            overlay_size = cfg.overlay_size
            enable_horizontal = cfg.enable_horizontal
            minimize_to_tray = cfg.minimize_to_tray
            enable_inertia = cfg.enable_inertia
            disable_fullscreen = cfg.disable_fullscreen
            horizontal_hotkey = cfg.horizontal_hotkey

        self.ui_widgets["sensitivity"].setValue(sensitivity)
        self.ui_widgets["speed_factor"].setValue(speed_factor)
        self.ui_widgets["dead_zone"].setValue(dead_zone)
        self.ui_widgets["overlay_size"].setValue(overlay_size)
        self.ui_widgets["enable_horizontal"].setChecked(enable_horizontal)
        self.ui_widgets["minimize_to_tray"].setChecked(minimize_to_tray)
        self.ui_widgets["enable_inertia"].setChecked(enable_inertia)
        if "disable_fullscreen" in self.ui_widgets:
            self.ui_widgets["disable_fullscreen"].setChecked(disable_fullscreen)

        if horizontal_hotkey:
            self.lbl_hotkey.setText(hotkey_to_display(horizontal_hotkey))
        else:
            self.lbl_hotkey.setText(tr("main.hotkey.not_set"))
        self.refresh_config_storage_ui()

    def update_hotkey_label(self) -> None:
        """更新横向滚动快捷键的显示标签。"""
        with STATE_LOCK:
            horizontal_hotkey = cfg.horizontal_hotkey
        if horizontal_hotkey:
            self.lbl_hotkey.setText(hotkey_to_display(horizontal_hotkey))
        else:
            self.lbl_hotkey.setText(tr("main.hotkey.not_set"))

    # ---- Overlay 事件 ----

    def on_show_overlay(self) -> None:
        """显示准星覆盖层（在鼠标当前位置居中）。"""
        with STATE_LOCK:
            hide = cfg.hide_overlay
            size = cfg.overlay_size
        if hide:
            return
        self.overlay.set_direction("neutral")
        self.overlay.move(
            int(QCursor.pos().x() - size / 2),
            int(QCursor.pos().y() - size / 2),
        )
        self.overlay.show()
        self.overlay.raise_()

    def on_hide_overlay(self) -> None:
        """隐藏准星覆盖层。"""
        self.overlay.hide()

    # ---- 对话框 (由 DialogMixin 提供) ----

    def on_toggle_horizontal_hotkey(self) -> None:
        """切换横向滚动开关，并显示托盘通知。"""
        new_state = not cfg.enable_horizontal
        set_config_attr("enable_horizontal", new_state)
        self.ui_widgets["enable_horizontal"].setChecked(new_state)
        self.tray_manager.update_horizontal_state(new_state)
        self.tray_manager.show_message(
            tr("main.toggle_horizontal.title"),
            tr("main.toggle_horizontal.status_on" if new_state else "main.toggle_horizontal.status_off"),
        )

    def _on_tray_preset_selected(self, _internal_name: str) -> None:
        """托盘菜单预设切换后，同步 UI 控件并刷新预设下拉框。"""
        self.sync_ui_from_config()
        if hasattr(self, "combo_presets"):
            self._refresh_combo_presets()

    def toggle_autorun(self, checked) -> None:
        """切换开机自启动开关，失败时回滚 UI 状态。"""
        if not self.ctrl.autostart.set_autorun(checked):
            self.sender().blockSignals(True)
            self.sender().setChecked(not checked)
            self.sender().blockSignals(False)
            QMessageBox.warning(self, tr("main.settings_failed.title"), tr("main.settings_failed.body"))

    def open_config_storage_dialog(self) -> None:
        """打开配置存储位置设置对话框。"""
        from FlowScroll.ui.dialogs import ConfigStorageDialog

        dialog = ConfigStorageDialog(self)
        dialog.exec()
        self.refresh_config_storage_ui()

    def get_config_storage_summary(self) -> str:
        """获取配置存储位置的摘要字符串。"""
        from FlowScroll.core.config import get_config_file

        return str(get_config_file())

    def refresh_config_storage_ui(self) -> None:
        """刷新配置存储位置按钮的工具提示。"""
        btn = self.ui_widgets.get("config_path_button")
        if btn is not None:
            btn.setToolTip(self.get_config_storage_summary())

    def open_webdav_settings(self) -> None:
        """打开 WebDAV 云同步设置对话框。"""
        dialog = WebDAVSyncDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.save_presets_to_file()

    def open_work_mode_dialog(self) -> None:
        """打开工作模式设置对话框。"""
        from FlowScroll.ui.dialogs import WorkModeDialog

        dialog = WorkModeDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.save_presets_to_file()

    def open_filter_mode_dialog(self) -> None:
        """打开应用过滤模式设置对话框，进程名不可用时给出提示。"""
        from FlowScroll.ui.dialogs import AppFilterDialog

        with STATE_LOCK:
            process_name_status = runtime.process_name_status
            filter_mode = cfg.filter_mode
        if filter_mode in (1, 2) and process_name_status == "unavailable":
            QMessageBox.information(
                self,
                tr("dialog.filter.process_name_unavailable_title"),
                tr("dialog.filter.process_name_unavailable"),
            )
        dialog = AppFilterDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.save_presets_to_file()

    def open_reverse_mode_dialog(self) -> None:
        """打开滚轮方向反转设置对话框。"""
        from FlowScroll.ui.dialogs import ReverseModeDialog

        dialog = ReverseModeDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.save_presets_to_file()

    def open_inertia_settings_dialog(self) -> None:
        """打开惯性滚动设置对话框。"""
        from FlowScroll.ui.dialogs import InertiaSettingsDialog

        dialog = InertiaSettingsDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.ctrl.on_inertia_settings_accepted()
