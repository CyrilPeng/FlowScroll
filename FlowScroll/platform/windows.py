import ctypes
import os
import winreg
from ctypes import wintypes

from FlowScroll.constants import WINDOWS_SCROLL_MULTIPLIER
from FlowScroll.platform.base import PlatformInterface
from FlowScroll.services.logging_service import logger


class WindowsPlatform(PlatformInterface):
    def __init__(self):
        self.screen_width = 0
        self.screen_height = 0
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
            kernel32 = ctypes.windll.kernel32
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return ("", "", "", False)

            length = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            window_name = buf.value

            process_name = ""
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value:
                process_handle = kernel32.OpenProcess(0x1000, False, pid.value)
                if process_handle:
                    try:
                        image_buf = ctypes.create_unicode_buffer(1024)
                        image_len = wintypes.DWORD(len(image_buf))
                        if kernel32.QueryFullProcessImageNameW(
                            process_handle, 0, image_buf, ctypes.byref(image_len)
                        ):
                            process_name = os.path.splitext(
                                os.path.basename(image_buf.value)
                            )[0]
                    finally:
                        kernel32.CloseHandle(process_handle)

            class_buf = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, class_buf, 256)
            window_class = class_buf.value

            rect = wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))

            hmonitor = user32.MonitorFromWindow(hwnd, 2)

            class MONITORINFO(ctypes.Structure):
                _fields_ = [
                    ("cbSize", ctypes.c_ulong),
                    ("rcMonitor", wintypes.RECT),
                    ("rcWork", wintypes.RECT),
                    ("dwFlags", ctypes.c_ulong),
                ]

            mi = MONITORINFO()
            mi.cbSize = ctypes.sizeof(MONITORINFO)
            user32.GetMonitorInfoW(hmonitor, ctypes.byref(mi))

            # 仅当窗口区域覆盖整个显示器时才视为全屏。
            is_fullscreen = (
                rect.left <= mi.rcMonitor.left
                and rect.top <= mi.rcMonitor.top
                and rect.right >= mi.rcMonitor.right
                and rect.bottom >= mi.rcMonitor.bottom
            )

            # 排除普通最大化窗口，避免误判为全屏。
            if is_fullscreen:
                style = user32.GetWindowLongW(hwnd, -16)
                is_maximized = bool(style & 0x01000000)

                if is_maximized:
                    monitor_h = mi.rcMonitor.bottom - mi.rcMonitor.top
                    window_h = rect.bottom - rect.top
                    if window_h != monitor_h:
                        is_fullscreen = False

            return (window_name, process_name, window_class, is_fullscreen)
        except Exception as e:
            logger.debug(f"获取 Windows 前台窗口失败: {e}")
            return ("", "", "", False)

    def set_autostart(self, app_name, app_path, enable) -> bool:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS
            ) as key:
                if enable:
                    command = self._build_startup_command(app_path)
                    winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, command)
                else:
                    try:
                        winreg.DeleteValue(key, app_name)
                    except FileNotFoundError:
                        pass
            return True
        except Exception as e:
            logger.error(f"设置开机自启失败: {e}")
            return False

    def is_autostart_enabled(self, app_name, app_path):
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ
            ) as key:
                value, _ = winreg.QueryValueEx(key, app_name)
            saved_executable = self._normalize_path(self._extract_executable(value))
            expected_executable = self._normalize_path(self._extract_executable(app_path))
            return bool(saved_executable) and saved_executable == expected_executable
        except FileNotFoundError:
            return False
        except Exception as e:
            logger.debug(f"is_autostart_enabled check failed: {e}")
            return False

    @staticmethod
    def _normalize_path(path):
        if not path:
            return ""
        return os.path.normcase(os.path.normpath(path.strip().strip('"')))

    @staticmethod
    def _extract_executable(command):
        if not command:
            return ""
        cmd = command.strip()
        if not cmd:
            return ""
        if cmd[0] == '"':
            end_quote = cmd.find('"', 1)
            return cmd[1:end_quote] if end_quote > 0 else cmd[1:]
        return cmd.split(" ", 1)[0]

    @staticmethod
    def _build_startup_command(app_path):
        cmd = (app_path or "").strip()
        if not cmd:
            return cmd
        if '"' in cmd:
            return cmd
        if " " in cmd:
            return f'"{cmd}"'
        return cmd

    def get_scroll_multiplier(self):
        return WINDOWS_SCROLL_MULTIPLIER

    def get_font_name(self) -> str:
        return "Segoe UI"

    def get_icon_name(self):
        return os.path.join("FlowScroll", "resources", "FlowScroll.svg")
