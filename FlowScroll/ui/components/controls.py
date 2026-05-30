"""控制类组件：屏蔽鼠标滚轮交互的微调控件。

当 FlowScroll 主界面中的 ``QSlider`` / ``QDoubleSpinBox`` 已经通过
拖动或键盘调整时，用户的鼠标滚轮在同一个控件上操作容易导致数值意外
变动。本模块提供两个基类，分别屏蔽 ``wheelEvent``，使这些控件只响应
拖动、点击或键盘输入。

典型用法::

    from FlowScroll.ui.components import NoWheelSlider, NoWheelSpinBox

    slider = NoWheelSlider(Qt.Horizontal, parent)
    spinbox = NoWheelSpinBox(parent)
"""

from PySide6.QtWidgets import QDoubleSpinBox, QSlider


class NoWheelSlider(QSlider):
    """屏蔽鼠标滚轮事件的滑块控件。

    继承 :class:`QSlider`，仅重写 :meth:`wheelEvent` 调用 ``event.ignore()``，
    使滚轮事件透传到父级滚动容器（如 ``QScrollArea``），避免在垂直滚动
    页面时误触数值变更。
    """

    def wheelEvent(self, event) -> None:
        """忽略滚轮事件，让其透传至上层容器。"""
        event.ignore()


class NoWheelSpinBox(QDoubleSpinBox):
    """屏蔽鼠标滚轮事件的数值输入框。

    继承 :class:`QDoubleSpinBox`，仅重写 :meth:`wheelEvent` 调用 ``event.ignore()``，
    与 :class:`NoWheelSlider` 配套使用，常见于参数调校卡片中成对出现。
    """

    def wheelEvent(self, event) -> None:
        """忽略滚轮事件，让其透传至上层容器。"""
        event.ignore()
