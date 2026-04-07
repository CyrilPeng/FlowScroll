import threading
import time

from FlowScroll.constants import (
    WINDOW_INFO_FAILURE_STALE_THRESHOLD,
    WINDOW_MONITOR_POLL_INTERVAL,
    WINDOW_MONITOR_START_DELAY,
)
from FlowScroll.core.config import STATE_LOCK, runtime
from FlowScroll.platform import system_platform
from FlowScroll.services.logging_service import logger


class WindowMonitor(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)

    def run(self) -> None:
        time.sleep(WINDOW_MONITOR_START_DELAY)
        while True:
            try:
                window_name, process_name, cls_name, is_fullscreen = (
                    system_platform.get_frontmost_window_info()
                )
                with STATE_LOCK:
                    runtime.current_window_name = window_name
                    runtime.current_process_name = process_name
                    runtime.process_name_status = (
                        "available" if process_name else "unavailable"
                    )
                    runtime.last_match_target = (
                        process_name or window_name or ""
                    ).strip().lower()
                    runtime.current_window_class = cls_name
                    runtime.is_fullscreen = is_fullscreen
                    runtime.window_info_failure_count = 0
            except Exception as e:
                with STATE_LOCK:
                    runtime.window_info_failure_count += 1
                    if (
                        runtime.window_info_failure_count
                        >= WINDOW_INFO_FAILURE_STALE_THRESHOLD
                    ):
                        runtime.current_window_name = ""
                        runtime.current_process_name = ""
                        runtime.current_window_class = ""
                        runtime.is_fullscreen = False
                        runtime.last_match_target = ""
                        runtime.process_name_status = "stale"
                logger.debug(f"WindowMonitor error: {e}")
            time.sleep(WINDOW_MONITOR_POLL_INTERVAL)
