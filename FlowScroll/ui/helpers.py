import os
from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QLabel,
    QDoubleSpinBox,
    QSlider,
    QCheckBox,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from FlowScroll.ui.utils import resource_path

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
    layout, key, icon_name, label_text, val, min_v, max_v, callback, decimals=1
):
    row = QWidget()
    row_layout = QVBoxLayout(row)
    row_layout.setContentsMargins(0, 0, 0, 0)
    row_layout.setSpacing(12)

    top_layout = QHBoxLayout()
    top_layout.setSpacing(8)

    if icon_name:
        icon_lbl = QLabel()
        icon_path = resource_path(
            os.path.join("FlowScroll", "resources", icon_name)
        )
        if os.path.exists(icon_path):
            pixmap = QIcon(icon_path).pixmap(QSize(18, 18))
            icon_lbl.setPixmap(pixmap)
        top_layout.addWidget(icon_lbl)

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
    return spin

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

    row_layout.addWidget(chk)
    row_layout.addStretch()
    if extra_widget:
        row_layout.addWidget(extra_widget)

    layout.addWidget(row)
    return chk
