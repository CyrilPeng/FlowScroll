import sys
import os
import math
import time
import threading
import json
import platform
import subprocess
import ctypes
from pynput import mouse, keyboard

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QSlider,
    QDoubleSpinBox,
    QPushButton,
    QDialog,
    QGridLayout,
    QCheckBox,
    QSystemTrayIcon,
    QMenu,
    QMessageBox,
    QComboBox,
    QInputDialog,
    QTextEdit,
    QKeySequenceEdit,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
)
from PySide6.QtCore import Qt, Signal, QObject, QTimer, QSize
from PySide6.QtGui import (
    QColor,
    QPainter,
    QPen,
    QFont,
    QPainterPath,
    QIcon,
    QCursor,
    QAction,
    QKeySequence,
)

from FlowScroll.platform import system_platform, OS_NAME
from FlowScroll.core.config import cfg, CONFIG_FILE
from FlowScroll.services.logging_service import logger, log_crash
from FlowScroll.core.engine import ScrollEngine
from FlowScroll.input.listeners import GlobalInputListener
from FlowScroll.services.autostart import AutoStartManager

from FlowScroll.ui.overlay import ResizableOverlay
from FlowScroll.ui.webdav_dialog import WebDAVSyncDialog
from FlowScroll.ui.components import HotkeyEdit
from FlowScroll.ui.utils import resource_path
from FlowScroll.ui.styles import get_main_stylesheet
from FlowScroll.services.window_monitor import WindowMonitor

mouse_controller = mouse.Controller()

# --- 逻辑信号桥接 ---
class LogicBridge(QObject):
    show_overlay = Signal()
    hide_overlay = Signal()
    update_direction = Signal(str)
    update_size = Signal(int)
    preview_size = Signal()
    toggle_horizontal = Signal()


# --- 主界面 ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        icon_name = system_platform.get_icon_name()
        if os.path.exists(resource_path(icon_name)):
            self.setWindowIcon(QIcon(resource_path(icon_name)))

        # 动态获取版本号
        self.current_version = "1.0.0"
        try:
            main_path = resource_path("main.py")
            if os.path.exists(main_path):
                import re
                with open(main_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    match = re.search(r'版本\s*v?([\d\.]+)', content)
                    if match:
                        self.current_version = match.group(1)
        except Exception:
            pass

        self.setWindowTitle(f"FlowScroll v{self.current_version}")
        self.setMinimumSize(420, 680)
        self.resize(650, 720)

        self.bridge = LogicBridge()
        self.overlay = ResizableOverlay()
        self.autostart = AutoStartManager()

        self.ui_widgets = {}
        self.presets = {"默认": cfg.to_dict()}
        self.current_preset_name = "默认"
        self.github_url = "https://github.com/CyrilPeng/FlowScroll"

        self.load_presets_from_file()

        # 确保窗口图标已经设置好再初始化系统托盘
        if self.windowIcon().isNull() and os.path.exists(resource_path(icon_name)):
            self.setWindowIcon(QIcon(resource_path(icon_name)))

        self.init_system_tray(icon_name)

        self.bridge.show_overlay.connect(self.on_show_overlay)
        self.bridge.hide_overlay.connect(self.on_hide_overlay)
        self.bridge.update_direction.connect(self.overlay.set_direction)
        self.bridge.update_size.connect(self.overlay.update_geometry)
        self.bridge.preview_size.connect(self.overlay.show_preview)
        self.bridge.toggle_horizontal.connect(self.on_toggle_horizontal_hotkey)

        self.init_ui()
        self.start_threads()
        self.check_for_updates()

    def check_for_updates(self):
        from FlowScroll.services.update_checker import UpdateCheckerThread
        self.update_checker = UpdateCheckerThread(self)
        self.update_checker.update_available.connect(self.on_update_available)
        self.update_checker.start()

    def on_update_available(self, latest_version, html_url):
        if latest_version != self.current_version:
            self.github_url = html_url
            if hasattr(self, 'btn_github'):
                self.btn_github.setToolTip(f"发现新版本: v{latest_version}\n点击前往下载")
                yellow_icon_path = resource_path(os.path.join("FlowScroll", "resources", "github_icon_yellow.svg"))
                if os.path.exists(yellow_icon_path):
                    self.btn_github.setIcon(QIcon(yellow_icon_path))
                self.btn_github.setStyleSheet("color: #EAB308;")

    def load_presets_from_file(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.presets = data.get("presets", {"默认": cfg.to_dict()})
                    last_used = data.get("last_used", "默认")
                    if last_used in self.presets:
                        self.current_preset_name = last_used
                        cfg.from_dict(self.presets[last_used])
            except:
                pass

    def save_presets_to_file(self):
        data = {"presets": self.presets, "last_used": self.current_preset_name}
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except:
            pass

    def init_system_tray(self, icon_name):
        self.tray_icon = QSystemTrayIcon(self)

        # 先尝试直接加载窗口图标，因为窗口图标已经设置好了
        if not self.windowIcon().isNull():
            self.tray_icon.setIcon(self.windowIcon())
        else:
            # 如果窗口图标没有，尝试加载 ICO 文件
            icon_path = resource_path(icon_name)
            if os.path.exists(icon_path):
                tray_icon = QIcon(icon_path)
                if not tray_icon.isNull():
                    self.tray_icon.setIcon(tray_icon)
                else:
                    # 最后使用默认图标
                    from PySide6.QtWidgets import QStyle

                    self.tray_icon.setIcon(
                        self.style().standardIcon(QStyle.SP_MessageBoxInformation)
                    )
            else:
                # 使用默认图标
                from PySide6.QtWidgets import QStyle

                self.tray_icon.setIcon(
                    self.style().standardIcon(QStyle.SP_MessageBoxInformation)
                )

        tray_menu = QMenu()
        action_show = QAction("显示设置", self)
        action_show.triggered.connect(self.show_normal_window)
        action_quit = QAction("退出程序", self)
        action_quit.triggered.connect(QApplication.instance().quit)

        tray_menu.addAction(action_show)
        tray_menu.addSeparator()
        tray_menu.addAction(action_quit)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_click)
        self.tray_icon.show()

    def on_tray_click(self, reason):
        if reason == QSystemTrayIcon.DoubleClick or reason == QSystemTrayIcon.Trigger:
            self.show_normal_window()

    def show_normal_window(self):
        self.show()
        self.setWindowState(Qt.WindowNoState)
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        if cfg.minimize_to_tray and self.tray_icon.isVisible():
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
        btn_help.setToolTip("功能说明与帮助")
        btn_help.setStyleSheet("""
            QPushButton {
                font-size: 16px; 
                font-weight: 800; 
                color: #CBD5E1; 
                background-color: #1E293B;
                border: 1px solid #475569;
                border-radius: 12px;
                min-width: 24px;
                min-height: 24px;
                padding: 4px;
            }
            QPushButton:hover { background-color: #334155; border-color: #64748B; color: #F8FAFC; }
        """)
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
            self.lbl_hotkey.setText(cfg.horizontal_hotkey)
        else:
            self.lbl_hotkey.setText("未设置快捷键")

    def open_hotkey_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("设置快捷键")
        dialog.setMinimumWidth(300)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(QLabel("按下要设置的快捷键："))

        hotkey_edit = HotkeyEdit()
        hotkey_edit.setKeySequence(QKeySequence(cfg.horizontal_hotkey))
        hotkey_edit.setMaximumSequenceLength(1)
        layout.addWidget(hotkey_edit)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_clear = QPushButton("清除")
        btn_clear.setObjectName("BtnDanger")
        btn_clear.clicked.connect(lambda: hotkey_edit.clear())
        btn_layout.addWidget(btn_clear)

        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_cancel)

        btn_ok = QPushButton("确定")
        btn_ok.setObjectName("BtnPrimary")
        btn_ok.clicked.connect(dialog.accept)
        btn_layout.addWidget(btn_ok)

        layout.addLayout(btn_layout)

        if dialog.exec() == QDialog.Accepted:
            cfg.horizontal_hotkey = hotkey_edit.keySequence().toString()
            self.update_hotkey_label()
            self.save_presets_to_file()

    def show_help_dialog(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("功能说明与帮助")
        msg.setIcon(QMessageBox.NoIcon)
        msg.setStyleSheet("""
            QMessageBox { background-color: #0F172A; }
            QLabel { color: #F8FAFC; font-size: 13px; line-height: 1.5; }
            QPushButton { background-color: #3B82F6; color: white; border-radius: 6px; padding: 6px 16px; font-weight: bold; }
            QPushButton:hover { background-color: #2563EB; }
        """)

        def img(name):
            path = resource_path(os.path.join("FlowScroll", "resources", name)).replace("\\", "/")
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
            f"{img('ic_lightbulb.svg')} <b>进阶用法：</b>在高级设置中绑定一个快捷键（如 <code>Shift</code>），平时默认关闭以保证纯净度。当需要横向看表格时，<b>按住 Shift 的同时按下鼠标中键</b>，即可瞬间解锁全向穿梭！<br><br>"
        )
        msg.setText(help_text)
        msg.exec()

    def toggle_advanced_settings(self, checked):
        self.adv_card.setVisible(checked)
        if checked:
            self.adv_btn_toggle.setText("▼ 高级设置 Advanced Settings")
        else:
            self.adv_btn_toggle.setText("▶ 高级设置 Advanced Settings")

    def on_filter_list_changed(self):
        lines = self.text_edit.toPlainText().split("\n")
        cfg.filter_list = [line.strip() for line in lines if line.strip()]
        self.save_presets_to_file()

    def on_toggle_horizontal_hotkey(self):
        new_state = not cfg.enable_horizontal
        setattr(cfg, "enable_horizontal", new_state)
        self.ui_widgets["enable_horizontal"].setChecked(new_state)
        if self.tray_icon.isVisible():
            state_str = "已开启" if new_state else "已关闭"
            self.tray_icon.showMessage(
                "横向滚动切换",
                f"横向滚动 {state_str}",
                QSystemTrayIcon.Information,
                1500,
            )

    def open_webdav_settings(self):
        dialog = WebDAVSyncDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.save_presets_to_file()

    def toggle_autorun(self, checked):
        if not self.autostart.set_autorun(checked):
            self.sender().blockSignals(True)
            self.sender().setChecked(not checked)
            self.sender().blockSignals(False)
            QMessageBox.warning(self, "设置失败", "权限不足或路径错误。")

    def save_new_preset(self):
        text, ok = QInputDialog.getText(
            self, "保存参数", "请输入预设名称:", text=self.current_preset_name
        )
        if ok and text:
            self.presets[text] = cfg.to_dict()
            self.current_preset_name = text
            self.save_presets_to_file()
            self.combo_presets.blockSignals(True)
            self.combo_presets.clear()
            self.combo_presets.addItems(list(self.presets.keys()))
            self.combo_presets.setCurrentText(text)
            self.combo_presets.blockSignals(False)

    def delete_preset(self):
        name = self.combo_presets.currentText()
        if name == "默认":
            QMessageBox.warning(self, "提示", "默认配置无法删除。")
            return
        del self.presets[name]
        self.current_preset_name = "默认"
        self.save_presets_to_file()
        self.combo_presets.blockSignals(True)
        self.combo_presets.clear()
        self.combo_presets.addItems(list(self.presets.keys()))
        self.combo_presets.setCurrentText("默认")
        self.combo_presets.blockSignals(False)
        self.load_selected_preset("默认")

    def on_filter_mode_changed(self, mode_id):
        cfg.filter_mode = mode_id
        # Enable/disable blacklist text edit based on mode
        self.text_edit.setEnabled(mode_id != 0)

    def load_selected_preset(self, name):
        if name in self.presets:
            cfg.from_dict(self.presets[name])
            self.current_preset_name = name
            self.ui_widgets["sensitivity"].setValue(cfg.sensitivity)
            self.ui_widgets["speed_factor"].setValue(cfg.speed_factor)
            self.ui_widgets["dead_zone"].setValue(cfg.dead_zone)
            self.ui_widgets["overlay_size"].setValue(cfg.overlay_size)
            self.ui_widgets["enable_horizontal"].setChecked(cfg.enable_horizontal)
            self.ui_widgets["minimize_to_tray"].setChecked(cfg.minimize_to_tray)

            # Update radio buttons and text edit
            if cfg.filter_mode == 0:
                self.radio_global.setChecked(True)
            else:
                self.radio_blacklist.setChecked(True)
            self.text_edit.setEnabled(cfg.filter_mode != 0)
            self.text_edit.setPlainText("\n".join(cfg.filter_list))

            self.update_hotkey_label()
            self.save_presets_to_file()

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
        except Exception:
            pass

        try:
            self.input_listener = GlobalInputListener(
                self.bridge, self.is_current_app_allowed
            )
            self.input_listener.start()
        except Exception as e:
            self.ui_widgets["enable_horizontal"].setChecked(False)
            QMessageBox.critical(
                self,
                "权限不足",
                "无法启动鼠标拦截服务。\n\n这通常是因为缺少底层挂钩权限。",
            )

        try:
            self.scroller = ScrollEngine(self.bridge, mouse_controller)
            self.scroller.start()
        except Exception:
            pass

    def is_current_app_allowed(self):
        if cfg.disable_fullscreen and cfg.is_fullscreen:
            return False

        if cfg.filter_mode == 0:
            return True

        app_name = cfg.current_window_name.lower()
        if cfg.filter_mode == 1:
            for keyword in cfg.filter_list:
                if keyword.lower() in app_name:
                    return False
            return True
        elif cfg.filter_mode == 2:
            for keyword in cfg.filter_list:
                if keyword.lower() in app_name:
                    return True
            return False
        return True
