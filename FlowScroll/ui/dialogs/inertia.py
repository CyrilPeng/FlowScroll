"""惯性滚动设置对话框（摩擦力、触发阈值）。

当惯性滚动功能启用时，用户释放滚动操作后内容会继续滑行一段
距离并逐渐停下。本对话框调整以下两个核心参数：

* **摩擦力（半衰期）**：滑块取值 100–3000ms。值越大，惯性持续越久，
  滑行距离越远（"松弛"手感）。
* **触发阈值**：滑块取值 30–300 px/s。只有释放瞬间的滚动速度超过此
  阈值时，才会启动惯性滑行；低于该值则直接停止，避免轻微拖动也产生
  惯性。

数值会随滑块拖动实时刷新到标签，便于直观评估。保存后写入 ``cfg``
并持久化。
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
)
from PySide6.QtCore import Qt

from FlowScroll.core.config import cfg, set_config_attr
from FlowScroll.i18n import tr
from FlowScroll.ui.helpers import create_card
from FlowScroll.ui.styles import (
    get_dialog_stylesheet,
    get_slider_style,
    get_value_label_style,
    get_hint_label_style,
    get_dialog_title_style,
    get_dialog_subtitle_style,
    get_card_label_style,
)
from FlowScroll.constants import (
    INERTIA_DIALOG_WIDTH,
    INERTIA_DIALOG_HEIGHT,
)


class InertiaSettingsDialog(QDialog):
    """惯性滚动的摩擦力与触发阈值设置对话框。

    属性:
        friction_slider (QSlider): 摩擦力半衰期滑块（100–3000 ms）。
        friction_value_label (QLabel): 摩擦力当前数值的显示标签。
        threshold_slider (QSlider): 触发阈值滑块（30–300 px/s）。
        threshold_value_label (QLabel): 触发阈值当前数值的显示标签。
    """

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
        title.setStyleSheet(get_dialog_title_style())
        subtitle = QLabel(tr("dialog.inertia.subtitle"))
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(get_dialog_subtitle_style())
        layout.addWidget(title)
        layout.addWidget(subtitle)

        card1, card_layout1 = create_card()
        card1.setStyleSheet(card1.styleSheet() + f"QLabel{{{get_card_label_style()}}}")
        card_layout1.setContentsMargins(16, 16, 16, 16)
        card_layout1.setSpacing(10)

        friction_header = QHBoxLayout()
        friction_title = QLabel(tr("dialog.inertia.friction_title"))
        friction_title.setStyleSheet(get_card_label_style())
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
        card2.setStyleSheet(card2.styleSheet() + f"QLabel{{{get_card_label_style()}}}")
        card_layout2.setContentsMargins(16, 16, 16, 16)
        card_layout2.setSpacing(10)

        threshold_header = QHBoxLayout()
        threshold_title = QLabel(tr("dialog.inertia.threshold_title"))
        threshold_title.setStyleSheet(get_card_label_style())
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
        """刷新摩擦力标签，显示当前滑块值（单位 ms）。"""
        ms = self.friction_slider.value()
        self.friction_value_label.setText(f"{ms} ms")

    def _update_threshold_label(self):
        """刷新触发阈值标签，显示当前滑块值（单位 px/s）。"""
        val = self.threshold_slider.value()
        self.threshold_value_label.setText(f"{val} px/s")

    def _on_friction_changed(self, _value):
        """滑块拖动回调：转发至 :meth:`_update_friction_label`。"""
        self._update_friction_label()

    def _on_threshold_changed(self, _value):
        """滑块拖动回调：转发至 :meth:`_update_threshold_label`。"""
        self._update_threshold_label()

    def save_and_close(self) -> None:
        """将惯性参数写入配置并关闭对话框。"""
        set_config_attr("inertia_friction_ms", self.friction_slider.value())
        set_config_attr("inertia_threshold", float(self.threshold_slider.value()))
        self.accept()
