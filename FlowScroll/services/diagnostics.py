import time
import threading
from FlowScroll.core.config import cfg
from FlowScroll.platform import system_platform


class WindowMonitor(threading.Thread):
    """窗口状态监控，定期检测当前前台窗口信息"""

    def __init__(self):
        super().__init__(daemon=True)

    def run(self):
        # 延迟启动，避免与启动流程争抢资源
        time.sleep(2)
        while True:
            try:
                name, cls_name, is_fullscreen = (
                    system_platform.get_frontmost_window_info()
                )
                cfg.current_window_name = name
                cfg.current_window_class = cls_name
                cfg.is_fullscreen = is_fullscreen
            except Exception:
                pass
            time.sleep(0.5)
