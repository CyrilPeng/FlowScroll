import os

from PySide6.QtWidgets import (
    QApplication,
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
    QSizePolicy,
    QLineEdit,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

from FlowScroll.core.config import STATE_LOCK, cfg, runtime
from FlowScroll.core.config import (
    get_config_file,
    get_config_override_source,
    set_persisted_config_file,
)
from FlowScroll.core.filter_validation import collect_invalid_regex_lines
from FlowScroll.i18n import tr
from FlowScroll.ui.components import HotkeyEdit
from FlowScroll.ui.helpers import create_card, create_h_line
from FlowScroll.ui.utils import resource_path
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
        self.setWindowTitle(tr("dialog.reverse.title"))
        self.setMinimumSize(REVERSE_DIALOG_WIDTH, REVERSE_DIALOG_HEIGHT)
        self.setSizeGripEnabled(True)

        self.setStyleSheet(get_dialog_stylesheet() + get_checkbox_style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        card, card_layout = create_card()

        hint_lbl = QLabel(tr("dialog.reverse.hint"))
        hint_lbl.setWordWrap(True)
        card_layout.addWidget(hint_lbl)

        card_layout.addWidget(create_h_line())

        self.chk_reverse_y = QCheckBox(tr("dialog.reverse.y"))
        self.chk_reverse_y.setChecked(cfg.reverse_y)
        self.chk_reverse_y.setCursor(Qt.PointingHandCursor)
        card_layout.addWidget(self.chk_reverse_y)

        self.chk_reverse_x = QCheckBox(tr("dialog.reverse.x"))
        self.chk_reverse_x.setChecked(cfg.reverse_x)
        self.chk_reverse_x.setCursor(Qt.PointingHandCursor)
        card_layout.addWidget(self.chk_reverse_x)

        layout.addWidget(card)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_save = QPushButton(tr("dialog.reverse.save"))
        btn_save.setObjectName("BtnPrimary")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.clicked.connect(self.save_and_close)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

        adaptive_height = max(REVERSE_DIALOG_HEIGHT, self.sizeHint().height())
        self.resize(REVERSE_DIALOG_WIDTH, adaptive_height)

    def save_and_close(self) -> None:
        cfg.reverse_y = self.chk_reverse_y.isChecked()
        cfg.reverse_x = self.chk_reverse_x.isChecked()
        self.accept()


class WorkModeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dialog.work.title"))
        self.setMinimumSize(WORK_MODE_DIALOG_WIDTH, WORK_MODE_DIALOG_HEIGHT)
        self.setSizeGripEnabled(True)

        self.setStyleSheet(
            get_dialog_stylesheet() + get_radiobutton_style() + get_checkbox_style()
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        mode_card, mode_layout = create_card()
        mode_layout.setContentsMargins(16, 16, 16, 16)
        mode_layout.setSpacing(12)

        title = QLabel(tr("dialog.work.header_title"))
        title.setStyleSheet("font-size: 17px; font-weight: 700; color: #F8FAFC;")
        subtitle = QLabel(tr("dialog.work.subtitle"))
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #94A3B8; font-size: 13px;")
        mode_layout.addWidget(title)
        mode_layout.addWidget(subtitle)

        self.activation_group = QButtonGroup(self)
        self._build_mode_block(
            mode_layout,
            mode_id=0,
            title=tr("dialog.work.mode_click_title"),
            desc=tr("dialog.work.mode_click_desc"),
            key_name="click",
            hotkey_value=cfg.activation_hotkey_click,
        )
        self._build_mode_block(
            mode_layout,
            mode_id=1,
            title=tr("dialog.work.mode_hold_title"),
            desc=tr("dialog.work.mode_hold_desc"),
            key_name="hold",
            hotkey_value=cfg.activation_hotkey_hold,
        )
        self.radio_click_toggle.setChecked(cfg.activation_mode == 0)
        self.radio_hold.setChecked(cfg.activation_mode == 1)
        layout.addWidget(mode_card)

        policy_card, policy_layout = create_card()
        policy_layout.setContentsMargins(16, 16, 16, 16)
        policy_layout.setSpacing(10)

        self.chk_activation_compat_mode = QCheckBox(tr("dialog.work.compat_mode"))
        self.chk_activation_compat_mode.setChecked(cfg.activation_compat_mode)
        self.chk_activation_compat_mode.setCursor(Qt.PointingHandCursor)
        self.chk_activation_compat_mode.toggled.connect(self._on_compat_mode_changed)
        policy_layout.addWidget(self.chk_activation_compat_mode)

        delay_row = QHBoxLayout()
        delay_row.setContentsMargins(8, 0, 0, 0)
        delay_row.setSpacing(10)
        self.delay_title = QLabel(tr("dialog.work.delay_title"))
        self.delay_title.setStyleSheet("color: #94A3B8; font-size: 13px;")
        self.delay_value_label = QLabel()
        self.delay_value_label.setStyleSheet(get_value_label_style())

        self.activation_delay_slider = QSlider(Qt.Horizontal)
        self.activation_delay_slider.setRange(0, 500)
        self.activation_delay_slider.setSingleStep(10)
        self.activation_delay_slider.setValue(int(cfg.activation_delay_ms))
        self.activation_delay_slider.valueChanged.connect(self._update_delay_label)
        self.activation_delay_slider.setCursor(Qt.PointingHandCursor)
        self.activation_delay_slider.setFixedHeight(22)

        delay_row.addWidget(self.delay_title)
        delay_row.addWidget(self.activation_delay_slider, 1)
        delay_row.addWidget(self.delay_value_label)
        policy_layout.addLayout(delay_row)

        self.compat_hint = QLabel(tr("dialog.work.compat_hint"))
        self.compat_hint.setWordWrap(True)
        self.compat_hint.setContentsMargins(8, 0, 0, 0)
        self.compat_hint.setStyleSheet("color: #94A3B8; font-size: 12px;")
        policy_layout.addWidget(self.compat_hint)

        layout.addWidget(policy_card)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_save = QPushButton(tr("dialog.work.save"))
        btn_save.setObjectName("BtnPrimary")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.clicked.connect(self.save_and_close)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

        self._update_delay_label()
        self._on_compat_mode_changed(self.chk_activation_compat_mode.isChecked())

        adaptive_height = max(WORK_MODE_DIALOG_HEIGHT, self.sizeHint().height())
        self.resize(WORK_MODE_DIALOG_WIDTH, adaptive_height)

    def _build_mode_block(
        self, parent_layout, mode_id, title, desc, key_name, hotkey_value
    ):
        block = QLabel()
        block.setFixedHeight(1)
        if parent_layout.count() > 0:
            parent_layout.addWidget(create_h_line())

        radio = QRadioButton(title)
        radio.setCursor(Qt.PointingHandCursor)
        self.activation_group.addButton(radio, mode_id)
        parent_layout.addWidget(radio)

        if mode_id == 0:
            self.radio_click_toggle = radio
        else:
            self.radio_hold = radio

        desc_lbl = QLabel(desc)
        desc_lbl.setWordWrap(True)
        desc_lbl.setContentsMargins(24, 0, 0, 0)
        desc_lbl.setStyleSheet("color: #94A3B8; font-size: 12px;")
        parent_layout.addWidget(desc_lbl)
        parent_layout.addLayout(self._create_hotkey_row(key_name, hotkey_value))

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

        btn_clear = QPushButton(tr("dialog.work.default"))
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.clicked.connect(edit.clear)
        row.addWidget(btn_clear)

        wrapper.addLayout(row)
        setattr(self, f"activation_hotkey_edit_{key_name}", edit)
        return wrapper

    def _update_delay_label(self):
        self.delay_value_label.setText(f"{self.activation_delay_slider.value()} ms")

    def _on_compat_mode_changed(self, checked):
        self.activation_delay_slider.setEnabled(checked)
        self.delay_title.setEnabled(checked)
        self.delay_value_label.setEnabled(checked)
        self.compat_hint.setEnabled(checked)

    def save_and_close(self) -> None:
        cfg.activation_mode = self.activation_group.checkedId()
        cfg.activation_hotkey_click = self.activation_hotkey_edit_click.hotkey_text()
        cfg.activation_hotkey_hold = self.activation_hotkey_edit_hold.hotkey_text()
        cfg.activation_compat_mode = self.chk_activation_compat_mode.isChecked()
        cfg.activation_delay_ms = int(self.activation_delay_slider.value())
        self.accept()


class AppFilterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dialog.filter.title"))
        self.setMinimumSize(WORK_MODE_DIALOG_WIDTH, WORK_MODE_DIALOG_HEIGHT)
        self.setSizeGripEnabled(True)

        self.setStyleSheet(
            get_dialog_stylesheet()
            + get_radiobutton_style()
            + get_textedit_style()
            + get_checkbox_style()
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel(tr("dialog.filter.header_title"))
        title.setStyleSheet("font-size: 17px; font-weight: 700; color: #F8FAFC;")
        subtitle = QLabel(tr("dialog.filter.subtitle"))
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #94A3B8; font-size: 13px;")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        with STATE_LOCK:
            process_name_status = runtime.process_name_status

        self.process_name_warning = QLabel(tr("dialog.filter.process_name_unavailable"))
        self.process_name_warning.setWordWrap(True)
        self.process_name_warning.setStyleSheet(
            "color: #FCA5A5; background: rgba(127, 29, 29, 0.28); border: 1px solid rgba(252, 165, 165, 0.35); border-radius: 10px; padding: 10px 12px;"
        )
        self.process_name_warning.setVisible(process_name_status == "unavailable")
        layout.addWidget(self.process_name_warning)

        mode_card, mode_layout = create_card()
        mode_layout.setContentsMargins(16, 16, 16, 16)
        mode_layout.setSpacing(10)

        mode_title = QLabel(tr("dialog.filter.mode_title"))
        mode_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #E2E8F0;")
        mode_layout.addWidget(mode_title)

        self.button_group = QButtonGroup(self)

        self.radio_global = QRadioButton(tr("dialog.filter.mode_global"))
        self.radio_global.setCursor(Qt.PointingHandCursor)
        self.button_group.addButton(self.radio_global, 0)
        mode_layout.addWidget(self.radio_global)

        desc_global = QLabel(tr("dialog.filter.mode_global_desc"))
        desc_global.setWordWrap(True)
        desc_global.setContentsMargins(24, 0, 0, 0)
        desc_global.setStyleSheet("color: #94A3B8; font-size: 12px;")
        mode_layout.addWidget(desc_global)

        mode_layout.addWidget(create_h_line())

        self.radio_blacklist = QRadioButton(tr("dialog.filter.mode_blacklist"))
        self.radio_blacklist.setCursor(Qt.PointingHandCursor)
        self.button_group.addButton(self.radio_blacklist, 1)
        mode_layout.addWidget(self.radio_blacklist)

        desc_blacklist = QLabel(tr("dialog.filter.mode_blacklist_desc"))
        desc_blacklist.setWordWrap(True)
        desc_blacklist.setContentsMargins(24, 0, 0, 0)
        desc_blacklist.setStyleSheet("color: #94A3B8; font-size: 12px;")
        mode_layout.addWidget(desc_blacklist)

        mode_layout.addWidget(create_h_line())

        self.radio_whitelist = QRadioButton(tr("dialog.filter.mode_whitelist"))
        self.radio_whitelist.setCursor(Qt.PointingHandCursor)
        self.button_group.addButton(self.radio_whitelist, 2)
        mode_layout.addWidget(self.radio_whitelist)

        desc_whitelist = QLabel(tr("dialog.filter.mode_whitelist_desc"))
        desc_whitelist.setWordWrap(True)
        desc_whitelist.setContentsMargins(24, 0, 0, 0)
        desc_whitelist.setStyleSheet("color: #94A3B8; font-size: 12px;")
        mode_layout.addWidget(desc_whitelist)

        self.radio_global.setChecked(cfg.filter_mode == 0)
        self.radio_blacklist.setChecked(cfg.filter_mode == 1)
        self.radio_whitelist.setChecked(cfg.filter_mode == 2)
        layout.addWidget(mode_card)

        keyword_card, keyword_layout = create_card()
        keyword_layout.setContentsMargins(16, 16, 16, 16)
        keyword_layout.setSpacing(10)

        list_row = QHBoxLayout()
        list_row.setSpacing(12)

        left_col = QVBoxLayout()
        left_col.setSpacing(8)
        lbl_black = QLabel(tr("dialog.filter.blacklist_title"))
        lbl_black.setStyleSheet("color: #E2E8F0; font-weight: 600;")
        lbl_black.setAlignment(Qt.AlignHCenter)
        black_action_row = QHBoxLayout()
        black_action_row.setSpacing(8)
        black_action_row.setContentsMargins(0, 7, 0, 7)
        self.btn_import_black = QPushButton(tr("dialog.filter.import"))
        self.btn_import_black.setCursor(Qt.PointingHandCursor)
        self.btn_import_black.setObjectName("BtnSmall")
        self.btn_import_black.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_import_black.setFixedHeight(20)
        self.btn_import_black.setStyleSheet(
            "min-height: 20px; padding-top: 1px; padding-bottom: 1px;"
        )
        self.btn_import_black.clicked.connect(
            lambda: self._import_keywords_to(self.text_edit_blacklist)
        )
        black_action_row.addWidget(self.btn_import_black)
        self.btn_clear_black = QPushButton(tr("dialog.filter.clear"))
        self.btn_clear_black.setCursor(Qt.PointingHandCursor)
        self.btn_clear_black.setObjectName("BtnSmall")
        self.btn_clear_black.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_clear_black.setFixedHeight(20)
        self.btn_clear_black.setStyleSheet(
            "min-height: 20px; padding-top: 1px; padding-bottom: 1px;"
        )
        self.btn_clear_black.clicked.connect(
            lambda: self._clear_keywords(
                self.text_edit_blacklist, tr("dialog.filter.blacklist_name")
            )
        )
        black_action_row.addWidget(self.btn_clear_black)
        self.text_edit_blacklist = QTextEdit()
        self.text_edit_blacklist.setPlainText("\n".join(cfg.filter_blacklist))
        self.text_edit_blacklist.setMinimumHeight(140)
        left_col.addWidget(lbl_black)
        left_col.addLayout(black_action_row)
        left_col.addWidget(self.text_edit_blacklist)

        right_col = QVBoxLayout()
        right_col.setSpacing(8)
        lbl_white = QLabel(tr("dialog.filter.whitelist_title"))
        lbl_white.setStyleSheet("color: #E2E8F0; font-weight: 600;")
        lbl_white.setAlignment(Qt.AlignHCenter)
        white_action_row = QHBoxLayout()
        white_action_row.setSpacing(8)
        white_action_row.setContentsMargins(0, 7, 0, 7)
        self.btn_import_white = QPushButton(tr("dialog.filter.import"))
        self.btn_import_white.setCursor(Qt.PointingHandCursor)
        self.btn_import_white.setObjectName("BtnSmall")
        self.btn_import_white.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_import_white.setFixedHeight(20)
        self.btn_import_white.setStyleSheet(
            "min-height: 20px; padding-top: 1px; padding-bottom: 1px;"
        )
        self.btn_import_white.clicked.connect(
            lambda: self._import_keywords_to(self.text_edit_whitelist)
        )
        white_action_row.addWidget(self.btn_import_white)
        self.btn_clear_white = QPushButton(tr("dialog.filter.clear"))
        self.btn_clear_white.setCursor(Qt.PointingHandCursor)
        self.btn_clear_white.setObjectName("BtnSmall")
        self.btn_clear_white.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_clear_white.setFixedHeight(20)
        self.btn_clear_white.setStyleSheet(
            "min-height: 20px; padding-top: 1px; padding-bottom: 1px;"
        )
        self.btn_clear_white.clicked.connect(
            lambda: self._clear_keywords(
                self.text_edit_whitelist, tr("dialog.filter.whitelist_name")
            )
        )
        white_action_row.addWidget(self.btn_clear_white)
        self.text_edit_whitelist = QTextEdit()
        self.text_edit_whitelist.setPlainText("\n".join(cfg.filter_whitelist))
        self.text_edit_whitelist.setMinimumHeight(140)
        right_col.addWidget(lbl_white)
        right_col.addLayout(white_action_row)
        right_col.addWidget(self.text_edit_whitelist)

        list_row.addLayout(left_col, 1)
        list_row.addLayout(right_col, 1)
        keyword_layout.addLayout(list_row)

        hint = QLabel(tr("dialog.filter.hint"))
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #94A3B8; font-size: 12px;")
        keyword_layout.addWidget(hint)

        self.chk_use_regex = QCheckBox(tr("dialog.filter.use_regex"))
        self.chk_use_regex.setChecked(cfg.filter_use_regex)
        self.chk_use_regex.setCursor(Qt.PointingHandCursor)
        keyword_layout.addWidget(self.chk_use_regex)

        layout.addWidget(keyword_card)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_save = QPushButton(tr("dialog.filter.save"))
        btn_save.setObjectName("BtnPrimary")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.clicked.connect(self.save_and_close)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

        adaptive_height = max(WORK_MODE_DIALOG_HEIGHT, self.sizeHint().height())
        self.resize(WORK_MODE_DIALOG_WIDTH, adaptive_height)

    @staticmethod
    def _parse_keywords(text):
        return [line.strip() for line in text.split("\n") if line.strip()]

    def _collect_invalid_regex_rules(self):
        invalid_rules = []
        rule_groups = [
            (tr("dialog.filter.blacklist_name"), self.text_edit_blacklist.toPlainText()),
            (tr("dialog.filter.whitelist_name"), self.text_edit_whitelist.toPlainText()),
        ]
        for list_name, raw_text in rule_groups:
            for line_no, keyword in collect_invalid_regex_lines(raw_text):
                invalid_rules.append(
                    tr(
                        "dialog.filter.invalid_regex_item",
                        name=list_name,
                        line=line_no,
                        pattern=keyword,
                    )
                )
        return invalid_rules

    def _clear_keywords(self, target_edit: QTextEdit, list_name: str):
        reply = QMessageBox.question(
            self,
            tr("dialog.filter.clear_confirm_title"),
            tr("dialog.filter.clear_confirm_body", name=list_name),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            target_edit.clear()

    def _import_keywords_to(self, target_edit: QTextEdit):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            tr("dialog.filter.import_title"),
            "",
            tr("dialog.filter.import_filter"),
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

    def save_and_close(self) -> None:
        if self.chk_use_regex.isChecked():
            invalid_rules = self._collect_invalid_regex_rules()
            if invalid_rules:
                QMessageBox.warning(
                    self,
                    tr("dialog.filter.invalid_regex_title"),
                    tr(
                        "dialog.filter.invalid_regex_body",
                        details="\n".join(invalid_rules),
                    ),
                )
                return
        cfg.filter_mode = self.button_group.checkedId()
        cfg.filter_blacklist = self._parse_keywords(
            self.text_edit_blacklist.toPlainText()
        )
        cfg.filter_whitelist = self._parse_keywords(
            self.text_edit_whitelist.toPlainText()
        )
        cfg.filter_use_regex = self.chk_use_regex.isChecked()
        self.accept()


class InertiaSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dialog.inertia.title"))
        self.setMinimumSize(INERTIA_DIALOG_WIDTH, INERTIA_DIALOG_HEIGHT)
        self.setSizeGripEnabled(True)

        self.setStyleSheet(get_dialog_stylesheet() + get_slider_style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel(tr("dialog.inertia.header_title"))
        title.setStyleSheet("font-size: 17px; font-weight: 700; color: #F8FAFC;")
        subtitle = QLabel(tr("dialog.inertia.subtitle"))
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #94A3B8; font-size: 13px;")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        card1, card_layout1 = create_card()
        card1.setStyleSheet(card1.styleSheet() + "QLabel{color:#E2E8F0;}")
        card_layout1.setContentsMargins(16, 16, 16, 16)
        card_layout1.setSpacing(10)

        friction_header = QHBoxLayout()
        friction_title = QLabel(tr("dialog.inertia.friction_title"))
        friction_title.setStyleSheet(
            "font-size: 15px; font-weight: 700; color: #E2E8F0;"
        )
        self.friction_value_label = QLabel()
        self.friction_value_label.setStyleSheet(get_value_label_style())
        friction_header.addWidget(friction_title)
        friction_header.addStretch()
        friction_header.addWidget(self.friction_value_label)
        card_layout1.addLayout(friction_header)

        friction_desc = QLabel(tr("dialog.inertia.friction_desc"))
        friction_desc.setWordWrap(True)
        card_layout1.addWidget(friction_desc)

        friction_slider_row = QHBoxLayout()
        hint_style = get_hint_label_style()
        lbl_compact = QLabel(tr("dialog.inertia.compact"))
        lbl_compact.setStyleSheet(hint_style)
        lbl_loose = QLabel(tr("dialog.inertia.loose"))
        lbl_loose.setStyleSheet(hint_style)

        self.friction_slider = QSlider(Qt.Horizontal)
        self.friction_slider.setRange(100, 3000)
        self.friction_slider.setValue(int(cfg.inertia_friction_ms))
        self.friction_slider.setSingleStep(50)
        self.friction_slider.setFixedHeight(22)
        self.friction_slider.setCursor(Qt.PointingHandCursor)
        self.friction_slider.valueChanged.connect(self._on_friction_changed)

        friction_slider_row.addWidget(lbl_compact)
        friction_slider_row.addWidget(self.friction_slider, 1)
        friction_slider_row.addWidget(lbl_loose)
        card_layout1.addLayout(friction_slider_row)

        layout.addWidget(card1)

        card2, card_layout2 = create_card()
        card2.setStyleSheet(card2.styleSheet() + "QLabel{color:#E2E8F0;}")
        card_layout2.setContentsMargins(16, 16, 16, 16)
        card_layout2.setSpacing(10)

        threshold_header = QHBoxLayout()
        threshold_title = QLabel(tr("dialog.inertia.threshold_title"))
        threshold_title.setStyleSheet(
            "font-size: 15px; font-weight: 700; color: #E2E8F0;"
        )
        self.threshold_value_label = QLabel()
        self.threshold_value_label.setStyleSheet(get_value_label_style())
        threshold_header.addWidget(threshold_title)
        threshold_header.addStretch()
        threshold_header.addWidget(self.threshold_value_label)
        card_layout2.addLayout(threshold_header)

        threshold_desc = QLabel(tr("dialog.inertia.threshold_desc"))
        threshold_desc.setWordWrap(True)
        card_layout2.addWidget(threshold_desc)

        threshold_slider_row = QHBoxLayout()
        lbl_slow = QLabel(tr("dialog.inertia.low"))
        lbl_slow.setStyleSheet(hint_style)
        lbl_fast = QLabel(tr("dialog.inertia.high"))
        lbl_fast.setStyleSheet(hint_style)

        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setRange(30, 300)
        self.threshold_slider.setValue(int(cfg.inertia_threshold))
        self.threshold_slider.setSingleStep(5)
        self.threshold_slider.setFixedHeight(22)
        self.threshold_slider.setCursor(Qt.PointingHandCursor)
        self.threshold_slider.valueChanged.connect(self._on_threshold_changed)

        threshold_slider_row.addWidget(lbl_slow)
        threshold_slider_row.addWidget(self.threshold_slider, 1)
        threshold_slider_row.addWidget(lbl_fast)
        card_layout2.addLayout(threshold_slider_row)

        layout.addWidget(card2)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_save = QPushButton(tr("dialog.inertia.save"))
        btn_save.setObjectName("BtnPrimary")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.clicked.connect(self.save_and_close)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

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

    def save_and_close(self) -> None:
        cfg.inertia_friction_ms = self.friction_slider.value()
        cfg.inertia_threshold = float(self.threshold_slider.value())
        self.accept()


class ConfigStorageDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._changed = False
        self._last_applied_path = get_config_file()

        self.setWindowTitle(tr("dialog.config_path.title"))
        self.setMinimumWidth(520)
        self.setStyleSheet(get_dialog_stylesheet())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        card, card_layout = create_card()

        hint_label = QLabel(tr("dialog.config_path.hint"))
        hint_label.setWordWrap(True)
        hint_label.setStyleSheet("color: #94A3B8; font-size: 13px; line-height: 1.5;")
        card_layout.addWidget(hint_label)

        self.locked_label = QLabel(tr("tab.advanced.config_path_env_locked"))
        self.locked_label.setWordWrap(True)
        self.locked_label.setStyleSheet(
            "color: #FDE68A; background: rgba(120, 53, 15, 0.28); "
            "border: 1px solid rgba(251, 191, 36, 0.35); border-radius: 10px; "
            "padding: 10px 12px; line-height: 1.4;"
        )
        card_layout.addWidget(self.locked_label)

        card_layout.addWidget(create_h_line())

        path_title = QLabel(tr("dialog.config_path.current_path_label"))
        path_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #E2E8F0;")
        card_layout.addWidget(path_title)

        path_row = QHBoxLayout()
        path_row.setSpacing(10)

        self.path_edit = QLineEdit()
        self.path_edit.setClearButtonEnabled(True)
        self.path_edit.returnPressed.connect(self.apply_path_from_input_with_notice)
        self.path_edit.editingFinished.connect(self.apply_path_from_input)
        path_row.addWidget(self.path_edit, 1)

        self.btn_pick_path = QPushButton()
        self.btn_pick_path.setObjectName("BtnIcon")
        self.btn_pick_path.setCursor(Qt.PointingHandCursor)
        self.btn_pick_path.setToolTip(tr("dialog.config_path.change_btn"))
        folder_icon_path = resource_path(
            os.path.join("FlowScroll", "resources", "ic_folder.svg")
        )
        if os.path.exists(folder_icon_path):
            self.btn_pick_path.setIcon(QIcon(folder_icon_path))
            self.btn_pick_path.setIconSize(QSize(18, 18))
        else:
            self.btn_pick_path.setText("...")
        self.btn_pick_path.clicked.connect(self.choose_path)
        path_row.addWidget(self.btn_pick_path)

        card_layout.addLayout(path_row)

        layout.addWidget(card)
        layout.addStretch()

        self.btn_reset = QPushButton(tr("tab.advanced.config_path_reset_btn"))
        self.btn_reset.setObjectName("BtnDanger")
        self.btn_reset.setCursor(Qt.PointingHandCursor)
        self.btn_reset.clicked.connect(self.reset_to_default)
        self.btn_reset.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.btn_reset)

        self.btn_copy_path = QPushButton(tr("dialog.config_path.copy_btn"))
        self.btn_copy_path.setObjectName("BtnPrimary")
        self.btn_copy_path.setCursor(Qt.PointingHandCursor)
        self.btn_copy_path.clicked.connect(self.copy_current_path)
        self.btn_copy_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.btn_copy_path)

        self.refresh_state()
        self.resize(560, max(260, self.sizeHint().height()))

    def _save_parent_config(self):
        parent = self.parent()
        if parent is not None and hasattr(parent, "save_presets_to_file"):
            parent.save_presets_to_file()

    def _apply_path(self, path: str | None):
        set_persisted_config_file(path)
        self._changed = True
        self._last_applied_path = get_config_file()
        self._save_parent_config()
        self.refresh_state()

    def refresh_state(self) -> None:
        source = get_config_override_source()
        env_override = source.startswith("env_")

        if self.path_edit.text().strip() != self._last_applied_path:
            self.path_edit.setText(self._last_applied_path)
        self.locked_label.setVisible(env_override)
        self.btn_pick_path.setEnabled(not env_override)
        self.path_edit.setEnabled(not env_override)
        self.btn_reset.setEnabled(source == "custom")
        self.btn_copy_path.setEnabled(True)

    def choose_path(self) -> None:
        selected_path, _ = QFileDialog.getSaveFileName(
            self,
            tr("tab.advanced.config_path_dialog_title"),
            get_config_file(),
            tr("tab.advanced.config_path_dialog_filter"),
        )
        if not selected_path:
            return

        self._apply_path(selected_path)
        QMessageBox.information(
            self,
            tr("webdav.success_title"),
            tr("tab.advanced.config_path_changed", path=get_config_file()),
        )

    def apply_path_from_input(self) -> bool:
        text = self.path_edit.text().strip()
        if not text or text == self._last_applied_path:
            self.path_edit.setText(self._last_applied_path)
            return False
        self._apply_path(text)
        return True

    def apply_path_from_input_with_notice(self) -> None:
        if not self.apply_path_from_input():
            return
        QMessageBox.information(
            self,
            tr("webdav.success_title"),
            tr("tab.advanced.config_path_changed", path=get_config_file()),
        )

    def reset_to_default(self) -> None:
        if get_config_override_source() != "custom":
            return

        self._apply_path(None)
        QMessageBox.information(
            self,
            tr("webdav.success_title"),
            tr("tab.advanced.config_path_reset_done", path=get_config_file()),
        )

    def copy_current_path(self) -> None:
        QApplication.clipboard().setText(self.path_edit.text().strip() or get_config_file())
        QMessageBox.information(
            self,
            tr("webdav.success_title"),
            tr("dialog.config_path.copy_done"),
        )
