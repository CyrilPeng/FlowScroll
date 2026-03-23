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

from FlowMouse.platform import system_platform, OS_NAME
from FlowMouse.core.config import cfg, CONFIG_FILE
from FlowMouse.services.logging_service import logger, log_crash
from FlowMouse.core.engine import ScrollEngine
from FlowMouse.input.listeners import GlobalInputListener
from FlowMouse.services.autostart import AutoStartManager

from FlowMouse.ui.overlay import ResizableOverlay
from FlowMouse.ui.webdav_dialog import WebDAVSyncDialog
from FlowMouse.ui.components import HotkeyEdit


# --- 资源定位 ---
def resource_path(relative_path):
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        # 为了兼容，依然使用当前工作目录
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


mouse_controller = mouse.Controller()


# --- 窗口侦听器 ---
class WindowMonitor(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)

    def run(self):
        time.sleep(2)
        while True:
            try:
                name, cls_name, is_fullscreen = (
                    system_platform.get_frontmost_window_info()
                )
                cfg.current_window_name = name
                cfg.current_window_class = cls_name
                cfg.is_fullscreen = is_fullscreen
            except Exception:
                pass
            time.sleep(0.5)


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

        self.setWindowTitle("FlowMouse")
        self.setMinimumSize(420, 680)
        self.resize(650, 720)

        self.bridge = LogicBridge()
        self.overlay = ResizableOverlay()
        self.autostart = AutoStartManager()

        self.ui_widgets = {}
        self.presets = {"默认": cfg.to_dict()}
        self.current_preset_name = "默认"

        self.load_presets_from_file()
        self.init_system_tray(icon_name)

        self.bridge.show_overlay.connect(self.on_show_overlay)
        self.bridge.hide_overlay.connect(self.on_hide_overlay)
        self.bridge.update_direction.connect(self.overlay.set_direction)
        self.bridge.update_size.connect(self.overlay.update_geometry)
        self.bridge.preview_size.connect(self.overlay.show_preview)
        self.bridge.toggle_horizontal.connect(self.on_toggle_horizontal_hotkey)

        self.init_ui()
        self.start_threads()

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

        # 优先尝试使用 SVG 图标，更适合系统托盘显示
        svg_icon_path = resource_path(
            os.path.join("FlowMouse", "resources", "FlowMouse.svg")
        )
        if os.path.exists(svg_icon_path):
            from PySide6.QtGui import QPixmap

            svg_icon = QIcon(svg_icon_path)
            # 确保图标有合适的尺寸用于系统托盘
            if not svg_icon.isNull():
                self.tray_icon.setIcon(svg_icon)
            else:
                # 如果 SVG 加载失败，尝试 ICO
                icon_path = resource_path(icon_name)
                if os.path.exists(icon_path):
                    self.tray_icon.setIcon(QIcon(icon_path))
                else:
                    from PySide6.QtWidgets import QStyle

                    self.tray_icon.setIcon(
                        self.style().standardIcon(QStyle.SP_MessageBoxInformation)
                    )
        else:
            # 如果没有 SVG，使用 ICO
            icon_path = resource_path(icon_name)
            if os.path.exists(icon_path):
                self.tray_icon.setIcon(QIcon(icon_path))
            else:
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
        font_family = (
            "'.AppleSystemUIFont', 'SF Pro Text', sans-serif"
            if OS_NAME == "Darwin"
            else "'Segoe UI', 'Microsoft YaHei', sans-serif"
        )
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: #0F172A; font-family: {font_family}; }}
            QScrollArea {{ border: none; background-color: transparent; }}
            QScrollArea > QWidget > QWidget {{ background-color: transparent; }}
            
            /* Custom Scrollbar for modern look */
            QScrollBar:vertical {{ border: none; background: #0F172A; width: 6px; margin: 0px; }}
            QScrollBar::handle:vertical {{ background: #334155; border-radius: 3px; min-height: 20px; }}
            QScrollBar::handle:vertical:hover {{ background: #475569; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
            
            QLabel {{ color: #F8FAFC; font-size: 14px; }}
            QLabel#HeaderTitle {{ font-size: 28px; font-weight: 800; color: #F8FAFC; letter-spacing: 0.5px; }}
            QLabel#HeaderSubtitle {{ font-size: 13px; color: #64748B; font-weight: 600; margin-top: -4px; }}
            QLabel#SectionTitle {{ font-size: 12px; font-weight: 700; color: #94A3B8; margin-top: 12px; margin-bottom: 4px; padding-left: 4px; padding-right: 12px; }}
            
            QFrame#Card {{ background-color: #1E293B; border-radius: 16px; border: 1px solid #334155; }}
            QFrame#Separator {{ background-color: #334155; max-height: 1px; }}
            
            QDoubleSpinBox {{ background-color: #0F172A; border: 1px solid #334155; border-radius: 8px; padding: 4px; color: #3B82F6; font-weight: 700; font-size: 14px; }}
            QDoubleSpinBox:focus {{ border: 1px solid #3B82F6; background-color: #0B1120; }}
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{ width: 0px; height: 0px; }}
            
            QSlider::groove:horizontal {{ border-radius: 4px; height: 8px; background: #334155; }}
            QSlider::sub-page:horizontal {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #3B82F6); border-radius: 4px; }}
            QSlider::handle:horizontal {{ background: #FFFFFF; border: 2px solid #3B82F6; width: 18px; height: 18px; margin: -5px 0; border-radius: 9px; }}
            QSlider::handle:horizontal:hover {{ background: #EFF6FF; border: 3px solid #2563EB; }}

            QCheckBox {{ color: #E2E8F0; font-size: 14px; font-weight: 600; spacing: 12px; min-height: 24px; }}
            QCheckBox::indicator {{ width: 20px; height: 20px; border-radius: 6px; border: 2px solid #475569; background-color: #0F172A; }}
            QCheckBox::indicator:hover {{ border-color: #64748B; }}
            QCheckBox::indicator:checked {{ background-color: #3B82F6; border-color: #3B82F6; }}
            
            QTabWidget::pane {{ border: none; background-color: transparent; }}
            QTabBar::tab {{ background: #0F172A; color: #94A3B8; font-weight: 700; font-size: 14px; padding: 12px 24px; border: none; border-bottom: 2px solid transparent; }}
            QTabBar::tab:hover {{ color: #E2E8F0; }}
            QTabBar::tab:selected {{ color: #3B82F6; border-bottom: 2px solid #3B82F6; }}
            
            QPushButton {{ background-color: #1E293B; border: 1px solid #334155; border-radius: 10px; padding: 8px 16px; color: #F8FAFC; font-weight: 600; font-size: 13px; }}
            QPushButton:hover {{ background-color: #334155; border-color: #475569; }}
            QPushButton:pressed {{ background-color: #0F172A; }}
            
            QPushButton#BtnPrimary {{ background-color: #3B82F6; color: #FFFFFF; border: none; padding: 10px 16px; font-size: 14px; border-radius: 10px; }}
            QPushButton#BtnPrimary:hover {{ background-color: #2563EB; }}
            QPushButton#BtnPrimary:pressed {{ background-color: #1D4ED8; }}
            
            QPushButton#BtnDanger {{ background-color: #450A0A; color: #FCA5A5; border: 1px solid #7F1D1D; border-radius: 10px; }}
            QPushButton#BtnDanger:hover {{ background-color: #7F1D1D; color: #FECACA; }}
            QPushButton#BtnDanger:pressed {{ background-color: #450A0A; }}
            
            QPushButton#BtnAdv {{ background-color: #1E293B; border: 1px solid #3B82F6; color: #60A5FA; border-radius: 10px; padding: 12px; font-weight: 700; font-size: 14px; }}
            QPushButton#BtnAdv:hover {{ background-color: #172554; border-color: #60A5FA; }}
            
            QPushButton#BtnIcon {{ background: transparent; border: none; padding: 6px; border-radius: 8px; }}
            QPushButton#BtnIcon:hover {{ background-color: #1E293B; }}
            
            QComboBox {{ background-color: #0F172A; border: 1px solid #334155; border-radius: 10px; padding: 8px 12px; color: #F8FAFC; font-weight: 600; font-size: 13px; }}
            QComboBox::drop-down {{ border: none; width: 30px; }}
            QComboBox::down-arrow {{ image: none; }}
            
            QKeySequenceEdit {{ border: 1px solid #334155; border-radius: 8px; padding: 4px 12px; background: #0F172A; color: #3B82F6; font-weight: 700; font-size: 14px; min-width: 60px; }}
            QKeySequenceEdit:focus {{ border: 1px solid #3B82F6; background: #0B1120; }}
        """)

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
            os.path.join("FlowMouse", "resources", "FlowMouse.svg")
        )
        if os.path.exists(logo_path):
            logo_pixmap = QIcon(logo_path).pixmap(QSize(56, 56))
            logo_label.setPixmap(logo_pixmap)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)

        header_title = QLabel("FlowMouse")
        header_title.setObjectName("HeaderTitle")

        header_subtitle = QLabel("全局平滑滚动引擎")
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

        # --- Helper Functions ---
        def create_card():
            card = QFrame()
            card.setObjectName("Card")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(24, 24, 24, 24)
            card_layout.setSpacing(20)
            return card, card_layout

        def create_h_line():
            line = QFrame()
            line.setObjectName("Separator")
            return line

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        # --- Helper Functions ---
        def create_card():
            card = QFrame()
            card.setObjectName("Card")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(24, 24, 24, 24)
            card_layout.setSpacing(20)
            return card, card_layout

        def create_h_line():
            line = QFrame()
            line.setObjectName("Separator")
            return line

        def add_slider_row(
            layout, key, label_text, val, min_v, max_v, callback, decimals=1
        ):
            row = QWidget()
            row_layout = QVBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(12)

            top_layout = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setStyleSheet("font-weight: 600; color: #F1F5F9; font-size: 14px;")

            spin = QDoubleSpinBox()
            spin.setRange(min_v, max_v)
            spin.setValue(val)
            spin.setDecimals(decimals)
            spin.setSingleStep(1.0 / (10**decimals))
            spin.setFixedSize(70, 32)
            spin.setAlignment(Qt.AlignCenter)
            spin.valueChanged.connect(callback)
            spin.setFocusPolicy(Qt.ClickFocus)

            top_layout.addWidget(lbl)
            top_layout.addStretch()
            top_layout.addWidget(spin)

            scale = 10**decimals
            slider = QSlider(Qt.Horizontal)
            slider.setRange(int(min_v * scale), int(max_v * scale))
            slider.setValue(int(val * scale))
            slider.setFixedHeight(24)
            slider.setCursor(Qt.PointingHandCursor)
            slider.valueChanged.connect(lambda v: spin.setValue(v / scale))
            spin.valueChanged.connect(lambda v: slider.setValue(int(v * scale)))
            slider.setFocusPolicy(Qt.NoFocus)

            row_layout.addLayout(top_layout)
            row_layout.addWidget(slider)

            layout.addWidget(row)
            self.ui_widgets[key] = spin

        def add_toggle_row(
            layout,
            key,
            label_text,
            is_checked,
            callback,
            extra_widget=None,
            style_sheet=None,
        ):
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)

            chk = QCheckBox(label_text)
            chk.setChecked(is_checked)
            chk.toggled.connect(callback)
            chk.setFocusPolicy(Qt.NoFocus)
            chk.setCursor(Qt.PointingHandCursor)
            if style_sheet:
                chk.setStyleSheet(style_sheet)
            if key:
                self.ui_widgets[key] = chk

            row_layout.addWidget(chk)
            row_layout.addStretch()
            if extra_widget:
                row_layout.addWidget(extra_widget)

            layout.addWidget(row)

        # --- Tab Widget ---
        tab_widget = QTabWidget()
        tab_widget.setTabPosition(QTabWidget.North)

        # --- Tab 1: 参数调校 ---
        tab1_widget = QWidget()
        tab1_layout = QVBoxLayout(tab1_widget)
        tab1_layout.setContentsMargins(0, 16, 0, 0)
        tab1_layout.setSpacing(20)
        tab1_layout.setAlignment(Qt.AlignTop)

        core_card, core_layout = create_card()

        add_slider_row(
            core_layout,
            "sensitivity",
            "🚀 加速度曲线 (Sensitivity)",
            cfg.sensitivity,
            1.0,
            5.0,
            lambda v: setattr(cfg, "sensitivity", v),
            decimals=1,
        )
        core_layout.addWidget(create_h_line())
        add_slider_row(
            core_layout,
            "speed_factor",
            "⚡ 基础速度倍率 (Base Speed)",
            cfg.speed_factor,
            0.01,
            10.00,
            lambda v: setattr(cfg, "speed_factor", v),
            decimals=2,
        )
        core_layout.addWidget(create_h_line())
        add_slider_row(
            core_layout,
            "dead_zone",
            "🎯 中心死区缓冲 (Dead Zone)",
            cfg.dead_zone,
            0.0,
            100.0,
            lambda v: setattr(cfg, "dead_zone", v),
            decimals=1,
        )
        core_layout.addWidget(create_h_line())
        add_slider_row(
            core_layout,
            "overlay_size",
            "🟢 导航指示器大小 (UI Size)",
            cfg.overlay_size,
            30,
            150,
            lambda v: (
                setattr(cfg, "overlay_size", v),
                self.bridge.update_size.emit(int(v)),
                self.bridge.preview_size.emit(),
            ),
            decimals=0,
        )

        tab1_layout.addWidget(core_card)

        # --- Author Info ---
        author_layout = QHBoxLayout()
        author_layout.setAlignment(Qt.AlignCenter)

        btn_github = QPushButton()
        btn_github.setCursor(Qt.PointingHandCursor)
        btn_github.setObjectName("BtnIcon")

        # Load and set GitHub SVG Icon
        gh_path = resource_path(
            os.path.join("FlowMouse", "resources", "github_icon.svg")
        )
        if os.path.exists(gh_path):
            btn_github.setIcon(QIcon(gh_path))
            btn_github.setIconSize(QSize(20, 20))

        btn_github.setText(" GitHub · 某不科学的高数")
        btn_github.clicked.connect(
            lambda: system_platform.open_url("https://github.com/CyrilPeng/FlowMouse")
        )

        author_layout.addWidget(btn_github)
        tab1_layout.addLayout(author_layout)

        # Add stretch to make content fit height
        tab1_layout.addStretch()

        tab_widget.addTab(tab1_widget, "参数调校")

        # --- Tab 2: 高级设置 ---
        tab2_widget = QWidget()
        tab2_layout = QVBoxLayout(tab2_widget)
        tab2_layout.setContentsMargins(0, 16, 0, 0)
        tab2_layout.setSpacing(20)
        tab2_layout.setAlignment(Qt.AlignTop)

        adv_card = QFrame()
        adv_card.setObjectName("Card")
        adv_layout = QVBoxLayout(adv_card)
        adv_layout.setContentsMargins(24, 24, 24, 24)
        adv_layout.setSpacing(20)

        # --- Horizontal Hotkey Row ---
        row_horizontal = QWidget()
        row_horizontal_layout = QHBoxLayout(row_horizontal)
        row_horizontal_layout.setContentsMargins(0, 0, 0, 0)
        row_horizontal_layout.setSpacing(12)

        chk_horizontal = QCheckBox("启用横向穿梭模式")
        chk_horizontal.setChecked(cfg.enable_horizontal)
        chk_horizontal.toggled.connect(lambda v: setattr(cfg, "enable_horizontal", v))
        chk_horizontal.setFocusPolicy(Qt.NoFocus)
        chk_horizontal.setCursor(Qt.PointingHandCursor)
        self.ui_widgets["enable_horizontal"] = chk_horizontal
        row_horizontal_layout.addWidget(chk_horizontal)
        row_horizontal_layout.addStretch()

        self.lbl_hotkey = QLabel()
        self.lbl_hotkey.setStyleSheet(
            "color: #94A3B8; font-size: 13px; font-weight: 600;"
        )
        self.update_hotkey_label()
        row_horizontal_layout.addWidget(self.lbl_hotkey)

        btn_gear = QPushButton("⚙️")
        btn_gear.setObjectName("BtnIcon")
        btn_gear.setCursor(Qt.PointingHandCursor)
        btn_gear.setToolTip("设置快捷键")
        btn_gear.clicked.connect(self.open_hotkey_dialog)
        row_horizontal_layout.addWidget(btn_gear)

        adv_layout.addWidget(row_horizontal)
        adv_layout.addWidget(create_h_line())
        add_toggle_row(
            adv_layout,
            "minimize_to_tray",
            "关闭后最小化到托盘",
            cfg.minimize_to_tray,
            lambda v: setattr(cfg, "minimize_to_tray", v),
        )
        adv_layout.addWidget(create_h_line())

        # Autorun (not stored in cfg, so key=None)
        add_toggle_row(
            adv_layout,
            None,
            "开机自动启动并在后台运行",
            self.autostart.is_autorun(),
            self.toggle_autorun,
        )
        adv_layout.addWidget(create_h_line())

        # Inline Advanced Rules
        add_toggle_row(
            adv_layout,
            "disable_fullscreen",
            "全屏模式下禁用",
            cfg.disable_fullscreen,
            lambda v: setattr(cfg, "disable_fullscreen", v),
            style_sheet="color: #FCA5A5;",
        )

        adv_layout.addWidget(create_h_line())

        adv_layout.addWidget(
            QLabel("<span style='font-weight: 600; color: #E2E8F0;'>工作模式</span>")
        )

        from PySide6.QtWidgets import QRadioButton, QButtonGroup

        # Radio button group for filter modes
        self.filter_button_group = QButtonGroup(self)

        # Global mode radio button
        self.radio_global = QRadioButton("全局模式")
        self.radio_global.setStyleSheet(
            "color: #E2E8F0; font-size: 14px; font-weight: 600; spacing: 12px; min-height: 24px;"
        )
        self.radio_global.setChecked(cfg.filter_mode == 0)
        self.radio_global.setCursor(Qt.PointingHandCursor)
        self.filter_button_group.addButton(self.radio_global, 0)
        adv_layout.addWidget(self.radio_global)

        # Blacklist mode radio button
        self.radio_blacklist = QRadioButton("黑名单模式")
        self.radio_blacklist.setStyleSheet(
            "color: #E2E8F0; font-size: 14px; font-weight: 600; spacing: 12px; min-height: 24px;"
        )
        self.radio_blacklist.setChecked(cfg.filter_mode == 1)
        self.radio_blacklist.setCursor(Qt.PointingHandCursor)
        self.filter_button_group.addButton(self.radio_blacklist, 1)
        adv_layout.addWidget(self.radio_blacklist)

        # Connect radio buttons
        self.filter_button_group.idClicked.connect(self.on_filter_mode_changed)

        adv_layout.addWidget(
            QLabel(
                "<span style='font-weight: 600; color: #E2E8F0;'>黑名单</span><br><span style='color: #94A3B8; font-size: 12px;'>例如输入 'potplayer' 就可以禁止在该播放器中使用，修改即时生效。<br><b>💡 提示：</b>每行输入一个，不区分大小写，可通过任务管理器查看进程名进行精准设置。</span>"
            )
        )
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText("\n".join(cfg.filter_list))
        self.text_edit.textChanged.connect(self.on_filter_list_changed)
        self.text_edit.setMaximumHeight(80)
        self.text_edit.setEnabled(cfg.filter_mode != 0)
        adv_layout.addWidget(self.text_edit)

        tab2_layout.addWidget(adv_card)

        # Section: 预设管理 (Presets)
        lbl_preset = QLabel("配置预设 Presets")
        lbl_preset.setObjectName("SectionTitle")
        tab2_layout.addWidget(lbl_preset)

        preset_card, preset_layout_card = create_card()

        preset_row = QHBoxLayout()
        preset_row.setSpacing(12)

        self.combo_presets = QComboBox()
        self.combo_presets.addItems(list(self.presets.keys()))
        self.combo_presets.setCurrentText(self.current_preset_name)
        self.combo_presets.currentTextChanged.connect(self.load_selected_preset)
        self.combo_presets.setFocusPolicy(Qt.NoFocus)
        self.combo_presets.setCursor(Qt.PointingHandCursor)
        self.combo_presets.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.combo_presets.setFixedHeight(38)
        preset_row.addWidget(self.combo_presets, 1)

        btn_save = QPushButton("保存为新预设")
        btn_save.setObjectName("BtnPrimary")
        btn_save.setFocusPolicy(Qt.NoFocus)
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.clicked.connect(self.save_new_preset)
        preset_row.addWidget(btn_save)

        btn_del = QPushButton("删除")
        btn_del.setObjectName("BtnDanger")
        btn_del.setFocusPolicy(Qt.NoFocus)
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.clicked.connect(self.delete_preset)
        preset_row.addWidget(btn_del)

        preset_layout_card.addLayout(preset_row)

        preset_layout_card.addWidget(create_h_line())
        btn_webdav = QPushButton("☁️ WebDAV 云同步配置")
        btn_webdav.setObjectName("BtnAdv")
        btn_webdav.setCursor(Qt.PointingHandCursor)
        btn_webdav.clicked.connect(self.open_webdav_settings)
        preset_layout_card.addWidget(btn_webdav)

        tab2_layout.addWidget(preset_card)

        # Add stretch to make content fit height
        tab2_layout.addStretch()

        tab_widget.addTab(tab2_widget, "高级设置")

        # Add tab widget to content layout (replacing the old sections)
        content_layout.addWidget(tab_widget)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

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

        help_text = (
            "<b>🚀 加速度曲线</b><br>"
            "决定了滑动距离与最终滚动速度之间的非线性关系。数值越大，用力滑动时页面飞出得越远。网页浏览推荐 1.0~1.5，长代码/文档推荐 2.0+。<br><br>"
            "<b>⚡ 基础速度倍率</b><br>"
            "全局滚动的乘数放大器。如果你觉得整体滚动太慢或太快，调整此项。<br><br>"
            "<b>🎯 中心死区缓冲</b><br>"
            "按下中键后，鼠标需要移动多少像素才会触发滚动。建议保留极小值以防止误触和手抖。<br><br>"
            "<b>🔄 横向穿梭模式</b><br>"
            "这与 Windows 原生的中键死板滚动完全不同。FlowMouse 提供的是<b>带有物理阻尼感、像触控板一样丝滑的 360° 全向滚动</b>。开启后，按下中键不仅能上下滑动，向左/向右移动鼠标也能让页面左右平滑滚动。<br>"
            "💡 <i>建议使用方式：</i>在输入框设置一个快捷键（如 <code>Shift</code>），平时默认关闭横向滚动以保证垂直阅读的纯净度。需要看宽表格或视频时间轴时，只要按下 <code>Shift</code> 即可瞬间切换为横向模式，松开则恢复，非常适合工作流！<br><br>"
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
            state_str = "已开启 🟢" if new_state else "已关闭 🔴"
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
