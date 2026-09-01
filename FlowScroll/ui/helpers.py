import os
from typing import Callable

from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QLabel,
    QCheckBox,
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QIcon
from FlowScroll.ui.utils import resource_path
from FlowScroll.ui.components import NoWheelSlider, NoWheelSpinBox
from FlowScroll.ui.styles import get_section_label_style


# 全局防抖计时器列表：存储 (计时器, 回调函数) 元组，
# 防止被垃圾回收，窗口关闭时必须刷新。
_DEBOUNCE_TIMERS: list[tuple["QTimer", Callable]] = []


def _make_debounced(callback: Callable, delay_ms: int = 250) -> Callable:
    """将回调包装为防抖版本：在最后一次调用后延迟 delay_ms 毫秒才真正执行。

    用于滑块拖动等频繁连续值变化场景，避免每次微小变化都触发磁盘写入。
    """
    timer = QTimer()
    timer.setSingleShot(True)
    _DEBOUNCE_TIMERS.append((timer, callback))

    def _on_timeout():
        args = timer.property("args")
        if args is not None:
            callback(*args)

    timer.timeout.connect(_on_timeout)

    def debounced(*args):
        timer.setProperty("args", args)
        timer.start(delay_ms)

    return debounced


def _flush_all_debounced() -> None:
    """立即执行所有待执行的防抖回调并停止计时器。

    窗口关闭前必须调用，防止最后一次配置变更因防抖延迟而丢失。
    """
    for timer, callback in list(_DEBOUNCE_TIMERS):
        if timer.isActive():
            timer.stop()
            args = timer.property("args")
            if args is not None:
                callback(*args)
    _DEBOUNCE_TIMERS.clear()


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


def add_slider_row(layout, key, icon_name, label_text, val, min_v, max_v, callback, decimals: int = 1):
    row = QWidget()
    row_layout = QVBoxLayout(row)
    row_layout.setContentsMargins(0, 0, 0, 0)
    row_layout.setSpacing(12)

    top_layout = QHBoxLayout()
    top_layout.setSpacing(8)

    if icon_name:
        icon_lbl = QLabel()
        icon_path = resource_path(os.path.join("FlowScroll", "resources", icon_name))
        if os.path.exists(icon_path):
            pixmap = QIcon(icon_path).pixmap(QSize(18, 18))
            icon_lbl.setPixmap(pixmap)
        top_layout.addWidget(icon_lbl)

    lbl = QLabel(label_text)
    lbl.setStyleSheet(get_section_label_style())

    spin = NoWheelSpinBox()
    spin.setRange(min_v, max_v)
    spin.setValue(val)
    spin.setDecimals(decimals)
    spin.setSingleStep(1.0 / (10**decimals))
    spin.setFixedSize(70, 32)
    spin.setAlignment(Qt.AlignCenter)
    debounced_callback = _make_debounced(callback)
    spin.valueChanged.connect(debounced_callback)
    spin.setFocusPolicy(Qt.ClickFocus)

    top_layout.addWidget(lbl)
    top_layout.addStretch()
    top_layout.addWidget(spin)

    scale = 10**decimals
    slider = NoWheelSlider(Qt.Horizontal)
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
