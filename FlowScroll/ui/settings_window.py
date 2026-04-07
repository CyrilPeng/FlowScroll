import os
from pynput import mouse

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QDialog,
    QMessageBox,
    QInputDialog,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QTextEdit,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import (
    QAction,
    QIcon,
    QCursor,
)
from PySide6.QtWidgets import QMenu

from FlowScroll.platform import OS_NAME, system_platform
from FlowScroll.core.config import (
    STATE_LOCK,
    cfg,
    runtime,
    BUILTIN_PRESETS,
    DEFAULT_PRESET_NAME,
    get_config_file,
    get_config_override_source,
)
from FlowScroll.core.engine import ScrollEngine
from FlowScroll.core.rules import is_current_app_allowed
from FlowScroll.input.listeners import GlobalInputListener
from FlowScroll.services.autostart import AutoStartManager
from FlowScroll.i18n import set_ui_language, tr

from FlowScroll.ui.overlay import ResizableOverlay
from FlowScroll.ui.webdav_dialog import WebDAVSyncDialog
from FlowScroll.ui.components import HotkeyEdit
from FlowScroll.core.hotkeys import hotkey_to_display
from FlowScroll.ui.utils import resource_path
from FlowScroll.ui.styles import (
    get_main_stylesheet,
    get_dialog_stylesheet,
    get_help_button_style,
    get_textedit_style,
)
from FlowScroll.ui.bridge import LogicBridge
from FlowScroll.ui.preset_manager import PresetManager
from FlowScroll.ui.tray_manager import TrayManager
from FlowScroll.services.window_monitor import WindowMonitor
from FlowScroll.services.logging_service import logger
from FlowScroll.services.update_checker import (
    is_newer_version,
    is_prerelease_version,
)

mouse_controller = mouse.Controller()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        icon_name = system_platform.get_icon_name()
        if os.path.exists(resource_path(icon_name)):
            self.setWindowIcon(QIcon(resource_path(icon_name)))

        from FlowScroll import __version__

        self.current_version = __version__
        self.version_label = (
            f"{self.current_version} (Dev)"
            if is_prerelease_version(self.current_version)
            else self.current_version
        )

        self.setWindowTitle(f"FlowScroll v{self.version_label}")
        self.setMinimumSize(420, 680)
        self.resize(650, 720)

        self.bridge = LogicBridge()
        self.overlay = ResizableOverlay()
        self.autostart = AutoStartManager()
        self.preset_manager = PresetManager()
        self.window_monitor = None
        self.scroller = None
        self.input_listener = None

        self.ui_widgets = {}
        self.ui_text_widgets = {}
        self.github_url = "https://github.com/CyrilPeng/FlowScroll"
        self.latest_release_version = None
        self.update_badge_mode = "hidden"

        self.preset_manager.load_from_file()

        # 确保窗口图标已经设置好，再初始化系统托盘。
        if self.windowIcon().isNull() and os.path.exists(resource_path(icon_name)):
            self.setWindowIcon(QIcon(resource_path(icon_name)))

        self.tray_manager = TrayManager(self, icon_name)
        self.tray_manager.show_window.connect(self.show_normal_window)

        self.bridge.show_overlay.connect(self.on_show_overlay)
        self.bridge.hide_overlay.connect(self.on_hide_overlay)
        self.bridge.update_direction.connect(self.overlay.set_direction)
        self.bridge.update_size.connect(self.overlay.update_geometry)
        self.bridge.preview_size.connect(self.overlay.show_preview)
        self.bridge.toggle_horizontal.connect(self.on_toggle_horizontal_hotkey)

        self.init_ui()
        self.start_threads()
        self.check_for_updates()

    @property
    def presets(self):
        return self.preset_manager.presets

    @property
    def current_preset_name(self):
        return self.preset_manager.current_preset_name

    @current_preset_name.setter
    def current_preset_name(self, value) -> None:
        self.preset_manager.current_preset_name = value

    def check_for_updates(self) -> None:
        from FlowScroll.services.update_checker import UpdateCheckerThread

        self.update_checker = UpdateCheckerThread(self)
        self.update_checker.update_available.connect(self.on_update_available)
        self.update_checker.start()

    def _get_input_hook_failure_detail(self):
        if OS_NAME == "Darwin":
            return tr("main.input_hook_failure_detail.macos")

        if OS_NAME == "Windows":
            return tr("main.input_hook_failure_detail.windows")

        session_type = os.environ.get("XDG_SESSION_TYPE", "").strip().lower()
        has_wayland = bool(os.environ.get("WAYLAND_DISPLAY"))
        has_x11 = bool(os.environ.get("DISPLAY"))

        if session_type == "wayland" or has_wayland:
            return tr("main.input_hook_failure_detail.linux_wayland")
        if session_type == "x11" or has_x11:
            return tr("main.input_hook_failure_detail.linux_x11")
        if OS_NAME == "Linux":
            return tr("main.input_hook_failure_detail.linux_generic")

        return tr("main.input_hook_failure_detail.generic")

    def refresh_input_hook_status_ui(self) -> None:
        keyboard_ok = getattr(self, "keyboard_hook_available", True)
        mouse_ok = getattr(self, "mouse_hook_available", True)

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
                self.input_hook_status_label.setText(
                    f"{text}\n\n{self._get_input_hook_failure_detail()}"
                )
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

    def on_update_available(self, latest_version, html_url) -> None:
        self.latest_release_version = latest_version
        self.github_url = html_url
        if is_prerelease_version(self.current_version):
            self.update_badge_mode = "dev"
        elif is_newer_version(latest_version, self.current_version):
            self.update_badge_mode = "update"
        else:
            self.update_badge_mode = "hidden"
        self._refresh_update_indicator()

    def save_presets_to_file(self) -> None:
        self.preset_manager.save_to_file()

    def get_config_storage_summary(self):
        current_path = get_config_file()
        source = get_config_override_source()
        source_key = {
            "default": "tab.advanced.config_path_source_default",
            "custom": "tab.advanced.config_path_source_custom",
            "env_file": "tab.advanced.config_path_source_env_file",
            "env_dir": "tab.advanced.config_path_source_env_dir",
        }.get(source, "tab.advanced.config_path_source_default")
        return tr("tab.advanced.config_path_summary", source=tr(source_key), path=current_path)

    def refresh_config_storage_ui(self) -> None:
        btn = self.ui_widgets.get("config_path_button")
        if btn is not None:
            btn.setToolTip(self.get_config_storage_summary())

    def open_config_storage_dialog(self) -> None:
        from FlowScroll.ui.dialogs import ConfigStorageDialog

        dialog = ConfigStorageDialog(self)
        dialog.exec()
        self.refresh_config_storage_ui()

    def _all_preset_names(self):
        return self.preset_manager.get_all_names()

    def _refresh_combo(self, select_name):
        self.combo_presets.blockSignals(True)
        self.combo_presets.clear()
        self.combo_presets.addItems(self._all_preset_names())
        self.combo_presets.setCurrentText(select_name)
        self.combo_presets.blockSignals(False)

    def show_normal_window(self) -> None:
        self.show()
        self.setWindowState(Qt.WindowNoState)
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event) -> None:
        if cfg.minimize_to_tray and self.tray_manager.is_visible():
            self.hide()
            event.ignore()
        else:
            event.accept()

    def init_ui(self) -> None:
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
        logo_path = resource_path(
            os.path.join("FlowScroll", "resources", "FlowScroll.svg")
        )
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
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if i == index:
                widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
            else:
                widget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.tab_widget.adjustSize()

    def _build_language_menu(self):
        self.language_menu = QMenu(self)
        self.action_lang_auto = QAction(tr("main.language.auto"), self)
        self.action_lang_zh = QAction(tr("main.language.zh"), self)
        self.action_lang_en = QAction(tr("main.language.en"), self)
        for action in (self.action_lang_auto, self.action_lang_zh, self.action_lang_en):
            action.setCheckable(True)
            self.language_menu.addAction(action)

        self.action_lang_auto.triggered.connect(lambda: self._apply_language("auto"))
        self.action_lang_zh.triggered.connect(lambda: self._apply_language("zh-CN"))
        self.action_lang_en.triggered.connect(lambda: self._apply_language("en-US"))
        self._sync_language_menu_checks()

    def _sync_language_menu_checks(self):
        with STATE_LOCK:
            configured = getattr(cfg, "ui_language", "auto")
        self.action_lang_auto.setChecked(configured == "auto")
        self.action_lang_zh.setChecked(configured == "zh-CN")
        self.action_lang_en.setChecked(configured == "en-US")

    def show_language_menu(self) -> None:
        if not hasattr(self, "language_menu"):
            self._build_language_menu()
        self._sync_language_menu_checks()
        self.language_menu.exec(
            self.btn_language.mapToGlobal(self.btn_language.rect().bottomLeft())
        )

    def _apply_language(self, language_code: str):
        set_ui_language(language_code)
        self.save_presets_to_file()
        self.retranslate_ui()

    def _rebuild_tabs(self):
        from FlowScroll.ui.tabs_builder import build_parameter_tab, build_advanced_tab

        index = self.tab_widget.currentIndex()
        self.tab_widget.blockSignals(True)
        self.tab_widget.clear()
        self.ui_widgets = {}
        self.ui_text_widgets = {}

        tab1_widget = build_parameter_tab(self)
        self.tab_widget.addTab(tab1_widget, tr("main.tab.parameters"))
        tab2_widget = build_advanced_tab(self)
        self.tab_widget.addTab(tab2_widget, tr("main.tab.advanced"))
        self.tab_widget.setCurrentIndex(max(0, min(index, self.tab_widget.count() - 1)))
        self.tab_widget.blockSignals(False)
        self.update_tab_height(self.tab_widget.currentIndex())
        self.sync_ui_from_config()
        self._refresh_update_indicator()

    def _refresh_update_indicator(self):
        if not hasattr(self, "btn_new_badge") or not hasattr(self, "btn_github"):
            return

        if self.update_badge_mode == "dev":
            self.btn_new_badge.setText(tr("main.update.dev_badge"))
            self.btn_new_badge.setToolTip(
                tr(
                    "main.update.dev_tooltip",
                    version=self.latest_release_version or tr("main.update.unknown"),
                )
            )
            self.btn_new_badge.setVisible(True)
            self.btn_github.setText(
                f" {tr('tab.author_dev', version=self.latest_release_version or tr('main.update.unknown'))}"
            )
            return

        if self.update_badge_mode == "update":
            self.btn_new_badge.setText(tr("main.update.release_badge"))
            self.btn_new_badge.setToolTip(
                tr(
                    "main.update.release_tooltip",
                    version=self.latest_release_version or tr("main.update.unknown"),
                )
            )
            self.btn_new_badge.setVisible(True)
            self.btn_github.setText(f" {tr('tab.author')}")
            return

        self.btn_new_badge.setVisible(False)
        self.btn_new_badge.setToolTip("")
        self.btn_github.setText(f" {tr('tab.author')}")

    def retranslate_ui(self) -> None:
        self.setWindowTitle(f"FlowScroll v{self.version_label}")
        self.header_subtitle.setText(tr("main.subtitle"))
        self.btn_language.setText(tr("main.language.button"))
        self.tray_manager.retranslate_ui()
        self._build_language_menu()
        self._rebuild_tabs()
        self.refresh_input_hook_status_ui()

    def update_hotkey_label(self) -> None:
        if cfg.horizontal_hotkey:
            self.lbl_hotkey.setText(hotkey_to_display(cfg.horizontal_hotkey))
        else:
            self.lbl_hotkey.setText(tr("main.hotkey.not_set"))

    def open_hotkey_dialog(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle(tr("main.hotkey_dialog.title"))
        dialog.setMinimumWidth(300)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        hint_label = QLabel(tr("main.hotkey_dialog.hint"))
        hint_label.setWordWrap(True)
        hint_label.setTextFormat(Qt.RichText)
        hint_label.setStyleSheet("color: #CBD5E1; font-size: 13px; line-height: 1.5;")
        layout.addWidget(hint_label)

        hotkey_edit = HotkeyEdit()
        hotkey_edit.set_hotkey(cfg.horizontal_hotkey)
        hotkey_edit.setMaximumSequenceLength(1)
        layout.addWidget(hotkey_edit)

        btn_layout = QHBoxLayout()

        btn_clear = QPushButton(tr("main.hotkey_dialog.clear"))
        btn_clear.setObjectName("BtnDanger")
        btn_clear.clicked.connect(lambda: hotkey_edit.clear())
        btn_layout.addWidget(btn_clear)

        btn_layout.addStretch()

        btn_cancel = QPushButton(tr("main.hotkey_dialog.cancel"))
        btn_cancel.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_cancel)

        btn_ok = QPushButton(tr("main.hotkey_dialog.ok"))
        btn_ok.setObjectName("BtnPrimary")
        btn_ok.clicked.connect(dialog.accept)
        btn_layout.addWidget(btn_ok)

        layout.addLayout(btn_layout)

        if dialog.exec() == QDialog.Accepted:
            cfg.horizontal_hotkey = hotkey_edit.hotkey_text()
            self.update_hotkey_label()
            self.save_presets_to_file()

    def show_help_dialog(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle(tr("main.help.title"))
        dialog.setMinimumSize(520, 420)
        dialog.resize(620, 500)
        dialog.setSizeGripEnabled(True)
        dialog.setStyleSheet(get_dialog_stylesheet() + get_textedit_style())

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        def img(name):
            path = resource_path(os.path.join("FlowScroll", "resources", name)).replace(
                "\\", "/"
            )
            return f"<img src='{path}' width='14' height='14'>"

        help_text = tr(
            "main.help.html",
            speed_icon=img("ic_speed.svg"),
            power_icon=img("ic_power.svg"),
            target_icon=img("ic_target.svg"),
            move_icon=img("ic_move.svg"),
        )

        help_view = QTextEdit(dialog)
        help_view.setReadOnly(True)
        help_view.setAcceptRichText(True)
        help_view.setHtml(help_text)
        help_view.setMinimumHeight(280)
        layout.addWidget(help_view)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_close = QPushButton(tr("main.hotkey_dialog.ok"))
        btn_close.setObjectName("BtnPrimary")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(dialog.accept)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

        dialog.exec()

    def on_toggle_horizontal_hotkey(self) -> None:
        new_state = not cfg.enable_horizontal
        setattr(cfg, "enable_horizontal", new_state)
        self.ui_widgets["enable_horizontal"].setChecked(new_state)
        self.tray_manager.show_message(
            tr("main.toggle_horizontal.title"),
            tr(
                "main.toggle_horizontal.status_on"
                if new_state
                else "main.toggle_horizontal.status_off"
            ),
        )

    def open_webdav_settings(self) -> None:
        dialog = WebDAVSyncDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.save_presets_to_file()

    def open_work_mode_dialog(self) -> None:
        from FlowScroll.ui.dialogs import WorkModeDialog

        dialog = WorkModeDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.save_presets_to_file()

    def open_filter_mode_dialog(self) -> None:
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
        from FlowScroll.ui.dialogs import ReverseModeDialog

        dialog = ReverseModeDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.save_presets_to_file()

    def open_inertia_settings_dialog(self) -> None:
        from FlowScroll.ui.dialogs import InertiaSettingsDialog

        dialog = InertiaSettingsDialog(self)
        if dialog.exec() == QDialog.Accepted:
            if hasattr(self, "scroller") and self.scroller:
                self.scroller.update_friction()
            self.save_presets_to_file()

    def toggle_autorun(self, checked) -> None:
        if not self.autostart.set_autorun(checked):
            self.sender().blockSignals(True)
            self.sender().setChecked(not checked)
            self.sender().blockSignals(False)
            QMessageBox.warning(
                self, tr("main.settings_failed.title"), tr("main.settings_failed.body")
            )

    def _confirm_preset_action(self, title, text):
        reply = QMessageBox.question(
            self,
            title,
            text,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return reply == QMessageBox.Yes

    def save_new_preset(self) -> None:
        suggested = self.current_preset_name
        if suggested in BUILTIN_PRESETS:
            suggested = ""
        text, ok = QInputDialog.getText(
            self,
            tr("main.preset.save_title"),
            tr("main.preset.save_prompt"),
            text=suggested,
        )
        if ok and text:
            if text in BUILTIN_PRESETS:
                QMessageBox.warning(
                    self,
                    tr("main.preset.builtin_warning_title"),
                    tr("main.preset.builtin_warning_body"),
                )
                return
            if text in self.presets and not self._confirm_preset_action(
                tr("main.preset.overwrite_title"),
                tr("main.preset.overwrite_body", name=text),
            ):
                return
            self.preset_manager.save_preset(text)
            self._refresh_combo(text)

    def delete_preset(self) -> None:
        name = self.combo_presets.currentText()
        if name in BUILTIN_PRESETS:
            QMessageBox.warning(
                self,
                tr("main.preset.delete_builtin_title"),
                tr("main.preset.delete_builtin_body"),
            )
            return
        if name not in self.presets:
            return
        if not self._confirm_preset_action(
            tr("main.preset.delete_confirm_title"),
            tr("main.preset.delete_confirm_body", name=name),
        ):
            return
        self.preset_manager.delete_preset(name)
        self._refresh_combo(DEFAULT_PRESET_NAME)
        self.load_selected_preset(DEFAULT_PRESET_NAME)

    def load_selected_preset(self, name) -> None:
        if not self.preset_manager.load_preset(name):
            return
        self.sync_ui_from_config()

        if hasattr(self, "scroller") and self.scroller:
            self.scroller.update_friction()

        self.save_presets_to_file()

    def sync_ui_from_config(self) -> None:
        self.ui_widgets["sensitivity"].setValue(cfg.sensitivity)
        self.ui_widgets["speed_factor"].setValue(cfg.speed_factor)
        self.ui_widgets["dead_zone"].setValue(cfg.dead_zone)
        self.ui_widgets["overlay_size"].setValue(cfg.overlay_size)
        self.ui_widgets["enable_horizontal"].setChecked(cfg.enable_horizontal)
        self.ui_widgets["minimize_to_tray"].setChecked(cfg.minimize_to_tray)
        self.ui_widgets["enable_inertia"].setChecked(cfg.enable_inertia)
        if "disable_fullscreen" in self.ui_widgets:
            self.ui_widgets["disable_fullscreen"].setChecked(cfg.disable_fullscreen)

        self.update_hotkey_label()
        self.refresh_config_storage_ui()

    def on_show_overlay(self) -> None:
        if cfg.hide_overlay:
            return
        self.overlay.set_direction("neutral")
        self.overlay.move(
            int(QCursor.pos().x() - cfg.overlay_size / 2),
            int(QCursor.pos().y() - cfg.overlay_size / 2),
        )
        self.overlay.show()
        self.overlay.raise_()

    def on_hide_overlay(self) -> None:
        self.overlay.hide()

    def start_threads(self) -> None:
        self.window_monitor = None
        self.scroller = None
        self.input_listener = None
        self.keyboard_hook_available = True
        self.mouse_hook_available = True

        try:
            self.window_monitor = WindowMonitor()
            self.window_monitor.start()
        except Exception as e:
            logger.error(f"Failed to start WindowMonitor: {e}")

        try:
            self.scroller = ScrollEngine(self.bridge, mouse_controller)
            self.scroller.start()
        except Exception as e:
            logger.error(f"Failed to start ScrollEngine: {e}")
            QMessageBox.critical(
                self,
                tr("main.scroll_engine_failed.title"),
                tr("main.scroll_engine_failed.body"),
            )

        try:
            self.input_listener = GlobalInputListener(
                self.bridge, is_current_app_allowed, self.scroller
            )
            self.input_listener.start()
            self.keyboard_hook_available = self.input_listener.keyboard_hook_available
            self.mouse_hook_available = self.input_listener.mouse_hook_available
            if not self.input_listener.keyboard_hook_available:
                QMessageBox.warning(
                    self,
                    tr("main.keyboard_hook_failed.title"),
                    tr(
                        "main.keyboard_hook_failed.body",
                        detail=self._get_input_hook_failure_detail(),
                    ),
                )
            if not self.input_listener.mouse_hook_available:
                QMessageBox.warning(
                    self,
                    tr("main.mouse_hook_failed.title"),
                    tr(
                        "main.mouse_hook_failed.body",
                        detail=self._get_input_hook_failure_detail(),
                    ),
                )
        except Exception as e:
            logger.error(f"Failed to start GlobalInputListener: {e}")
            self.keyboard_hook_available = False
            self.mouse_hook_available = False
            if "enable_horizontal" in self.ui_widgets:
                self.ui_widgets["enable_horizontal"].setChecked(False)
            QMessageBox.critical(
                self,
                tr("main.permission_denied.title"),
                tr("main.permission_denied.body"),
            )
        self.refresh_input_hook_status_ui()
