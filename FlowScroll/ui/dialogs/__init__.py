"""FlowScroll 对话框模块包。

将原单体文件 ``dialogs.py``（874 行）拆分为 5 个独立子模块，
按功能职责分类以便独立维护与单元测试。通过 :data:`__all__`
统一导出，外部仍以 ``from FlowScroll.ui.dialogs import XxxDialog`` 使用。

子模块索引:
    * :mod:`reverse_mode <FlowScroll.ui.dialogs.reverse_mode>`:
      :class:`ReverseModeDialog` —— 滚动方向反转（X/Y 轴）。
    * :mod:`work_mode <FlowScroll.ui.dialogs.work_mode>`:
      :class:`WorkModeDialog` —— 激活模式（点击/长按）与延迟启动。
    * :mod:`app_filter <FlowScroll.ui.dialogs.app_filter>`:
      :class:`AppFilterDialog` —— 应用过滤（黑/白名单 + 正则）。
    * :mod:`inertia <FlowScroll.ui.dialogs.inertia>`:
      :class:`InertiaSettingsDialog` —— 惯性滚动的摩擦力与触发阈值。
    * :mod:`config_storage <FlowScroll.ui.dialogs.config_storage>`:
      :class:`ConfigStorageDialog` —— 配置文件的存储路径。
"""

from FlowScroll.ui.dialogs.app_filter import AppFilterDialog
from FlowScroll.ui.dialogs.config_storage import ConfigStorageDialog
from FlowScroll.ui.dialogs.inertia import InertiaSettingsDialog
from FlowScroll.ui.dialogs.reverse_mode import ReverseModeDialog
from FlowScroll.ui.dialogs.work_mode import WorkModeDialog

__all__ = [
    "AppFilterDialog",
    "ConfigStorageDialog",
    "InertiaSettingsDialog",
    "ReverseModeDialog",
    "WorkModeDialog",
]
