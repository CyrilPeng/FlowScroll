import platform

OS_NAME = platform.system()

if OS_NAME == "Windows":
    from FlowScroll.platform.windows import WindowsPlatform

    system_platform = WindowsPlatform()
elif OS_NAME == "Darwin":
    from FlowScroll.platform.macos import MacOSPlatform

    system_platform = MacOSPlatform()
else:
    # 暂时回退到空实现或Windows实现
    from FlowScroll.platform.base import PlatformInterface

    class NullPlatform(PlatformInterface):
        def get_frontmost_window_info(self):
            return ("", "", False)

        def set_autostart(self, a, p, e):
            return False

        def is_autostart_enabled(self, a, p):
            return False

        def get_scroll_multiplier(self):
            return 0.00005

        def get_font_name(self):
            return "sans-serif"

        def get_icon_name(self):
            return "logo.ico"

    system_platform = NullPlatform()
