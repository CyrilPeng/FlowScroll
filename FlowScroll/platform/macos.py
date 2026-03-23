import os
import plistlib
import subprocess
from FlowScroll.platform.base import PlatformInterface
from FlowScroll.services.logging_service import logger


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
            window_name = res.stdout.strip()
            # macOS暂不实现精确全屏和类名探测
            return (window_name, "", False)
        except Exception as e:
            logger.debug(f"获取 macOS 前台窗口失败: {e}")
            return ("", "", False)

    def set_autostart(self, app_name, app_path, enable):
        if enable:
            try:
                os.makedirs(os.path.dirname(self.plist_path), exist_ok=True)
                plist_content = {
                    "Label": self.label,
                    "ProgramArguments": [app_path],
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
        return 0.0001

    def get_font_name(self):
        return ".AppleSystemUIFont"

    def get_icon_name(self):
        return "logo.icns"
