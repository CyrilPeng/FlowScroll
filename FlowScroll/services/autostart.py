import sys
import os
from FlowScroll.platform import system_platform, OS_NAME


class AutoStartManager:
    """跨平台开机自启动管理封装。"""

    def __init__(self) -> None:
        self.app_name: str = "FlowScroll"
        if getattr(sys, "frozen", False):
            self.app_path: str = os.path.abspath(sys.executable)
        else:
            script_path = os.path.abspath(sys.argv[0])
            if OS_NAME == "Windows":
                # Windows 的 Run 注册表项需要可直接执行的完整命令。
                python_path = os.path.abspath(sys.executable)
                self.app_path = f'"{python_path}" "{script_path}"'
            else:
                # 开发环境下通常不会真正注册自启动，这里指向入口脚本。
                self.app_path = script_path

    def is_autorun(self) -> bool:
        return system_platform.is_autostart_enabled(self.app_name, self.app_path)

    def set_autorun(self, enable: bool) -> bool:
        return system_platform.set_autostart(self.app_name, self.app_path, enable)
