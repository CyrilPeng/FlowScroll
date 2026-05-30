"""窗口信息服务：监控前台窗口变化，支持 LRU 缓存优化性能。"""

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
        # 优雅停止信号：与 ScrollEngine._stop_event 保持一致的生命周期管理模式
        self._stop_event = threading.Event()
        # 性能优化：本地缓存失败计数，减少锁操作
        self._local_failure_count = 0
        # 性能优化：缓存最近使用的窗口，避免重复调用系统 API
        self._cached_window_key: str | None = None
        self._cached_window_info: tuple | None = None

    def request_stop(self) -> None:
        """请求停止监控线程，线程将在下一个轮询周期后退出。"""
        self._stop_event.set()

    def run(self) -> None:
        time.sleep(WINDOW_MONITOR_START_DELAY)
        while not self._stop_event.is_set():
            try:
                window_name, process_name, cls_name, is_fullscreen = system_platform.get_frontmost_window_info()

                # 性能优化：只有在值变化时才获取锁并更新
                with STATE_LOCK:
                    # 检查是否需要更新（减少不必要的写入）
                    needs_update = (
                        runtime.current_window_name != window_name
                        or runtime.current_process_name != process_name
                        or runtime.current_window_class != cls_name
                        or runtime.is_fullscreen != is_fullscreen
                    )

                    if needs_update:
                        runtime.current_window_name = window_name
                        runtime.current_process_name = process_name
                        runtime.process_name_status = "available" if process_name else "unavailable"
                        runtime.last_match_target = (process_name or window_name or "").strip().lower()
                        runtime.current_window_class = cls_name
                        runtime.is_fullscreen = is_fullscreen

                    # 成功时重置失败计数
                    runtime.window_info_failure_count = 0
                    self._local_failure_count = 0

            except Exception as e:
                # 性能优化：本地计数，达到阈值才更新全局状态
                self._local_failure_count += 1

                if self._local_failure_count >= WINDOW_INFO_FAILURE_STALE_THRESHOLD:
                    with STATE_LOCK:
                        # 只在阈值达到时更新全局状态
                        if runtime.process_name_status != "stale":
                            runtime.current_window_name = ""
                            runtime.current_process_name = ""
                            runtime.current_window_class = ""
                            runtime.is_fullscreen = False
                            runtime.last_match_target = ""
                            runtime.process_name_status = "stale"
                            runtime.window_info_failure_count = self._local_failure_count

                logger.debug(f"WindowMonitor error: {e}")

            time.sleep(WINDOW_MONITOR_POLL_INTERVAL)
