from functools import lru_cache
from FlowScroll.platform import OS_NAME


@lru_cache(maxsize=1)
def _get_font_family() -> str:
    """获取平台特定的字体族。结果在整个程序生命周期内不变。"""
    if OS_NAME == "Darwin":
        return "'.AppleSystemUIFont', 'SF Pro Text', sans-serif"
    return "'Segoe UI', 'Microsoft YaHei', sans-serif"


# ==========================================
# 通用颜色常量
# ==========================================

COLOR_BG_DARK = "#0F172A"
COLOR_BG_CARD = "#1E293B"
COLOR_BG_INPUT = "#0B1120"
COLOR_BORDER = "#334155"
COLOR_BORDER_HOVER = "#475569"
COLOR_TEXT_PRIMARY = "#F8FAFC"
COLOR_TEXT_SECONDARY = "#E2E8F0"
COLOR_TEXT_MUTED = "#94A3B8"
COLOR_TEXT_HINT = "#64748B"
COLOR_TEXT_LIGHT = "#CBD5E1"
COLOR_ACCENT = "#3B82F6"
COLOR_ACCENT_HOVER = "#2563EB"
COLOR_ACCENT_PRESSED = "#1D4ED8"
COLOR_ACCENT_LIGHT = "#60A5FA"
COLOR_DANGER = "#EF4444"
COLOR_DANGER_HOVER = "#DC2626"
COLOR_DANGER_BG = "#450A0A"
COLOR_DANGER_BORDER = "#7F1D1D"
COLOR_DANGER_TEXT = "#FCA5A5"
COLOR_WARNING = "#F59E0B"
COLOR_WARNING_TEXT = "#FDE68A"
COLOR_SUCCESS = "#059669"
COLOR_SUCCESS_HOVER = "#047857"

# 警示横幅用的半透明背景色（rgba 无法用 hex 常量表达，保留为字符串）
WARNING_BANNER_BG = "rgba(120, 53, 15, 0.28)"
WARNING_BANNER_BORDER = "rgba(251, 191, 36, 0.35)"
ERROR_BANNER_BG = "rgba(127, 29, 29, 0.28)"
ERROR_BANNER_BORDER = "rgba(252, 165, 165, 0.35)"


@lru_cache(maxsize=1)
def get_main_stylesheet() -> str:
    """获取主窗口样式表。缓存以避免重复生成。"""
    font_family = _get_font_family()
    return f"""
        QMainWindow {{ background-color: {COLOR_BG_DARK}; font-family: {font_family}; }}
        QScrollArea {{ border: none; background-color: transparent; }}
        QScrollArea > QWidget > QWidget {{ background-color: transparent; }}

        /* Custom Scrollbar for modern look */
        QScrollBar:vertical {{ border: none; background: {COLOR_BG_DARK}; width: 6px; margin: 0px; }}
        QScrollBar::handle:vertical {{ background: {COLOR_BORDER}; border-radius: 3px; min-height: 20px; }}
        QScrollBar::handle:vertical:hover {{ background: {COLOR_BORDER_HOVER}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}

        QLabel {{ color: {COLOR_TEXT_PRIMARY}; font-size: 14px; }}
        QLabel#HeaderTitle {{ font-size: 28px; font-weight: 700; color: {COLOR_TEXT_PRIMARY}; letter-spacing: 0.5px; }}
        QLabel#HeaderSubtitle {{ font-size: 13px; color: {COLOR_TEXT_HINT}; font-weight: 600; margin-top: -4px; }}
        QLabel#SectionTitle {{ font-size: 11px; font-weight: 600; color: {COLOR_TEXT_MUTED}; letter-spacing: 1px; margin-top: 12px; margin-bottom: 4px; padding-left: 4px; padding-right: 12px; }}

        QFrame#Card {{ background-color: {COLOR_BG_CARD}; border-radius: 16px; border: 1px solid {COLOR_BORDER}; }}
        QFrame#Card:hover {{ border: 1px solid {COLOR_BORDER_HOVER}; background-color: #233046; }}
        QFrame#Separator {{ background-color: {COLOR_BORDER}; max-height: 1px; }}

        QDoubleSpinBox {{ background-color: {COLOR_BG_DARK}; border: 1px solid {COLOR_BORDER}; border-radius: 8px; padding: 4px; color: {COLOR_ACCENT_LIGHT}; font-weight: 600; font-size: 13px; }}
        QDoubleSpinBox:focus {{ border: 1px solid {COLOR_ACCENT}; background-color: {COLOR_BG_INPUT}; }}
        QDoubleSpinBox:disabled {{ color: {COLOR_TEXT_HINT}; border-color: {COLOR_BORDER}; }}
        QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{ width: 0px; height: 0px; }}

        QSlider::groove:horizontal {{ border-radius: 4px; height: 8px; background: {COLOR_BORDER}; }}
        QSlider::sub-page:horizontal {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLOR_ACCENT_HOVER}, stop:1 {COLOR_ACCENT}); border-radius: 4px; }}
        QSlider::handle:horizontal {{ background: #FFFFFF; border: 2px solid {COLOR_ACCENT}; width: 18px; height: 18px; margin: -5px 0; border-radius: 9px; }}
        QSlider::handle:horizontal:hover {{ background: #EFF6FF; border: 3px solid {COLOR_ACCENT_HOVER}; width: 20px; height: 20px; margin: -6px 0; border-radius: 10px; }}
        QSlider::handle:horizontal:pressed {{ background: {COLOR_ACCENT}; border: 2px solid #FFFFFF; width: 16px; height: 16px; margin: -4px 0; border-radius: 8px; }}
        QSlider:disabled {{ opacity: 0.5; }}

        QCheckBox {{ color: {COLOR_TEXT_SECONDARY}; font-size: 14px; font-weight: 600; spacing: 12px; min-height: 24px; }}
        QCheckBox::indicator {{ width: 20px; height: 20px; border-radius: 6px; border: 2px solid {COLOR_BORDER_HOVER}; background-color: {COLOR_BG_DARK}; }}
        QCheckBox::indicator:hover {{ border-color: #64748B; }}
        QCheckBox::indicator:checked {{ background-color: {COLOR_ACCENT}; border-color: {COLOR_ACCENT}; }}
        QCheckBox:disabled {{ color: {COLOR_TEXT_HINT}; }}
        QCheckBox::indicator:disabled {{ border-color: {COLOR_BORDER}; background-color: {COLOR_BG_INPUT}; }}

        QTabWidget::pane {{ border: none; background-color: transparent; }}
        QTabBar {{ background: transparent; }}
        QTabBar::tab {{ background: transparent; color: {COLOR_TEXT_MUTED}; font-weight: 600; font-size: 14px; padding: 10px 20px; border: none; border-radius: 8px; margin: 2px 4px; }}
        QTabBar::tab:hover {{ color: {COLOR_TEXT_SECONDARY}; background-color: rgba(59, 130, 246, 0.08); }}
        QTabBar::tab:selected {{ color: {COLOR_ACCENT}; background-color: rgba(59, 130, 246, 0.12); }}

        QPushButton {{ background-color: {COLOR_BG_CARD}; border: 1px solid {COLOR_BORDER}; border-radius: 10px; padding: 8px 16px; color: {COLOR_TEXT_PRIMARY}; font-weight: 600; font-size: 13px; }}
        QPushButton:hover {{ background-color: {COLOR_BORDER}; border-color: {COLOR_BORDER_HOVER}; }}
        QPushButton:pressed {{ background-color: {COLOR_BG_DARK}; }}
        QPushButton:disabled {{ background-color: {COLOR_BG_INPUT}; color: {COLOR_TEXT_HINT}; border-color: {COLOR_BORDER}; }}

        QPushButton#BtnPrimary {{ background-color: {COLOR_ACCENT}; color: #FFFFFF; border: none; padding: 10px 16px; font-size: 14px; border-radius: 10px; }}
        QPushButton#BtnPrimary:hover {{ background-color: {COLOR_ACCENT_HOVER}; }}
        QPushButton#BtnPrimary:pressed {{ background-color: {COLOR_ACCENT_PRESSED}; }}
        QPushButton#BtnPrimary:disabled {{ background-color: #1E3A5F; color: #64748B; }}

        QPushButton#BtnDanger {{ background-color: {COLOR_DANGER_BG}; color: {COLOR_DANGER_TEXT}; border: 1px solid {COLOR_DANGER_BORDER}; border-radius: 10px; }}
        QPushButton#BtnDanger:hover {{ background-color: {COLOR_DANGER_BORDER}; color: #FECACA; }}
        QPushButton#BtnDanger:pressed {{ background-color: {COLOR_DANGER_BG}; }}
        QPushButton#BtnDanger:disabled {{ background-color: {COLOR_BG_INPUT}; color: {COLOR_TEXT_HINT}; border-color: {COLOR_BORDER}; }}

        QPushButton#BtnAdv {{ background-color: {COLOR_BG_CARD}; border: 1px solid {COLOR_ACCENT}; color: {COLOR_ACCENT_LIGHT}; border-radius: 10px; padding: 10px 12px; font-weight: 600; font-size: 14px; text-align: center; min-height: 40px; }}
        QPushButton#BtnAdv:hover {{ background-color: #172554; border-color: {COLOR_ACCENT_LIGHT}; }}
        QPushButton#BtnAdv:pressed {{ background-color: #0C1A33; }}
        QPushButton#BtnAdv:disabled {{ background-color: {COLOR_BG_INPUT}; color: {COLOR_TEXT_HINT}; border-color: {COLOR_BORDER}; }}

        QPushButton#BtnAdvSecondary {{ background-color: {COLOR_BG_CARD}; border: 1px solid {COLOR_BORDER}; color: {COLOR_TEXT_SECONDARY}; border-radius: 10px; padding: 10px 12px; font-weight: 600; font-size: 14px; text-align: center; min-height: 40px; }}
        QPushButton#BtnAdvSecondary:hover {{ background-color: {COLOR_BORDER}; border-color: {COLOR_BORDER_HOVER}; color: {COLOR_TEXT_PRIMARY}; }}
        QPushButton#BtnAdvSecondary:pressed {{ background-color: {COLOR_BG_DARK}; }}
        QPushButton#BtnAdvSecondary:disabled {{ background-color: {COLOR_BG_INPUT}; color: {COLOR_TEXT_HINT}; border-color: {COLOR_BORDER}; }}

        QPushButton#BtnIcon {{ background: transparent; border: none; padding: 6px; border-radius: 8px; }}
        QPushButton#BtnIcon:hover {{ background-color: {COLOR_BG_CARD}; }}

        QComboBox {{ background-color: {COLOR_BG_DARK}; border: 1px solid {COLOR_BORDER}; border-radius: 10px; padding: 8px 12px; color: {COLOR_TEXT_PRIMARY}; font-weight: 600; font-size: 13px; }}
        QComboBox:hover {{ border-color: {COLOR_BORDER_HOVER}; }}
        QComboBox:focus {{ border-color: {COLOR_ACCENT}; background-color: {COLOR_BG_INPUT}; }}
        QComboBox:disabled {{ color: {COLOR_TEXT_HINT}; border-color: {COLOR_BORDER}; }}
        QComboBox::drop-down {{ border: none; width: 30px; }}
        QComboBox::down-arrow {{ image: none; }}
        QComboBox QAbstractItemView {{ background-color: {COLOR_BG_CARD}; border: 1px solid {COLOR_BORDER}; border-radius: 8px; padding: 4px; color: {COLOR_TEXT_PRIMARY}; selection-background-color: {COLOR_ACCENT}; selection-color: #FFFFFF; outline: none; }}
        QComboBox QAbstractItemView::item {{ min-height: 30px; padding: 6px 12px; border-radius: 4px; }}
        QComboBox QAbstractItemView::item:hover {{ background-color: {COLOR_BORDER}; }}

        QKeySequenceEdit {{ border: 1px solid {COLOR_BORDER}; border-radius: 8px; padding: 4px 12px; background: {COLOR_BG_DARK}; color: {COLOR_ACCENT}; font-weight: 700; font-size: 14px; min-width: 60px; }}
        QKeySequenceEdit:focus {{ border: 1px solid {COLOR_ACCENT}; background: {COLOR_BG_INPUT}; }}
        QKeySequenceEdit:disabled {{ color: {COLOR_TEXT_HINT}; border-color: {COLOR_BORDER}; }}
    """


@lru_cache(maxsize=1)
def get_dialog_stylesheet() -> str:
    """获取通用对话框样式表。缓存以避免重复生成。"""
    font_family = _get_font_family()
    return f"""
        QDialog {{ background-color: {COLOR_BG_DARK}; font-family: {font_family}; }}
        QLabel {{ font-size: 14px; color: {COLOR_TEXT_SECONDARY}; }}
        QPushButton {{
            background-color: {COLOR_BG_CARD};
            border: 1px solid {COLOR_BORDER};
            border-radius: 8px;
            padding: 8px 16px;
            color: {COLOR_TEXT_PRIMARY};
            font-weight: 600;
            font-size: 14px;
        }}
        QPushButton:hover {{ background-color: {COLOR_BORDER}; border-color: {COLOR_BORDER_HOVER}; }}
        QPushButton:pressed {{ background-color: {COLOR_BG_DARK}; }}
        QPushButton:disabled {{ background-color: {COLOR_BG_INPUT}; color: {COLOR_TEXT_HINT}; border-color: {COLOR_BORDER}; }}
        QPushButton#BtnSmall {{
            background-color: {COLOR_BG_DARK};
            border: 1px solid {COLOR_BORDER_HOVER};
            border-radius: 8px;
            padding: 6px 12px;
            color: {COLOR_TEXT_SECONDARY};
            font-size: 12px;
            font-weight: 600;
            min-height: 34px;
        }}
        QPushButton#BtnSmall:hover {{ background-color: {COLOR_BORDER}; border-color: #64748B; color: {COLOR_TEXT_PRIMARY}; }}
        QPushButton#BtnSmall:pressed {{ background-color: {COLOR_BG_DARK}; }}
        QPushButton#BtnPrimary {{ background-color: {COLOR_ACCENT}; color: #FFFFFF; border: none; padding: 10px 24px; font-size: 14px; border-radius: 10px; }}
        QPushButton#BtnPrimary:hover {{ background-color: {COLOR_ACCENT_HOVER}; }}
        QPushButton#BtnPrimary:pressed {{ background-color: {COLOR_ACCENT_PRESSED}; }}
        QPushButton#BtnPrimary:disabled {{ background-color: #1E3A5F; color: #64748B; }}
        QFrame#Card {{ background-color: {COLOR_BG_CARD}; border-radius: 16px; border: 1px solid {COLOR_BORDER}; }}
        QFrame#Card:hover {{ border: 1px solid {COLOR_BORDER_HOVER}; background-color: #233046; }}
        QFrame#Separator {{ background-color: {COLOR_BORDER}; max-height: 1px; }}
    """


@lru_cache(maxsize=1)
def get_checkbox_style() -> str:
    """获取复选框样式。缓存以避免重复生成。"""
    return f"""
        QCheckBox {{ color: {COLOR_TEXT_SECONDARY}; font-size: 14px; font-weight: 600; spacing: 12px; min-height: 24px; }}
        QCheckBox::indicator {{ width: 20px; height: 20px; border-radius: 6px; border: 2px solid {COLOR_BORDER_HOVER}; background-color: {COLOR_BG_DARK}; }}
        QCheckBox::indicator:hover {{ border-color: #64748B; }}
        QCheckBox::indicator:checked {{ background-color: {COLOR_ACCENT}; border-color: {COLOR_ACCENT}; }}
        QCheckBox:disabled {{ color: {COLOR_TEXT_HINT}; }}
        QCheckBox::indicator:disabled {{ border-color: {COLOR_BORDER}; background-color: {COLOR_BG_INPUT}; }}
    """


@lru_cache(maxsize=1)
def get_radiobutton_style() -> str:
    """获取单选按钮样式。缓存以避免重复生成。"""
    return f"""
        QRadioButton {{ color: {COLOR_TEXT_SECONDARY}; font-size: 14px; font-weight: 600; spacing: 12px; min-height: 24px; }}
    """


@lru_cache(maxsize=1)
def get_textedit_style() -> str:
    """获取文本编辑框样式。缓存以避免重复生成。"""
    return f"""
        QTextEdit {{ border: 1px solid {COLOR_BORDER}; border-radius: 8px; padding: 10px; background: {COLOR_BG_CARD}; font-size: 14px; color: {COLOR_TEXT_PRIMARY}; }}
        QTextEdit:focus {{ border: 1px solid {COLOR_ACCENT}; }}
    """


@lru_cache(maxsize=1)
def get_lineedit_style() -> str:
    """获取行编辑框样式。缓存以避免重复生成。"""
    return f"""
        QLineEdit {{
            border: 1px solid {COLOR_BORDER};
            border-radius: 8px;
            padding: 8px 12px;
            background: {COLOR_BG_CARD};
            font-size: 13px;
            color: {COLOR_TEXT_PRIMARY};
        }}
        QLineEdit:focus {{ border: 1px solid {COLOR_ACCENT}; background: {COLOR_BG_INPUT}; }}
    """


@lru_cache(maxsize=1)
def get_slider_style() -> str:
    """获取滑块样式。缓存以避免重复生成。"""
    return f"""
        QSlider::groove:horizontal {{ border-radius: 4px; height: 8px; background: {COLOR_BORDER}; }}
        QSlider::sub-page:horizontal {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLOR_ACCENT_HOVER}, stop:1 {COLOR_ACCENT}); border-radius: 4px; }}
        QSlider::handle:horizontal {{ background: #FFFFFF; border: 2px solid {COLOR_ACCENT}; width: 18px; height: 18px; margin: -5px 0; border-radius: 9px; }}
        QSlider::handle:horizontal:hover {{ background: #EFF6FF; border: 3px solid {COLOR_ACCENT_HOVER}; width: 20px; height: 20px; margin: -6px 0; border-radius: 10px; }}
        QSlider::handle:horizontal:pressed {{ background: {COLOR_ACCENT}; border: 2px solid #FFFFFF; width: 16px; height: 16px; margin: -4px 0; border-radius: 8px; }}
        QSlider:disabled {{ opacity: 0.5; }}
    """


@lru_cache(maxsize=1)
def get_webdav_dialog_style() -> str:
    """获取 WebDAV 对话框样式。缓存以避免重复生成。"""
    return (
        get_dialog_stylesheet()
        + get_lineedit_style()
        + f"""
        /* Avoid vertical clipping for CJK labels in WebDAV dialog buttons */
        QPushButton {{ min-height: 36px; padding-top: 8px; padding-bottom: 8px; }}
        QPushButton#BtnSuccess {{ background-color: {COLOR_SUCCESS}; color: #FFFFFF; border: none; }}
        QPushButton#BtnSuccess:hover {{ background-color: {COLOR_SUCCESS_HOVER}; }}
        QPushButton#BtnSuccess:pressed {{ background-color: #065F46; }}
        QPushButton#BtnSuccess:disabled {{ background-color: #1E3A5F; color: #64748B; }}
    """
    )


@lru_cache(maxsize=1)
def get_help_dialog_style() -> str:
    """获取帮助对话框样式。缓存以避免重复生成。"""
    font_family = _get_font_family()
    return f"""
        QMessageBox {{ background-color: {COLOR_BG_DARK}; font-family: {font_family}; }}
        QLabel {{ color: {COLOR_TEXT_PRIMARY}; font-size: 14px; font-family: {font_family}; }}
        QPushButton {{ background-color: {COLOR_ACCENT}; color: white; border-radius: 6px; padding: 6px 16px; font-weight: bold; }}
        QPushButton:hover {{ background-color: {COLOR_ACCENT_HOVER}; }}
    """


@lru_cache(maxsize=1)
def get_value_label_style() -> str:
    """获取数值标签样式（用于滑块旁的数值显示）。缓存以避免重复生成。"""
    return f"color: {COLOR_ACCENT}; font-weight: 700; font-size: 13px;"


@lru_cache(maxsize=1)
def get_hint_label_style() -> str:
    """获取提示标签样式（用于滑块两端的标签）。缓存以避免重复生成。"""
    return f"color: {COLOR_TEXT_MUTED}; font-size: 12px;"


@lru_cache(maxsize=1)
def get_section_label_style() -> str:
    """获取节标题标签样式。缓存以避免重复生成。"""
    return f"font-weight: 600; color: {COLOR_TEXT_PRIMARY}; font-size: 14px;"


@lru_cache(maxsize=1)
def get_hotkey_label_style() -> str:
    """获取快捷键标签样式。缓存以避免重复生成。"""
    return f"color: {COLOR_TEXT_MUTED}; font-size: 13px; font-weight: 600;"


@lru_cache(maxsize=1)
def get_new_badge_style() -> str:
    """获取 NEW 徽章样式。缓存以避免重复生成。"""
    return """
        QPushButton { background-color: #EF4444; color: white; font-size: 10px;
            font-weight: 800; padding: 2px 6px; border-radius: 8px; border: none; }
        QPushButton:hover { background-color: #DC2626; }
    """


@lru_cache(maxsize=1)
def get_help_button_style() -> str:
    """获取帮助按钮样式。缓存以避免重复生成。"""
    return f"""
        QPushButton {{
            font-size: 16px;
            font-weight: 800;
            color: #CBD5E1;
            background-color: {COLOR_BG_CARD};
            border: 1px solid {COLOR_BORDER_HOVER};
            border-radius: 12px;
            min-width: 24px;
            min-height: 24px;
            padding: 4px;
        }}
        QPushButton:hover {{ background-color: {COLOR_BORDER}; border-color: #64748B; color: {COLOR_TEXT_PRIMARY}; }}
    """


# ==========================================
# 语义化组件样式函数
# 用于对话框和标签页构建，消除裸字符串硬编码
# ==========================================


@lru_cache(maxsize=1)
def get_dialog_title_style() -> str:
    """对话框标题样式（如"滚动行为"、"应用过滤"等）。缓存以避免重复生成。"""
    return f"font-size: 17px; font-weight: 700; color: {COLOR_TEXT_PRIMARY};"


@lru_cache(maxsize=1)
def get_dialog_subtitle_style() -> str:
    """对话框副标题样式（标题下方的说明文字）。缓存以避免重复生成。"""
    return f"color: {COLOR_TEXT_MUTED}; font-size: 13px;"


@lru_cache(maxsize=1)
def get_card_title_style() -> str:
    """卡片内的小标题样式（如"摩擦力"、"触发阈值"等）。缓存以避免重复生成。"""
    return f"font-size: 15px; font-weight: 700; color: {COLOR_TEXT_SECONDARY};"


@lru_cache(maxsize=1)
def get_description_style() -> str:
    """描述性文本样式（用于选项说明、选项解释等次要文字）。缓存以避免重复生成。"""
    return f"color: {COLOR_TEXT_MUTED}; font-size: 12px;"


@lru_cache(maxsize=1)
def get_column_header_style() -> str:
    """列标题样式（如黑名单/白名单标题、强调标签）。缓存以避免重复生成。"""
    return f"color: {COLOR_TEXT_SECONDARY}; font-weight: 600;"


@lru_cache(maxsize=1)
def get_hint_block_style() -> str:
    """带行高的多行提示文本样式（如配置路径对话框中的说明）。缓存以避免重复生成。"""
    return f"color: {COLOR_TEXT_LIGHT}; font-size: 13px; line-height: 1.5;"


@lru_cache(maxsize=1)
def get_warning_banner_style() -> str:
    """黄色警示横幅样式（用于进程名不可用、环境变量锁定等软性警告）。缓存以避免重复生成。"""
    return (
        f"color: {COLOR_WARNING_TEXT}; background: {WARNING_BANNER_BG}; "
        f"border: 1px solid {WARNING_BANNER_BORDER}; border-radius: 10px; "
        f"padding: 10px 12px; line-height: 1.4;"
    )


@lru_cache(maxsize=1)
def get_error_banner_style() -> str:
    """红色错误横幅样式（用于严重问题，如输入钩子不可用）。缓存以避免重复生成。"""
    return (
        f"color: {COLOR_DANGER_TEXT}; background: {ERROR_BANNER_BG}; "
        f"border: 1px solid {ERROR_BANNER_BORDER}; border-radius: 10px; "
        f"padding: 10px 12px;"
    )


@lru_cache(maxsize=1)
def get_card_label_style() -> str:
    """卡片内通用标签文本样式（用于卡片中默认浅色文本）。缓存以避免重复生成。"""
    return f"color: {COLOR_TEXT_SECONDARY};"


@lru_cache(maxsize=1)
def get_small_warning_style() -> str:
    """小字号警示文本样式（如 keyring 不可用等轻量提示）。缓存以避免重复生成。"""
    return f"color: {COLOR_WARNING}; font-size: 11px;"
