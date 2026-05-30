"""应用过滤设置对话框（黑名单/白名单）。

允许用户按进程名或窗口标题过滤哪些应用程序可以触发 FlowScroll 的
自动滚动功能。支持三种过滤模式：

* **全局模式（mode=0）**：所有应用程序均可触发。
* **黑名单模式（mode=1）**：匹配黑名单关键词的应用程序**不**触发。
* **白名单模式（mode=2）**：仅匹配白名单关键词的应用程序触发。

每条关键词可选择普通子串匹配或正则表达式匹配（启用 ``filter_use_regex``）。
黑名单/白名单支持从文本文件批量导入以及逐条清空。
"""

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
    QFileDialog,
    QMessageBox,
    QSizePolicy,
)
from PySide6.QtCore import Qt

from FlowScroll.core.config import STATE_LOCK, cfg, runtime, set_config_attr
from FlowScroll.core.filter_validation import collect_invalid_regex_lines
from FlowScroll.i18n import tr
from FlowScroll.ui.helpers import create_card, create_h_line
from FlowScroll.ui.styles import (
    get_dialog_stylesheet,
    get_checkbox_style,
    get_radiobutton_style,
    get_textedit_style,
    get_dialog_title_style,
    get_dialog_subtitle_style,
    get_card_title_style,
    get_description_style,
    get_column_header_style,
    get_error_banner_style,
)
from FlowScroll.constants import (
    WORK_MODE_DIALOG_WIDTH,
    WORK_MODE_DIALOG_HEIGHT,
)


class AppFilterDialog(QDialog):
    """应用过滤设置对话框。

    属性:
        button_group (QButtonGroup): 互斥的过滤模式单选按钮组。
        text_edit_blacklist (QTextEdit): 黑名单关键词编辑框。
        text_edit_whitelist (QTextEdit): 白名单关键词编辑框。
        chk_use_regex (QCheckBox): 是否启用正则表达式匹配。
        process_name_warning (QLabel): 当无法获取当前进程名时显示的警告横幅。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dialog.filter.title"))
        self.setMinimumSize(WORK_MODE_DIALOG_WIDTH, WORK_MODE_DIALOG_HEIGHT)
        self.setSizeGripEnabled(True)

        self.setStyleSheet(
            get_dialog_stylesheet() + get_radiobutton_style() + get_textedit_style() + get_checkbox_style()
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel(tr("dialog.filter.header_title"))
        title.setStyleSheet(get_dialog_title_style())
        subtitle = QLabel(tr("dialog.filter.subtitle"))
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(get_dialog_subtitle_style())
        layout.addWidget(title)
        layout.addWidget(subtitle)

        with STATE_LOCK:
            process_name_status = runtime.process_name_status

        self.process_name_warning = QLabel(tr("dialog.filter.process_name_unavailable"))
        self.process_name_warning.setWordWrap(True)
        self.process_name_warning.setStyleSheet(get_error_banner_style())
        self.process_name_warning.setVisible(process_name_status == "unavailable")
        layout.addWidget(self.process_name_warning)

        mode_card, mode_layout = create_card()
        mode_layout.setContentsMargins(16, 16, 16, 16)
        mode_layout.setSpacing(10)

        mode_title = QLabel(tr("dialog.filter.mode_title"))
        mode_title.setStyleSheet(get_card_title_style())
        mode_layout.addWidget(mode_title)

        self.button_group = QButtonGroup(self)

        self.radio_global = QRadioButton(tr("dialog.filter.mode_global"))
        self.radio_global.setCursor(Qt.PointingHandCursor)
        self.button_group.addButton(self.radio_global, 0)
        mode_layout.addWidget(self.radio_global)

        desc_global = QLabel(tr("dialog.filter.mode_global_desc"))
        desc_global.setWordWrap(True)
        desc_global.setContentsMargins(24, 0, 0, 0)
        desc_global.setStyleSheet(get_description_style())
        mode_layout.addWidget(desc_global)

        mode_layout.addWidget(create_h_line())

        self.radio_blacklist = QRadioButton(tr("dialog.filter.mode_blacklist"))
        self.radio_blacklist.setCursor(Qt.PointingHandCursor)
        self.button_group.addButton(self.radio_blacklist, 1)
        mode_layout.addWidget(self.radio_blacklist)

        desc_blacklist = QLabel(tr("dialog.filter.mode_blacklist_desc"))
        desc_blacklist.setWordWrap(True)
        desc_blacklist.setContentsMargins(24, 0, 0, 0)
        desc_blacklist.setStyleSheet(get_description_style())
        mode_layout.addWidget(desc_blacklist)

        mode_layout.addWidget(create_h_line())

        self.radio_whitelist = QRadioButton(tr("dialog.filter.mode_whitelist"))
        self.radio_whitelist.setCursor(Qt.PointingHandCursor)
        self.button_group.addButton(self.radio_whitelist, 2)
        mode_layout.addWidget(self.radio_whitelist)

        desc_whitelist = QLabel(tr("dialog.filter.mode_whitelist_desc"))
        desc_whitelist.setWordWrap(True)
        desc_whitelist.setContentsMargins(24, 0, 0, 0)
        desc_whitelist.setStyleSheet(get_description_style())
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
        lbl_black.setStyleSheet(get_column_header_style())
        lbl_black.setAlignment(Qt.AlignHCenter)
        black_action_row = QHBoxLayout()
        black_action_row.setSpacing(8)
        black_action_row.setContentsMargins(0, 7, 0, 7)
        self.btn_import_black = QPushButton(tr("dialog.filter.import"))
        self.btn_import_black.setCursor(Qt.PointingHandCursor)
        self.btn_import_black.setObjectName("BtnSmall")
        self.btn_import_black.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_import_black.setFixedHeight(20)
        self.btn_import_black.setStyleSheet("min-height: 20px; padding-top: 1px; padding-bottom: 1px;")
        self.btn_import_black.clicked.connect(lambda: self._import_keywords_to(self.text_edit_blacklist))
        black_action_row.addWidget(self.btn_import_black)
        self.btn_clear_black = QPushButton(tr("dialog.filter.clear"))
        self.btn_clear_black.setCursor(Qt.PointingHandCursor)
        self.btn_clear_black.setObjectName("BtnSmall")
        self.btn_clear_black.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_clear_black.setFixedHeight(20)
        self.btn_clear_black.setStyleSheet("min-height: 20px; padding-top: 1px; padding-bottom: 1px;")
        self.btn_clear_black.clicked.connect(
            lambda: self._clear_keywords(self.text_edit_blacklist, tr("dialog.filter.blacklist_name"))
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
        lbl_white.setStyleSheet(get_column_header_style())
        lbl_white.setAlignment(Qt.AlignHCenter)
        white_action_row = QHBoxLayout()
        white_action_row.setSpacing(8)
        white_action_row.setContentsMargins(0, 7, 0, 7)
        self.btn_import_white = QPushButton(tr("dialog.filter.import"))
        self.btn_import_white.setCursor(Qt.PointingHandCursor)
        self.btn_import_white.setObjectName("BtnSmall")
        self.btn_import_white.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_import_white.setFixedHeight(20)
        self.btn_import_white.setStyleSheet("min-height: 20px; padding-top: 1px; padding-bottom: 1px;")
        self.btn_import_white.clicked.connect(lambda: self._import_keywords_to(self.text_edit_whitelist))
        white_action_row.addWidget(self.btn_import_white)
        self.btn_clear_white = QPushButton(tr("dialog.filter.clear"))
        self.btn_clear_white.setCursor(Qt.PointingHandCursor)
        self.btn_clear_white.setObjectName("BtnSmall")
        self.btn_clear_white.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_clear_white.setFixedHeight(20)
        self.btn_clear_white.setStyleSheet("min-height: 20px; padding-top: 1px; padding-bottom: 1px;")
        self.btn_clear_white.clicked.connect(
            lambda: self._clear_keywords(self.text_edit_whitelist, tr("dialog.filter.whitelist_name"))
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
        hint.setStyleSheet(get_description_style())
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
        """按行拆分文本并去除空白，过滤掉空行。

        参数:
            text (str): 多行关键词文本。

        返回:
            list[str]: 非空关键词列表（已去掉首尾空白）。
        """
        return [line.strip() for line in text.split("\n") if line.strip()]

    def _collect_invalid_regex_rules(self):
        """扫描黑白名单编辑框，收集无法编译的正则表达式及其行号。

        返回:
            list[str]: 用户可读的无效正则提示消息列表；空列表表示全部合法。
        """
        invalid_rules = []
        rule_groups = [
            (
                tr("dialog.filter.blacklist_name"),
                self.text_edit_blacklist.toPlainText(),
            ),
            (
                tr("dialog.filter.whitelist_name"),
                self.text_edit_whitelist.toPlainText(),
            ),
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
        """经二次确认后清空指定编辑框中的全部关键词。

        参数:
            target_edit: 待清空的黑/白名单编辑框。
            list_name (str): 用于提示消息中的列表名称（如 ``"黑名单"``）。
        """
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
        """通过文件选择对话框打开文本文件，并覆盖导入到指定编辑框。

        自动检测 UTF-8-BOM 或 GBK 编码，兼容中文 Windows 导出的文本文件。

        参数:
            target_edit: 目标黑/白名单编辑框。
        """
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
        """校验收并持久化过滤设置。

        如勾选了正则表达式模式，会先对黑白名单内容进行合法性校验：
        任一正则无效时弹出警告并不保存；全部合法则写入 ``cfg`` 并关闭对话框。
        """
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
        set_config_attr("filter_mode", self.button_group.checkedId())
        set_config_attr(
            "filter_blacklist",
            self._parse_keywords(self.text_edit_blacklist.toPlainText()),
        )
        set_config_attr(
            "filter_whitelist",
            self._parse_keywords(self.text_edit_whitelist.toPlainText()),
        )
        set_config_attr("filter_use_regex", self.chk_use_regex.isChecked())
        self.accept()
