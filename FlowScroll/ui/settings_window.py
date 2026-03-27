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
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import (
    QIcon,
    QCursor,
)

from FlowScroll.platform import system_platform
from FlowScroll.core.config import cfg, BUILTIN_PRESETS, DEFAULT_PRESET_NAME
from FlowScroll.core.engine import ScrollEngine
from FlowScroll.core.rules import is_current_app_allowed
from FlowScroll.input.listeners import GlobalInputListener
from FlowScroll.services.autostart import AutoStartManager

from FlowScroll.ui.overlay import ResizableOverlay
from FlowScroll.ui.webdav_dialog import WebDAVSyncDialog
from FlowScroll.ui.components import HotkeyEdit
from FlowScroll.core.hotkeys import hotkey_to_display
from FlowScroll.ui.utils import resource_path
from FlowScroll.ui.styles import (
    get_main_stylesheet,
    get_help_dialog_style,
    get_help_button_style,
)
from FlowScroll.ui.bridge import LogicBridge
from FlowScroll.ui.preset_manager import PresetManager
from FlowScroll.ui.tray_manager import TrayManager
from FlowScroll.services.window_monitor import WindowMonitor
from FlowScroll.services.logging_service import logger
from FlowScroll.services.update_checker import is_newer_version

mouse_controller = mouse.Controller()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        icon_name = system_platform.get_icon_name()
        if os.path.exists(resource_path(icon_name)):
            self.setWindowIcon(QIcon(resource_path(icon_name)))

        from FlowScroll import __version__

        self.current_version = __version__

        self.setWindowTitle(f"FlowScroll v{self.current_version}")
        self.setMinimumSize(420, 680)
        self.resize(650, 720)

        self.bridge = LogicBridge()
        self.overlay = ResizableOverlay()
        self.autostart = AutoStartManager()
        self.preset_manager = PresetManager()

        self.ui_widgets = {}
        self.github_url = "https://github.com/CyrilPeng/FlowScroll"

        self.preset_manager.load_from_file()

        # 确保窗口图标已经设置好再初始化系统托盘
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
    def current_preset_name(self, value):
        self.preset_manager.current_preset_name = value

    def check_for_updates(self):
        from FlowScroll.services.update_checker import UpdateCheckerThread

        self.update_checker = UpdateCheckerThread(self)
        self.update_checker.update_available.connect(self.on_update_available)
        self.update_checker.start()

    def on_update_available(self, latest_version, html_url):
        if is_newer_version(latest_version, self.current_version):
            self.github_url = html_url
            if hasattr(self, "btn_new_badge"):
                self.btn_new_badge.setVisible(True)

    def save_presets_to_file(self):
        self.preset_manager.save_to_file()

    def _all_preset_names(self):
        return self.preset_manager.get_all_names()

    def _refresh_combo(self, select_name):
        self.combo_presets.blockSignals(True)
        self.combo_presets.clear()
        self.combo_presets.addItems(self._all_preset_names())
        self.combo_presets.setCurrentText(select_name)
        self.combo_presets.blockSignals(False)

    def show_normal_window(self):
        self.show()
        self.setWindowState(Qt.WindowNoState)
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        if cfg.minimize_to_tray and self.tray_manager.is_visible():
            self.hide()
            event.ignore()
        else:
            event.accept()

    def init_ui(self):
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

        # --- Header Section ---
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

        header_title = QLabel("FlowScroll")
        header_title.setObjectName("HeaderTitle")

        header_subtitle = QLabel("全局平滑滚动，按下中键，即刻享受")
        header_subtitle.setObjectName("HeaderSubtitle")

        title_layout.addWidget(header_title)
        title_layout.addWidget(header_subtitle)

        header_layout.addWidget(logo_label)
        header_layout.addSpacing(12)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        btn_help = QPushButton("?")
        btn_help.setObjectName("BtnIcon")
        btn_help.setCursor(Qt.PointingHandCursor)
        btn_help.setStyleSheet(get_help_button_style())
        btn_help.clicked.connect(self.show_help_dialog)
        header_layout.addWidget(btn_help)

        content_layout.addLayout(header_layout)
        content_layout.addSpacing(10)

        # 引入外部帮助函数和Tab构建器
        from FlowScroll.ui.tabs_builder import build_parameter_tab, build_advanced_tab

        # --- Tab Widget ---
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)

        # Build tabs
        tab1_widget = build_parameter_tab(self)
        self.tab_widget.addTab(tab1_widget, "参数调校")

        tab2_widget = build_advanced_tab(self)
        self.tab_widget.addTab(tab2_widget, "高级设置")

        self.tab_widget.currentChanged.connect(self.update_tab_height)
        self.update_tab_height(0)

        # Add tab widget to content layout
        content_layout.addWidget(self.tab_widget)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

    def update_tab_height(self, index):
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if i == index:
                widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
            else:
                widget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.tab_widget.adjustSize()

    def update_hotkey_label(self):
        if cfg.horizontal_hotkey:
            self.lbl_hotkey.setText(hotkey_to_display(cfg.horizontal_hotkey))
        else:
            self.lbl_hotkey.setText("未设置快捷键")

    def open_hotkey_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("设置快捷键")
        dialog.setMinimumWidth(300)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        hotkey_edit = HotkeyEdit()
        hotkey_edit.set_hotkey(cfg.horizontal_hotkey)
        hotkey_edit.setMaximumSequenceLength(1)
        layout.addWidget(hotkey_edit)

        btn_layout = QHBoxLayout()

        btn_clear = QPushButton("清除")
        btn_clear.setObjectName("BtnDanger")
        btn_clear.clicked.connect(lambda: hotkey_edit.clear())
        btn_layout.addWidget(btn_clear)

        btn_layout.addStretch()

        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_cancel)

        btn_ok = QPushButton("确定")
        btn_ok.setObjectName("BtnPrimary")
        btn_ok.clicked.connect(dialog.accept)
        btn_layout.addWidget(btn_ok)

        layout.addLayout(btn_layout)

        if dialog.exec() == QDialog.Accepted:
            cfg.horizontal_hotkey = hotkey_edit.hotkey_text()
            self.update_hotkey_label()
            self.save_presets_to_file()

    def show_help_dialog(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("功能说明与帮助")
        msg.setIcon(QMessageBox.NoIcon)
        msg.setStyleSheet(get_help_dialog_style())
        msg.setTextFormat(Qt.RichText)

        def img(name):
            path = resource_path(os.path.join("FlowScroll", "resources", name)).replace(
                "\\", "/"
            )
            return f"<img src='{path}' width='14' height='14'>"

        help_text = (
            f"<b>{img('ic_speed.svg')} 加速度曲线</b><br>"
            "决定了滑动距离与最终滚动速度之间的非线性关系。数值越大，用力滑动时页面飞出得越远。网页浏览推荐 1.0~1.5，长代码/文档推荐 2.0+。<br><br>"
            f"<b>{img('ic_power.svg')} 基础速度倍率</b><br>"
            "全局滚动的乘数放大器。如果你觉得整体滚动太慢或太快，调整此项。<br><br>"
            f"<b>{img('ic_target.svg')} 中心死区缓冲</b><br>"
            "按下中键后，鼠标需要移动多少像素才会触发滚动。建议保留极小值以防止误触和手抖。<br><br>"
            f"<b>{img('ic_move.svg')} 横向穿梭模式</b><br>"
            "<b>未开启时：</b>提供绝对纯净的单轴（Y轴）物理惯性滚动。屏蔽一切水平手抖，保证日常刷网页、看代码时的极致专注与平稳。<br>"
            "<b>开启时：</b>解锁全向（X轴+Y轴）平移引擎！鼠标中键将化身为触控板，支持 360° 自由滑动。非常适合浏览超宽 Excel 表格、无限画板或视频剪辑的时间轴。<br>"
            f"{img('ic_lightbulb.svg')} <b>进阶用法：</b>在高级设置中绑定一个快捷键（如 <code>⬆️</code>），平时默认关闭以保证纯净度。当需要横向看表格时，<b>按 ⬆️ 后再按下鼠标中键</b>，即可瞬间解锁全向穿梭！<br><br>"
        )
        msg.setText(help_text)
        msg.exec()

    def toggle_advanced_settings(self, checked):
        self.adv_card.setVisible(checked)
        if checked:
            self.adv_btn_toggle.setText("▼ 高级设置 Advanced Settings")
        else:
            self.adv_btn_toggle.setText("▶ 高级设置 Advanced Settings")

    def on_toggle_horizontal_hotkey(self):
        new_state = not cfg.enable_horizontal
        setattr(cfg, "enable_horizontal", new_state)
        self.ui_widgets["enable_horizontal"].setChecked(new_state)
        self.tray_manager.show_message(
            "横向滚动切换",
            f"横向滚动 {'已开启' if new_state else '已关闭'}",
        )

    def open_webdav_settings(self):
        dialog = WebDAVSyncDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.save_presets_to_file()

    def open_work_mode_dialog(self):
        from FlowScroll.ui.dialogs import WorkModeDialog

        dialog = WorkModeDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.save_presets_to_file()

    def open_reverse_mode_dialog(self):
        from FlowScroll.ui.dialogs import ReverseModeDialog

        dialog = ReverseModeDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.save_presets_to_file()

    def open_inertia_settings_dialog(self):
        from FlowScroll.ui.dialogs import InertiaSettingsDialog

        dialog = InertiaSettingsDialog(self)
        if dialog.exec() == QDialog.Accepted:
            if hasattr(self, "scroller") and self.scroller:
                self.scroller.update_friction()
            self.save_presets_to_file()

    def toggle_autorun(self, checked):
        if not self.autostart.set_autorun(checked):
            self.sender().blockSignals(True)
            self.sender().setChecked(not checked)
            self.sender().blockSignals(False)
            QMessageBox.warning(self, "设置失败", "权限不足或路径错误。")

    def _confirm_preset_action(self, title, text):
        reply = QMessageBox.question(
            self,
            title,
            text,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return reply == QMessageBox.Yes

    def save_new_preset(self):
        suggested = self.current_preset_name
        if suggested in BUILTIN_PRESETS:
            suggested = ""
        text, ok = QInputDialog.getText(
            self, "保存预设", "请输入预设名称:", text=suggested
        )
        if ok and text:
            if text in BUILTIN_PRESETS:
                QMessageBox.warning(
                    self, "提示", "内置预设名称不可使用，请换一个名称。"
                )
                return
            if text in self.presets and not self._confirm_preset_action(
                "确认覆盖",
                f"预设“{text}”已存在，是否用当前配置覆盖它？",
            ):
                return
            self.preset_manager.save_preset(text)
            self._refresh_combo(text)

    def delete_preset(self):
        name = self.combo_presets.currentText()
        if name in BUILTIN_PRESETS:
            QMessageBox.warning(self, "提示", "内置预设无法删除。")
            return
        if name not in self.presets:
            return
        if not self._confirm_preset_action(
            "确认删除",
            f"确定要删除预设“{name}”吗？此操作不可撤销。",
        ):
            return
        self.preset_manager.delete_preset(name)
        self._refresh_combo(DEFAULT_PRESET_NAME)
        self.load_selected_preset(DEFAULT_PRESET_NAME)

    def load_selected_preset(self, name):
        if not self.preset_manager.load_preset(name):
            return
        self.sync_ui_from_config()

        if hasattr(self, "scroller") and self.scroller:
            self.scroller.update_friction()

        self.save_presets_to_file()

    def sync_ui_from_config(self):
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

    def on_show_overlay(self):
        self.overlay.set_direction("neutral")
        self.overlay.move(
            int(QCursor.pos().x() - cfg.overlay_size / 2),
            int(QCursor.pos().y() - cfg.overlay_size / 2),
        )
        self.overlay.show()
        self.overlay.raise_()

    def on_hide_overlay(self):
        self.overlay.hide()

    def start_threads(self):
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

        try:
            self.input_listener = GlobalInputListener(
                self.bridge, is_current_app_allowed, self.scroller
            )
            self.input_listener.start()
        except Exception as e:
            logger.error(f"Failed to start GlobalInputListener: {e}")
            self.ui_widgets["enable_horizontal"].setChecked(False)
            QMessageBox.critical(
                self,
                "权限不足",
                "无法启动鼠标拦截服务。\n\n这通常是因为缺少底层挂钩权限。",
            )
