from abc import ABC, abstractmethod
from typing import Tuple


class PlatformInterface(ABC):
    @abstractmethod
    def get_frontmost_window_info(self) -> Tuple[str, str, bool]:
        """
        获取当前前台窗口的信息。
        返回: (进程名/窗口名, 窗口类名, 是否全屏)
        """
        pass

    @abstractmethod
    def set_autostart(self, app_name: str, app_path: str, enable: bool) -> bool:
        """
        设置开机自启。
        返回: 成功与否的布尔值
        """
        pass

    @abstractmethod
    def is_autostart_enabled(self, app_name: str, app_path: str) -> bool:
        """
        检查是否已开启开机自启。
        返回: 布尔值
        """
        pass

    @abstractmethod
    def get_scroll_multiplier(self) -> float:
        """
        获取当前平台的滚动乘数。
        """
        pass

    @abstractmethod
    def get_font_name(self) -> str:
        """
        获取默认字体名
        """
        pass

    @abstractmethod
    def get_icon_name(self) -> str:
        """
        获取图标文件名
        """
        pass
