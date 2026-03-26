import time
import threading
from FlowScroll.core.config import cfg
from FlowScroll.platform import system_platform
from FlowScroll.services.logging_service import logger
from FlowScroll.constants import (
    WINDOW_MONITOR_START_DELAY,
    WINDOW_MONITOR_POLL_INTERVAL,
)


class WindowMonitor(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)

    def run(self):
        time.sleep(WINDOW_MONITOR_START_DELAY)
        while True:
            try:
                name, cls_name, is_fullscreen = (
                    system_platform.get_frontmost_window_info()
                )
                cfg.current_window_name = name
                cfg.current_window_class = cls_name
                cfg.is_fullscreen = is_fullscreen
            except Exception as e:
                logger.debug(f"WindowMonitor error: {e}")
            time.sleep(WINDOW_MONITOR_POLL_INTERVAL)
