import os

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
    set_config_attr,
)
from FlowScroll.i18n import set_ui_language, tr

from FlowScroll.ui.app_controller import ApplicationController
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
from FlowScroll.ui.tray_manager import TrayManager
from FlowScroll.services.update_checker import (
    is_newer_version,
    is_prerelease_version,
)


class MainWindow(QMainWindow):
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

        self.tray_manager = TrayManager(self, icon_name)
        self.tray_manager.show_window.connect(self.show_normal_window)

        self.ctrl.bridge.show_overlay.connect(self.on_show_overlay)
        self.ctrl.bridge.hide_overlay.connect(self.on_hide_overlay)
        self.ctrl.bridge.update_direction.connect(self.overlay.set_direction)
        self.ctrl.bridge.update_size.connect(self.overlay.update_geometry)
        self.ctrl.bridge.preview_size.connect(self.overlay.show_preview)
        self.ctrl.bridge.toggle_horizontal.connect(self.on_toggle_horizontal_hotkey)

        self.init_ui()
        self._start_threads()
        self.ctrl.check_for_updates(self._refresh_update_indicator)

    # ---- 代理属性：向后兼容 tabs_builder / dialogs 等 ----

    @property
    def presets(self):
        """代理属性：返回当前预设字典。"""
        return self.ctrl.presets

    @property
    def current_preset_name(self):
        """代理属性：返回当前预设名称。"""
        return self.ctrl.current_preset_name

    @current_preset_name.setter
    def current_preset_name(self, value) -> None:
        """代理属性：设置当前预设名称。"""
        self.ctrl.current_preset_name = value

    @property
    def bridge(self):
        """代理属性：返回 LogicBridge 实例。"""
        return self.ctrl.bridge

    @property
    def autostart(self):
        """代理属性：返回 AutoStartManager 实例。"""
        return self.ctrl.autostart

    @property
    def preset_manager(self):
        """代理属性：返回 PresetManager 实例。"""
        return self.ctrl.preset_manager

    @property
    def scroller(self):
        """代理属性：返回 ScrollEngine 实例。"""
        return self.ctrl.scroller

    @property
    def keyboard_hook_available(self):
        """代理属性：返回键盘钩子是否可用。"""
        return self.ctrl.keyboard_hook_available

    @keyboard_hook_available.setter
    def keyboard_hook_available(self, value):
        """代理属性：设置键盘钩子可用状态。"""
        self.ctrl.keyboard_hook_available = value

    @property
    def mouse_hook_available(self):
        """代理属性：返回鼠标钩子是否可用。"""
        return self.ctrl.mouse_hook_available

    @mouse_hook_available.setter
    def mouse_hook_available(self, value):
        """代理属性：设置鼠标钩子可用状态。"""
        self.ctrl.mouse_hook_available = value

    @property
    def github_url(self):
        """代理属性：返回 GitHub 仓库 URL。"""
        return self.ctrl.github_url

    @github_url.setter
    def github_url(self, value):
        """代理属性：设置 GitHub 仓库 URL。"""
        self.ctrl.github_url = value

    @property
    def latest_release_version(self):
        """代理属性：返回最新发布版本号。"""
        return self.ctrl.latest_release_version

    @latest_release_version.setter
    def latest_release_version(self, value):
        """代理属性：设置最新发布版本号。"""
        self.ctrl.latest_release_version = value

    @property
    def update_badge_mode(self):
        """代理属性：返回更新徽章模式。"""
        return self.ctrl.update_badge_mode

    @update_badge_mode.setter
    def update_badge_mode(self, value):
        """代理属性：设置更新徽章模式。"""
        self.ctrl.update_badge_mode = value

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
                self.input_hook_status_label.setText(
                    f"{text}\n\n{self.ctrl._get_input_hook_failure_detail()}"
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
            self.btn_new_badge.setToolTip(
                tr("main.update.release_tooltip", version=latest)
            )
            self.btn_new_badge.setVisible(True)
            self.btn_github.setText(f" {tr('tab.author')}")
            return

        self.btn_new_badge.setVisible(False)
        self.btn_new_badge.setToolTip("")
        self.btn_github.setText(f" {tr('tab.author')}")

    # ---- 配置持久化 ----

    def save_presets_to_file(self) -> None:
        """将当前预设和配置持久化到磁盘。"""
        self.ctrl.save_presets_to_file()

    def get_config_storage_summary(self):
        """返回配置存储位置的可读摘要文本。"""
        return self.ctrl.get_config_storage_summary()

    def refresh_config_storage_ui(self) -> None:
        """刷新配置路径按钮的工具提示。"""
        btn = self.ui_widgets.get("config_path_button")
        if btn is not None:
            btn.setToolTip(self.get_config_storage_summary())

    def open_config_storage_dialog(self) -> None:
        """打开配置存储位置设置对话框。"""
        from FlowScroll.ui.dialogs import ConfigStorageDialog

        dialog = ConfigStorageDialog(self)
        dialog.exec()
        self.refresh_config_storage_ui()

    # ---- 预设管理 ----

    def _all_preset_names(self):
        """返回所有预设名称列表（内置 + 自定义）。"""
        return self.ctrl.preset_manager.get_all_names()

    def _refresh_combo(self, select_name):
        """刷新预设下拉框，选中指定名称。"""
        self.combo_presets.blockSignals(True)
        self.combo_presets.clear()
        self.combo_presets.addItems(self._all_preset_names())
        self.combo_presets.setCurrentText(select_name)
        self.combo_presets.blockSignals(False)

    def save_new_preset(self) -> None:
        """保存新预设：弹出输入框，校验名称后持久化。"""
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
            self.ctrl.save_new_preset(text)
            self._refresh_combo(text)

    def delete_preset(self) -> None:
        """删除自定义预设：确认后删除并回退到默认预设。"""
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
        self.ctrl.delete_preset(name)
        self._refresh_combo(DEFAULT_PRESET_NAME)
        self.load_selected_preset(DEFAULT_PRESET_NAME)

    def load_selected_preset(self, name) -> None:
        """加载指定预设并同步 UI 控件。"""
        self.ctrl.load_selected_preset(name)
        self.sync_ui_from_config()

    def _confirm_preset_action(self, title, text):
        """弹出确认对话框，返回用户是否选择"是"。"""
        reply = QMessageBox.question(
            self,
            title,
            text,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return reply == QMessageBox.Yes

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
        """切换标签页时更新各页的尺寸策略，确保当前页正常显示。"""
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if i == index:
                widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
            else:
                widget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.tab_widget.adjustSize()

    # ---- 语言切换 ----

    def _build_language_menu(self):
        """构建语言切换菜单（自动/中文/英文）。"""
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
        """根据配置同步语言菜单的选中状态。"""
        with STATE_LOCK:
            configured = getattr(cfg, "ui_language", "auto")
        self.action_lang_auto.setChecked(configured == "auto")
        self.action_lang_zh.setChecked(configured == "zh-CN")
        self.action_lang_en.setChecked(configured == "en-US")

    def show_language_menu(self) -> None:
        """在语言按钮下方弹出语言选择菜单。"""
        if not hasattr(self, "language_menu"):
            self._build_language_menu()
        self._sync_language_menu_checks()
        self.language_menu.exec(
            self.btn_language.mapToGlobal(self.btn_language.rect().bottomLeft())
        )

    def _apply_language(self, language_code: str):
        """切换 UI 语言并持久化配置。"""
        set_ui_language(language_code)
        self.save_presets_to_file()
        self.retranslate_ui()

    def _rebuild_tabs(self):
        """重建标签页内容（语言切换后调用）。"""
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

    def retranslate_ui(self) -> None:
        """重新翻译所有 UI 文本（语言切换后调用）。"""
        self.setWindowTitle(f"FlowScroll v{self.ctrl.version_label}")
        self.header_subtitle.setText(tr("main.subtitle"))
        self.btn_language.setText(tr("main.language.button"))
        self.tray_manager.retranslate_ui()
        self._build_language_menu()
        self._rebuild_tabs()
        self.refresh_input_hook_status_ui()

    # ---- UI 同步 ----

    def sync_ui_from_config(self) -> None:
        """将 cfg 中的值同步到 UI 控件。"""
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

    def update_hotkey_label(self) -> None:
        """更新横向滚动快捷键的显示标签。"""
        if cfg.horizontal_hotkey:
            self.lbl_hotkey.setText(hotkey_to_display(cfg.horizontal_hotkey))
        else:
            self.lbl_hotkey.setText(tr("main.hotkey.not_set"))

    # ---- Overlay 事件 ----

    def on_show_overlay(self) -> None:
        """显示准星覆盖层（在鼠标当前位置居中）。"""
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
        """隐藏准星覆盖层。"""
        self.overlay.hide()

    # ---- 对话框 ----

    def open_hotkey_dialog(self) -> None:
        """打开横向滚动快捷键设置对话框。"""
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
            set_config_attr("horizontal_hotkey", hotkey_edit.hotkey_text())
            self.update_hotkey_label()
            self.save_presets_to_file()

    def show_help_dialog(self) -> None:
        """显示帮助对话框（含参数说明和图标）。"""
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
            """辅助函数：构建资源图片的 HTML img 标签。"""
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
        """切换横向滚动开关，并显示托盘通知。"""
        new_state = not cfg.enable_horizontal
        set_config_attr("enable_horizontal", new_state)
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

    def toggle_autorun(self, checked) -> None:
        """切换开机自启动开关，失败时回滚 UI 状态。"""
        if not self.autostart.set_autorun(checked):
            self.sender().blockSignals(True)
            self.sender().setChecked(not checked)
            self.sender().blockSignals(False)
            QMessageBox.warning(
                self, tr("main.settings_failed.title"), tr("main.settings_failed.body")
            )
