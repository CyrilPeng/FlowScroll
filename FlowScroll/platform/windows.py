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

            # 获取窗口所在的显示器信息
            HMONITOR = user32.MonitorFromWindow(hwnd, 2) # MONITOR_DEFAULTTONEAREST
            
            class MONITORINFO(ctypes.Structure):
                _fields_ = [
                    ('cbSize', ctypes.c_ulong),
                    ('rcMonitor', wintypes.RECT),
                    ('rcWork', wintypes.RECT),
                    ('dwFlags', ctypes.c_ulong)
                ]
            
            mi = MONITORINFO()
            mi.cbSize = ctypes.sizeof(MONITORINFO)
            user32.GetMonitorInfoW(HMONITOR, ctypes.byref(mi))

            # 判断真正的全屏：
            # 1. 窗口区域必须大于或等于整个显示器区域（rcMonitor）。
            is_fullscreen = (
                rect.left <= mi.rcMonitor.left and
                rect.top <= mi.rcMonitor.top and
                rect.right >= mi.rcMonitor.right and
                rect.bottom >= mi.rcMonitor.bottom
            )
            
            # 2. 排除普通的“最大化”窗口：
            # 在 Windows 中，带有边框的普通窗口最大化时，系统为了隐藏边框，会让它稍微“溢出”显示器。
            # 但它的有效显示区域（不包含被切掉的边框）实际上只覆盖了“工作区（rcWork）”，而把任务栏留了出来。
            # 所以，如果当前显示器有任务栏（即工作区高度 < 显示器高度），
            # 而窗口的实际高度不足以覆盖整个显示器加上边框溢出量时，它并不是真正的全屏（比如 F11 或 游戏）。
            if is_fullscreen:
                style = user32.GetWindowLongW(hwnd, -16) # GWL_STYLE
                is_maximized = bool(style & 0x01000000) # WS_MAXIMIZE
                
                if is_maximized:
                    # 比较窗口高度与全屏高度
                    monitor_h = mi.rcMonitor.bottom - mi.rcMonitor.top
                    window_h = rect.bottom - rect.top
                    
                    # 很多有边框的普通窗口最大化后，其尺寸大约是 工作区高度 + 16 (边框)
                    # 真正的 F11 全屏/独占全屏尺寸通常刚好等于 显示器高度，或者是 显示器高度 + 更少的边框溢出，并且没有 WS_MAXIMIZE 样式，或者全屏后覆盖了任务栏。
                    # 如果窗口并没有比整个屏幕高度大出明显的边框，或者它的位置受到了任务栏的挤压，这就不是全屏。
                    # 最保险的判定：大多数真全屏应用（包括无边框窗口）尺寸严格等于 Monitor 尺寸。
                    if window_h != monitor_h:
                        # 有些最大化窗口由于边框溢出，可能比 monitor_h 还大，但如果是最大化且有任务栏，那么底部通常在 rcWork.bottom 附近或者更下面一点。
                        # 我们通过检查窗口是否遮挡了整个屏幕来判断：如果屏幕有任务栏，普通最大化绝不会覆盖它。
                        is_fullscreen = False

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
