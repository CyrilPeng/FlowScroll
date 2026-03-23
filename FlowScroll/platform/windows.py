import ctypes
import winreg
from ctypes import wintypes
from FlowScroll.platform.base import PlatformInterface
from FlowScroll.services.logging_service import logger


class WindowsPlatform(PlatformInterface):
    def __init__(self):
        self.screen_width = 0
        self.screen_height = 0
        # 获取主屏幕分辨率 (粗略)
        try:
            from PySide6.QtWidgets import QApplication

            if QApplication.instance():
                screen_geom = QApplication.primaryScreen().geometry()
                self.screen_width = screen_geom.width()
                self.screen_height = screen_geom.height()
            else:
                user32 = ctypes.windll.user32
                self.screen_width = user32.GetSystemMetrics(0)
                self.screen_height = user32.GetSystemMetrics(1)
        except Exception as e:
            logger.warning(f"Windows 平台初始化屏幕尺寸失败: {e}")

    def get_frontmost_window_info(self):
        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return ("", "", False)

            length = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            window_name = buf.value

            class_buf = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, class_buf, 256)
            window_class = class_buf.value

            rect = wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            w = rect.right - rect.left
            h = rect.bottom - rect.top

            # 待办: 如果是多显示器，改进健壮的屏幕检测
            is_fullscreen = (
                (w >= self.screen_width and h >= self.screen_height)
                if self.screen_width
                else False
            )

            return (window_name, window_class, is_fullscreen)
        except Exception as e:
            logger.debug(f"获取 Windows 前台窗口失败: {e}")
            return ("", "", False)

    def set_autostart(self, app_name, app_path, enable):
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS
            )
            if enable:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
            return True
        except Exception as e:
            logger.error(f"设置开机自启失败: {e}")
            return False

    def is_autostart_enabled(self, app_name, app_path):
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, app_name)
            winreg.CloseKey(key)
            return value == app_path
        except:
            return False

    def get_scroll_multiplier(self):
        return 0.00005

    def get_font_name(self):
        return "Segoe UI"

    def get_icon_name(self):
        return "logo.ico"
