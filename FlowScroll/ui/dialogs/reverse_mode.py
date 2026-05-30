"""滚动方向反转设置对话框。

提供反转纵向（Y 轴）和横向（X 轴）滚动方向的界面。
当用户勾选某一项后点击保存，会将对应的 ``cfg.reverse_y`` 或 ``cfg.reverse_x``
标志写入全局配置并持久化。

典型用法::

    dialog = ReverseModeDialog(parent_window)
    if dialog.exec():
        # cfg.reverse_y / reverse_x 已被更新
        pass
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QCheckBox,
    QPushButton,
)
from PySide6.QtCore import Qt

from FlowScroll.core.config import cfg, set_config_attr
from FlowScroll.i18n import tr
from FlowScroll.ui.helpers import create_card, create_h_line
from FlowScroll.ui.styles import (
    get_dialog_stylesheet,
    get_checkbox_style,
)
from FlowScroll.constants import (
    REVERSE_DIALOG_WIDTH,
    REVERSE_DIALOG_HEIGHT,
)


class ReverseModeDialog(QDialog):
    """滚动方向反转设置对话框。

    属性:
        chk_reverse_y (QCheckBox): 反转纵向滚动的复选框。
        chk_reverse_x (QCheckBox): 反转横向滚动的复选框。
    """

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
        """将勾选状态写入配置并以 DialogResult.Accepted 关闭对话框。"""
        set_config_attr("reverse_y", self.chk_reverse_y.isChecked())
        set_config_attr("reverse_x", self.chk_reverse_x.isChecked())
        self.accept()
