import platform
from FlowScroll.constants import DEFAULT_SCROLL_MULTIPLIER
from FlowScroll.platform.base import PlatformInterface

OS_NAME = platform.system()
system_platform: PlatformInterface

if OS_NAME == "Windows":
    from FlowScroll.platform.windows import WindowsPlatform

    system_platform = WindowsPlatform()
elif OS_NAME == "Darwin":
    from FlowScroll.platform.macos import MacOSPlatform

    system_platform = MacOSPlatform()
elif OS_NAME == "Linux":
    from FlowScroll.platform.linux import LinuxPlatform

    system_platform = LinuxPlatform()
else:
    # 暂时回退到空实现或Windows实现
    class NullPlatform(PlatformInterface):
        def get_frontmost_window_info(self):
            return ("", "", "", False)

        def set_autostart(self, a, p, e):
            return False

        def is_autostart_enabled(self, a, p):
            return False

        def get_scroll_multiplier(self):
            return DEFAULT_SCROLL_MULTIPLIER

        def get_font_name(self):
            return "sans-serif"

        def get_icon_name(self):
            return "FlowScroll/resources/FlowScroll.svg"

    system_platform = NullPlatform()
