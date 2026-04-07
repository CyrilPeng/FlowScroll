import os
import plistlib
import shlex
import subprocess
from FlowScroll.platform.base import PlatformInterface
from FlowScroll.services.logging_service import logger
from FlowScroll.constants import MACOS_SCROLL_MULTIPLIER


class MacOSPlatform(PlatformInterface):
    def __init__(self):
        self.label = "com.cyrilpeng.flowscroll"
        self.plist_path = os.path.expanduser(
            f"~/Library/LaunchAgents/{self.label}.plist"
        )

    def get_frontmost_window_info(self):
        try:
            script = 'tell application "System Events" to get name of first application process whose frontmost is true'
            res = subprocess.run(
                ["osascript", "-e", script], capture_output=True, text=True
            )
            process_name = res.stdout.strip()
            # macOS暂不实现精确全屏和类名探测
            return ("", process_name, "", False)
        except Exception as e:
            logger.debug(f"获取 macOS 前台窗口失败: {e}")
            return ("", "", "", False)

    def set_autostart(self, app_name, app_path, enable) -> bool:
        if enable:
            try:
                os.makedirs(os.path.dirname(self.plist_path), exist_ok=True)
                program_args = []
                if app_path:
                    if app_path.startswith('"'):
                        program_args = shlex.split(app_path)
                    else:
                        program_args = [app_path]
                if not program_args:
                    return False
                plist_content = {
                    "Label": self.label,
                    "ProgramArguments": program_args,
                    "RunAtLoad": True,
                    "KeepAlive": False,
                }
                with open(self.plist_path, "wb") as f:
                    plistlib.dump(plist_content, f)
                return True
            except Exception as e:
                logger.error(f"设置 macOS 开机自启失败: {e}")
                return False
        else:
            try:
                if os.path.exists(self.plist_path):
                    os.remove(self.plist_path)
                return True
            except Exception as e:
                logger.error(f"移除 macOS 开机自启失败: {e}")
                return False

    def is_autostart_enabled(self, app_name, app_path):
        return os.path.exists(self.plist_path)

    def get_scroll_multiplier(self):
        return MACOS_SCROLL_MULTIPLIER

    def get_font_name(self) -> str:
        return ".AppleSystemUIFont"

    def get_icon_name(self):
        return os.path.join("FlowScroll", "resources", "FlowScroll.svg")
