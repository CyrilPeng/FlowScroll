import os
import shlex
import sys

from FlowScroll.platform import OS_NAME, system_platform


class AutoStartManager:
    """跨平台开机自启动管理封装。"""

    def __init__(self) -> None:
        self.app_name: str = "FlowScroll"
        script_path = os.path.abspath(sys.argv[0])
        self.app_path: str = self._build_launch_command(script_path)

    def _build_launch_command(self, script_path: str) -> str:
        """构建自启动命令：可执行文件路径 + --silent 参数。"""
        if getattr(sys, "frozen", False):
            executable_path = os.path.abspath(sys.executable)
            if OS_NAME == "Windows":
                return f"{self._quote_path(executable_path)} --silent"
            return f"{shlex.quote(executable_path)} --silent"

        if OS_NAME == "Windows" and script_path.lower().endswith(".exe"):
            return f"{self._quote_path(script_path)} --silent"
        return self._build_source_launch_command(script_path)

    @staticmethod
    def _build_source_launch_command(script_path: str) -> str:
        python_path = os.path.abspath(sys.executable)
        if OS_NAME == "Windows":
            return f'"{python_path}" "{script_path}" --silent'
        return f"{shlex.quote(python_path)} {shlex.quote(script_path)} --silent"

    @staticmethod
    def _quote_path(path: str) -> str:
        return f'"{path}"'

    def is_autorun(self) -> bool:
        return system_platform.is_autostart_enabled(self.app_name, self.app_path)

    def set_autorun(self, enable: bool) -> bool:
        return system_platform.set_autostart(self.app_name, self.app_path, enable)
