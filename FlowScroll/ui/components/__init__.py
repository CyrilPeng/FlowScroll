"""FlowScroll UI 组件包。

将原单体文件 ``components.py``（270 行）拆分为三个独立子模块，
按交互形态（输入 / 控制 / 可视化）分类。通过 :data:`__all__`
统一导出，外部仍以 ``from FlowScroll.ui.components import Xxx`` 使用。

子模块索引:
    * :mod:`input <FlowScroll.ui.components.input>`:
      :class:`HotkeyEdit`, :class:`UpwardComboBox` —— 接收键盘/鼠标输入的控件。
    * :mod:`controls <FlowScroll.ui.components.controls>`:
      :class:`NoWheelSlider`, :class:`NoWheelSpinBox` —— 屏蔽鼠标滚轮的微调控件。
    * :mod:`visualization <FlowScroll.ui.components.visualization>`:
      :class:`SpeedCurveWidget` —— 实时速度曲线可视化组件。
"""

from FlowScroll.ui.components.input import HotkeyEdit, UpwardComboBox
from FlowScroll.ui.components.controls import NoWheelSlider, NoWheelSpinBox
from FlowScroll.ui.components.visualization import SpeedCurveWidget

__all__ = [
    "HotkeyEdit",
    "UpwardComboBox",
    "NoWheelSlider",
    "NoWheelSpinBox",
    "SpeedCurveWidget",
]
