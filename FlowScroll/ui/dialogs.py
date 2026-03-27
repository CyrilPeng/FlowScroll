from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QCheckBox,
    QRadioButton,
    QButtonGroup,
    QTextEdit,
    QPushButton,
    QSlider,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt
from FlowScroll.core.config import cfg
from FlowScroll.ui.components import HotkeyEdit
from FlowScroll.ui.helpers import create_card, create_h_line
from FlowScroll.ui.styles import (
    get_dialog_stylesheet,
    get_checkbox_style,
    get_radiobutton_style,
    get_textedit_style,
    get_slider_style,
    get_value_label_style,
    get_hint_label_style,
)
from FlowScroll.constants import (
    REVERSE_DIALOG_WIDTH,
    REVERSE_DIALOG_HEIGHT,
    WORK_MODE_DIALOG_WIDTH,
    WORK_MODE_DIALOG_HEIGHT,
    INERTIA_DIALOG_WIDTH,
    INERTIA_DIALOG_HEIGHT,
)


class ReverseModeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("反转模式")
        self.setMinimumSize(REVERSE_DIALOG_WIDTH, REVERSE_DIALOG_HEIGHT)
        self.setSizeGripEnabled(True)

        self.setStyleSheet(get_dialog_stylesheet() + get_checkbox_style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        card, card_layout = create_card()

        hint_lbl = QLabel(
            "<span style='font-weight: 600; color: #E2E8F0;'>滚轮方向</span>"
            "<br><span style='color: #94A3B8; font-size: 12px;'>"
            "部分习惯反转操作的用户（向上拨动滚轮 = 页面向下）可以在此调整。</span>"
        )
        hint_lbl.setWordWrap(True)
        card_layout.addWidget(hint_lbl)

        card_layout.addWidget(create_h_line())

        self.chk_reverse_y = QCheckBox("反转纵向滚动 (Y轴)")
        self.chk_reverse_y.setChecked(cfg.reverse_y)
        self.chk_reverse_y.setCursor(Qt.PointingHandCursor)
        card_layout.addWidget(self.chk_reverse_y)

        self.chk_reverse_x = QCheckBox("反转横向滚动 (X轴)")
        self.chk_reverse_x.setChecked(cfg.reverse_x)
        self.chk_reverse_x.setCursor(Qt.PointingHandCursor)
        card_layout.addWidget(self.chk_reverse_x)

        layout.addWidget(card)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_save = QPushButton("确定")
        btn_save.setObjectName("BtnPrimary")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.clicked.connect(self.save_and_close)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

        adaptive_height = max(REVERSE_DIALOG_HEIGHT, self.sizeHint().height())
        self.resize(REVERSE_DIALOG_WIDTH, adaptive_height)

    def save_and_close(self):
        cfg.reverse_y = self.chk_reverse_y.isChecked()
        cfg.reverse_x = self.chk_reverse_x.isChecked()
        self.accept()


class WorkModeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("工作模式")
        self.setMinimumSize(WORK_MODE_DIALOG_WIDTH, WORK_MODE_DIALOG_HEIGHT)
        self.setSizeGripEnabled(True)

        self.setStyleSheet(
            get_dialog_stylesheet() + get_radiobutton_style() + get_textedit_style()
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # --- 启用模式 ---
        card, card_layout = create_card()
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(8)

        card_layout.addWidget(
            QLabel("<span style='font-weight: 600; color: #E2E8F0;'>启用模式</span>")
        )

        self.activation_group = QButtonGroup(self)

        self.radio_click_toggle = QRadioButton("点击启用键启用/关闭")
        self.radio_click_toggle.setCursor(Qt.PointingHandCursor)
        self.activation_group.addButton(self.radio_click_toggle, 0)
        card_layout.addWidget(self.radio_click_toggle)

        desc_click = QLabel(
            "<span style='color: #94A3B8; font-size: 12px;'>"
            "点击后启用，再次点击自动关闭功能。留空时默认使用鼠标中键。</span>"
        )
        desc_click.setWordWrap(True)
        desc_click.setContentsMargins(24, 0, 0, 0)
        card_layout.addWidget(desc_click)
        card_layout.addLayout(
            self._create_hotkey_row("click", cfg.activation_hotkey_click)
        )

        self.radio_hold = QRadioButton("长按启用键时启用")
        self.radio_hold.setCursor(Qt.PointingHandCursor)
        self.activation_group.addButton(self.radio_hold, 1)
        card_layout.addWidget(self.radio_hold)

        desc_hold = QLabel(
            "<span style='color: #94A3B8; font-size: 12px;'>"
            "长按时启用，松开时自动关闭功能。留空时默认使用鼠标中键。</span>"
        )
        desc_hold.setWordWrap(True)
        desc_hold.setContentsMargins(24, 0, 0, 0)
        card_layout.addWidget(desc_hold)
        card_layout.addLayout(
            self._create_hotkey_row("hold", cfg.activation_hotkey_hold)
        )

        self.radio_click_toggle.setChecked(cfg.activation_mode == 0)
        self.radio_hold.setChecked(cfg.activation_mode == 1)

        layout.addWidget(card)

        # --- 应用过滤模式 ---
        card2, card_layout2 = create_card()
        card_layout2.setContentsMargins(16, 16, 16, 16)
        card_layout2.setSpacing(8)

        card_layout2.addWidget(
            QLabel(
                "<span style='font-weight: 600; color: #E2E8F0;'>应用过滤模式</span>"
            )
        )

        self.button_group = QButtonGroup(self)

        self.radio_global = QRadioButton("全局模式")
        self.radio_global.setCursor(Qt.PointingHandCursor)
        self.button_group.addButton(self.radio_global, 0)
        card_layout2.addWidget(self.radio_global)

        desc_global = QLabel(
            "<span style='color: #94A3B8; font-size: 12px;'>"
            "此模式下，滚动功能将在所有应用中启用。"
            "如果设置了全屏模式禁用，则全屏模式下不会启用。</span>"
        )
        desc_global.setWordWrap(True)
        desc_global.setContentsMargins(24, 0, 0, 0)
        card_layout2.addWidget(desc_global)

        self.radio_blacklist = QRadioButton("黑名单模式")
        self.radio_blacklist.setCursor(Qt.PointingHandCursor)
        self.button_group.addButton(self.radio_blacklist, 1)

        row_black_mode = QHBoxLayout()
        row_black_mode.addWidget(self.radio_blacklist)
        row_black_mode.addStretch()
        self.btn_import_black = QPushButton("导入")
        self.btn_import_black.setCursor(Qt.PointingHandCursor)
        self.btn_import_black.setObjectName("BtnSmall")
        self.btn_import_black.clicked.connect(
            lambda: self._import_keywords_to(self.text_edit_blacklist)
        )
        row_black_mode.addWidget(self.btn_import_black)
        self.btn_clear_black = QPushButton("清空")
        self.btn_clear_black.setCursor(Qt.PointingHandCursor)
        self.btn_clear_black.setObjectName("BtnSmall")
        self.btn_clear_black.clicked.connect(
            lambda: self._clear_keywords(self.text_edit_blacklist, "黑名单")
        )
        row_black_mode.addWidget(self.btn_clear_black)
        card_layout2.addLayout(row_black_mode)

        desc_blacklist = QLabel(
            "<span style='color: #94A3B8; font-size: 12px;'>"
            "每行输入一个应用名称关键词，不区分大小写。<br>"
            "黑名单模式下可以禁止在指定应用中使用滚动功能，例如输入 <b>potplayer</b> 即可在该播放器中禁用滚动。</span>"
        )
        desc_blacklist.setWordWrap(True)
        desc_blacklist.setContentsMargins(24, 0, 0, 0)
        card_layout2.addWidget(desc_blacklist)

        self.radio_whitelist = QRadioButton("白名单模式")
        self.radio_whitelist.setCursor(Qt.PointingHandCursor)
        self.button_group.addButton(self.radio_whitelist, 2)

        row_white_mode = QHBoxLayout()
        row_white_mode.addWidget(self.radio_whitelist)
        row_white_mode.addStretch()
        self.btn_import_white = QPushButton("导入")
        self.btn_import_white.setCursor(Qt.PointingHandCursor)
        self.btn_import_white.setObjectName("BtnSmall")
        self.btn_import_white.clicked.connect(
            lambda: self._import_keywords_to(self.text_edit_whitelist)
        )
        row_white_mode.addWidget(self.btn_import_white)
        self.btn_clear_white = QPushButton("清空")
        self.btn_clear_white.setCursor(Qt.PointingHandCursor)
        self.btn_clear_white.setObjectName("BtnSmall")
        self.btn_clear_white.clicked.connect(
            lambda: self._clear_keywords(self.text_edit_whitelist, "白名单")
        )
        row_white_mode.addWidget(self.btn_clear_white)
        card_layout2.addLayout(row_white_mode)

        desc_whitelist = QLabel(
            "<span style='color: #94A3B8; font-size: 12px;'>"
            "每行输入一个应用名称关键词，不区分大小写。<br>"
            "白名单模式下仅在指定应用中启用滚动功能，例如输入 <b>chrome</b> "
            "即可只在浏览器中启用。</span>"
        )
        desc_whitelist.setWordWrap(True)
        desc_whitelist.setContentsMargins(24, 0, 0, 0)
        card_layout2.addWidget(desc_whitelist)

        self.radio_global.setChecked(cfg.filter_mode == 0)
        self.radio_blacklist.setChecked(cfg.filter_mode == 1)
        self.radio_whitelist.setChecked(cfg.filter_mode == 2)

        card_layout2.addWidget(create_h_line())

        list_row = QHBoxLayout()
        list_row.setSpacing(10)

        left_col = QVBoxLayout()
        lbl_black = QLabel("黑名单关键词")
        lbl_black.setStyleSheet("color: #E2E8F0; font-weight: 600;")
        self.text_edit_blacklist = QTextEdit()
        self.text_edit_blacklist.setPlainText("\n".join(cfg.filter_blacklist))
        self.text_edit_blacklist.setMinimumHeight(120)
        left_col.addWidget(lbl_black)
        left_col.addWidget(self.text_edit_blacklist)

        right_col = QVBoxLayout()
        lbl_white = QLabel("白名单关键词")
        lbl_white.setStyleSheet("color: #E2E8F0; font-weight: 600;")
        self.text_edit_whitelist = QTextEdit()
        self.text_edit_whitelist.setPlainText("\n".join(cfg.filter_whitelist))
        self.text_edit_whitelist.setMinimumHeight(120)
        right_col.addWidget(lbl_white)
        right_col.addWidget(self.text_edit_whitelist)

        list_row.addLayout(left_col, 1)
        list_row.addLayout(right_col, 1)
        card_layout2.addLayout(list_row)

        layout.addWidget(card2)

        # --- Save button ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_save = QPushButton("确定")
        btn_save.setObjectName("BtnPrimary")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.clicked.connect(self.save_and_close)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

        adaptive_height = max(WORK_MODE_DIALOG_HEIGHT, self.sizeHint().height())
        self.resize(WORK_MODE_DIALOG_WIDTH, adaptive_height)

    def _create_hotkey_row(self, key_name, hotkey_value):
        wrapper = QVBoxLayout()
        wrapper.setContentsMargins(24, 0, 0, 0)
        wrapper.setSpacing(8)

        row = QHBoxLayout()
        row.setSpacing(8)

        edit = HotkeyEdit()
        edit.set_hotkey(hotkey_value)
        edit.setMaximumSequenceLength(1)
        row.addWidget(edit, 1)

        btn_clear = QPushButton("默认")
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.clicked.connect(edit.clear)
        row.addWidget(btn_clear)

        wrapper.addLayout(row)
        setattr(self, f"activation_hotkey_edit_{key_name}", edit)
        return wrapper

    def save_and_close(self):
        cfg.activation_mode = self.activation_group.checkedId()
        cfg.activation_hotkey_click = self.activation_hotkey_edit_click.hotkey_text()
        cfg.activation_hotkey_hold = self.activation_hotkey_edit_hold.hotkey_text()
        cfg.filter_mode = self.button_group.checkedId()
        cfg.filter_blacklist = self._parse_keywords(
            self.text_edit_blacklist.toPlainText()
        )
        cfg.filter_whitelist = self._parse_keywords(
            self.text_edit_whitelist.toPlainText()
        )
        self.accept()

    @staticmethod
    def _parse_keywords(text):
        return [line.strip() for line in text.split("\n") if line.strip()]

    def _clear_keywords(self, target_edit: QTextEdit, list_name: str):
        reply = QMessageBox.question(
            self,
            "确认清空",
            f"确定要清空{list_name}关键词吗？此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            target_edit.clear()

    def _import_keywords_to(self, target_edit: QTextEdit):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "导入关键词",
            "",
            "文本文件 (*.txt *.csv *.log);;所有文件 (*.*)",
        )
        if not file_path:
            return

        with open(file_path, "rb") as f:
            raw = f.read()

        try:
            content = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            content = raw.decode("gbk", errors="ignore")

        target_edit.setPlainText("\n".join(self._parse_keywords(content)))


class InertiaSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("惯性滚动设置")
        self.setMinimumSize(INERTIA_DIALOG_WIDTH, INERTIA_DIALOG_HEIGHT)
        self.setSizeGripEnabled(True)

        self.setStyleSheet(get_dialog_stylesheet() + get_slider_style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # --- 使用建议 ---
        hint_label = QLabel(
            "<span style='color: #94A3B8; font-size: 13px;'>"
            "\u2139\ufe0f 建议搭配「长按启用键时启用」模式使用，松手即停配合惯性滑行，"
            "可以更好地模拟触控板或触摸屏的滑动手感。"
            "启用模式可在「高级设置 → 配置工作模式与应用过滤」中切换。</span>"
        )
        hint_label.setWordWrap(True)
        hint_label.setTextFormat(Qt.RichText)
        layout.addWidget(hint_label)

        # --- 阻尼/摩擦力 ---
        card1, card_layout1 = create_card()

        friction_header = QHBoxLayout()
        friction_title = QLabel(
            "<span style='font-weight: 600; color: #E2E8F0;'>阻尼 / 摩擦力</span>"
        )
        self.friction_value_label = QLabel()
        self.friction_value_label.setStyleSheet(get_value_label_style())
        friction_header.addWidget(friction_title)
        friction_header.addStretch()
        friction_header.addWidget(self.friction_value_label)
        card_layout1.addLayout(friction_header)

        friction_desc = QLabel(
            "<span style='color: #94A3B8; font-size: 12px;'>"
            "控制惯性滑行的持续时间。数值越大，滑得越远越久。</span>"
        )
        friction_desc.setWordWrap(True)
        card_layout1.addWidget(friction_desc)

        friction_slider_row = QHBoxLayout()
        hint_style = get_hint_label_style()
        lbl_compact = QLabel("紧凑")
        lbl_compact.setStyleSheet(hint_style)
        lbl_loose = QLabel("松弛")
        lbl_loose.setStyleSheet(hint_style)

        self.friction_slider = QSlider(Qt.Horizontal)
        self.friction_slider.setRange(100, 3000)
        self.friction_slider.setValue(int(cfg.inertia_friction_ms))
        self.friction_slider.setSingleStep(50)
        self.friction_slider.setFixedHeight(24)
        self.friction_slider.setCursor(Qt.PointingHandCursor)
        self.friction_slider.valueChanged.connect(self._on_friction_changed)

        friction_slider_row.addWidget(lbl_compact)
        friction_slider_row.addWidget(self.friction_slider, 1)
        friction_slider_row.addWidget(lbl_loose)
        card_layout1.addLayout(friction_slider_row)

        layout.addWidget(card1)

        # --- 触发阈值 ---
        card2, card_layout2 = create_card()

        threshold_header = QHBoxLayout()
        threshold_title = QLabel(
            "<span style='font-weight: 600; color: #E2E8F0;'>触发阈值</span>"
        )
        self.threshold_value_label = QLabel()
        self.threshold_value_label.setStyleSheet(get_value_label_style())
        threshold_header.addWidget(threshold_title)
        threshold_header.addStretch()
        threshold_header.addWidget(self.threshold_value_label)
        card_layout2.addLayout(threshold_header)

        threshold_desc = QLabel(
            "<span style='color: #94A3B8; font-size: 12px;'>"
            "鼠标移动速度超过此值时，松开中键才会触发惯性滑行。"
            "低于此值则直接停止，避免轻微拖动也产生惯性。</span>"
        )
        threshold_desc.setWordWrap(True)
        card_layout2.addWidget(threshold_desc)

        threshold_slider_row = QHBoxLayout()
        lbl_slow = QLabel("低")
        lbl_slow.setStyleSheet(hint_style)
        lbl_fast = QLabel("高")
        lbl_fast.setStyleSheet(hint_style)

        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setRange(30, 300)
        self.threshold_slider.setValue(int(cfg.inertia_threshold))
        self.threshold_slider.setSingleStep(5)
        self.threshold_slider.setFixedHeight(24)
        self.threshold_slider.setCursor(Qt.PointingHandCursor)
        self.threshold_slider.valueChanged.connect(self._on_threshold_changed)

        threshold_slider_row.addWidget(lbl_slow)
        threshold_slider_row.addWidget(self.threshold_slider, 1)
        threshold_slider_row.addWidget(lbl_fast)
        card_layout2.addLayout(threshold_slider_row)

        layout.addWidget(card2)

        layout.addStretch()

        # --- Save button ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_save = QPushButton("确定")
        btn_save.setObjectName("BtnPrimary")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.clicked.connect(self.save_and_close)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

        # 初始化显示
        self._update_friction_label()
        self._update_threshold_label()

        adaptive_height = max(INERTIA_DIALOG_HEIGHT, self.sizeHint().height())
        self.resize(INERTIA_DIALOG_WIDTH, adaptive_height)

    def _update_friction_label(self):
        ms = self.friction_slider.value()
        self.friction_value_label.setText(f"{ms} ms")

    def _update_threshold_label(self):
        val = self.threshold_slider.value()
        self.threshold_value_label.setText(f"{val} px/s")

    def _on_friction_changed(self, _value):
        self._update_friction_label()

    def _on_threshold_changed(self, _value):
        self._update_threshold_label()

    def save_and_close(self):
        cfg.inertia_friction_ms = self.friction_slider.value()
        cfg.inertia_threshold = float(self.threshold_slider.value())
        self.accept()
