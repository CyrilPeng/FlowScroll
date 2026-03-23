import sys
import os
from FlowScroll.platform import system_platform


class AutoStartManager:
    """跨平台开机自启管理封装"""

    def __init__(self):
        self.app_name = "FlowScroll"
        if getattr(sys, "frozen", False):
            self.app_path = sys.executable
        else:
            # 开发环境下通常不建议真正开启自启，这里指向入口脚本
            self.app_path = os.path.abspath(sys.argv[0])

    def is_autorun(self):
        return system_platform.is_autostart_enabled(self.app_name, self.app_path)

    def set_autorun(self, enable):
        return system_platform.set_autostart(self.app_name, self.app_path, enable)
