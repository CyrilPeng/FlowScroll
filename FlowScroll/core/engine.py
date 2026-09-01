import math
import os
import time
import threading
from collections import deque
from types import SimpleNamespace
from FlowScroll.core.config import STATE_LOCK, cfg, runtime, config_bus
from FlowScroll.core.scroller import default_scroll_strategy
from FlowScroll.platform import system_platform
from FlowScroll.services.logging_service import logger
from FlowScroll.constants import (
    ENGINE_TICK_INTERVAL,
    ENGINE_IDLE_POLL_INTERVAL,
    INERTIA_STOP_THRESHOLD,
    SCROLL_HISTORY_WINDOW,
)


def _request_windows_timer_precision():
    """Windows 下请求 1ms 定时器精度，避免默认 15.6ms 分辨率导致 4ms tick 抖动。

    timeBeginPeriod(1) 仅影响本进程的定时器调度精度，
    让 time.sleep(0.004) 更接近真实的 4ms 而非 0-16ms 随机值。
    这对滚动平滑度有直接影响。
    """
    if os.name != "nt":
        return False
    try:
        import ctypes

        winmm = ctypes.windll.winmm
        winmm.timeBeginPeriod(1)
        return True
    except Exception:
        return False


def _release_windows_timer_precision():
    """释放 Windows 定时器精度请求，避免长期占用高精度定时器。"""
    if os.name != "nt":
        return
    try:
        import ctypes

        ctypes.windll.winmm.timeEndPeriod(1)
    except Exception:
        pass


class ScrollEngine(threading.Thread):
    """滚动引擎线程：根据鼠标偏移计算滚动速度，支持惯性衰减。"""

    def __init__(self, bridge, mouse_controller):
        """初始化滚动引擎，绑定桥接器与鼠标控制器，设置惯性参数和历史记录。"""
        super().__init__(daemon=True)
        self.bridge = bridge
        self.mouse_controller = mouse_controller
        self.strategy = default_scroll_strategy
        self._stop_event = threading.Event()
        # Windows 高精度定时器：请求 1ms 精度以保证 4ms tick 稳定性
        self._windows_timer_precision_active = _request_windows_timer_precision()

        # 惯性状态。
        self.inertia_active = False
        self.inertia_vx = 0.0
        self.inertia_vy = 0.0
        with STATE_LOCK:
            self.friction = self._compute_friction(cfg.inertia_friction_ms)

        # 订阅 inertia_friction_ms 变更，配置更新时自动重算摩擦系数
        config_bus.subscribe("inertia_friction_ms", self._on_friction_config_changed)

        # 浮点滚动累积器：pynput 在 Windows 将浮点截断为整数，
        # 导致低速滚动丢失精度。累积小数部分，达到 1.0 时才实际发送整数滚动。
        self._scroll_accum_x = 0.0
        self._scroll_accum_y = 0.0

        # 滚动速度历史，用于估算惯性初速度。
        self._inertia_lock = threading.Lock()

        self._scroll_history: deque = deque()
        self._scroll_history_window = SCROLL_HISTORY_WINDOW

        # 鼠标位置历史，用于计算触发惯性的速度阈值。
        self._mouse_pos_history: deque = deque()

        # 保护历史记录的专用锁，避免 engine 线程追加/裁剪与
        # interrupt_inertia 的 clear 产生竞态。
        self._history_lock = threading.Lock()

    @staticmethod
    def _compute_friction(half_life_ms):
        """将半衰期毫秒值换算为每帧的摩擦系数。"""
        if half_life_ms <= 0:
            return 0.9
        ticks = half_life_ms / (ENGINE_TICK_INTERVAL * 1000)
        return math.pow(0.5, 1.0 / ticks)

    def update_friction(self) -> None:
        """配置变化后重新计算摩擦系数。

        .. deprecated::
            保留向后兼容；新代码应依赖 config_bus 订阅机制，
            当 cfg.inertia_friction_ms 变化时自动触发重算。
        """
        with STATE_LOCK:
            self.friction = self._compute_friction(cfg.inertia_friction_ms)

    def _on_friction_config_changed(self, new_value) -> None:
        """config_bus 订阅回调：friction_ms 变化时重算摩擦系数。"""
        with self._inertia_lock:
            self.friction = self._compute_friction(new_value)

    def interrupt_inertia(self) -> None:
        """立即中断惯性滚动，并清空速度与位置历史。"""
        with self._inertia_lock:
            if self.inertia_active:
                self.inertia_active = False
                self.inertia_vx = 0.0
                self.inertia_vy = 0.0
            # 重置滚动累积器，避免上次残留的余数影响下次激活
            self._scroll_accum_x = 0.0
            self._scroll_accum_y = 0.0
        with self._history_lock:
            self._scroll_history.clear()
            self._mouse_pos_history.clear()

    def _prune_history(self, history, now):
        """清理超出时间窗口的历史记录，使用 deque.popleft 实现 O(1) 裁剪。"""
        cutoff = now - self._scroll_history_window
        while history and history[0][0] < cutoff:
            history.popleft()

    def _get_weighted_velocity_from_history(self):
        """使用指数时间加权平均计算滚动速度向量。

        比"取最大速度帧"更稳定：近期帧权重更高，避免快速抖动
        时产生不自然的惯性爆发，让惯性初速度更贴近拖动末期趋势。

        衰减常数 50ms，与 SCROLL_HISTORY_WINDOW(100ms) 配合后，
        早期帧权重已可忽略。
        """
        if not self._scroll_history:
            return 0.0, 0.0

        decay = 0.05  # 秒
        now = self._scroll_history[-1][0]
        vx_weighted = 0.0
        vy_weighted = 0.0
        total_weight = 0.0

        for ts, vx, vy in self._scroll_history:
            age = max(0.0, now - ts)
            weight = math.exp(-age / decay)
            vx_weighted += vx * weight
            vy_weighted += vy * weight
            total_weight += weight

        if total_weight < 1e-9:
            return 0.0, 0.0

        return vx_weighted / total_weight, vy_weighted / total_weight

    def _get_mouse_speed_px_per_s(self):
        """计算最近时间窗口内鼠标的平均移动速度，单位 px/s。"""
        if len(self._mouse_pos_history) < 2:
            return 0.0

        first = self._mouse_pos_history[0]
        last = self._mouse_pos_history[-1]
        dt = last[0] - first[0]
        if dt <= 0:
            return 0.0

        dist = math.hypot(last[1] - first[1], last[2] - first[2])
        return dist / dt

    def _try_enter_inertia(self):
        """尝试从激活状态切换到惯性模式。所有历史读写均在 _history_lock 下原子执行。"""
        with STATE_LOCK:
            enable_inertia = cfg.enable_inertia
            inertia_threshold = cfg.inertia_threshold
        if not enable_inertia:
            with self._history_lock:
                self._scroll_history.clear()
                self._mouse_pos_history.clear()
            return

        with self._history_lock:
            mouse_speed = self._get_mouse_speed_px_per_s()
            if mouse_speed < inertia_threshold:
                self._scroll_history.clear()
                self._mouse_pos_history.clear()
                return

            vx, vy = self._get_weighted_velocity_from_history()
            speed_sq = vx * vx + vy * vy
            if speed_sq < 0.01:
                self._scroll_history.clear()
                self._mouse_pos_history.clear()
                return

            with self._inertia_lock:
                self.inertia_vx = vx
                self.inertia_vy = vy
                self.inertia_active = True
                # 重置浮点累积器，避免 active 阶段的残留余数影响惯性首帧精度
                self._scroll_accum_x = 0.0
                self._scroll_accum_y = 0.0
            self._scroll_history.clear()
            self._mouse_pos_history.clear()

    def _is_inertia_active(self) -> bool:
        with self._inertia_lock:
            return self.inertia_active

    def request_stop(self) -> None:
        """请求引擎线程停止，线程将在下一个 tick 结束后退出，并释放 Windows 定时器精度。"""
        self._stop_event.set()
        # 释放 Windows 定时器精度请求，避免长期占用
        if getattr(self, "_windows_timer_precision_active", False):
            _release_windows_timer_precision()
            self._windows_timer_precision_active = False

    def _snapshot_config(self):
        """一次性快照配置与运行时状态，避免在主循环中反复加锁。"""
        with STATE_LOCK:
            return (
                runtime.active,
                runtime.origin_pos,
                cfg.enable_horizontal,
                cfg.dead_zone,
                cfg.sensitivity,
                cfg.speed_factor,
                cfg.reverse_x,
                cfg.reverse_y,
            )

    def run(self) -> None:
        """主循环：根据 active/inertia/idle 三种状态分别处理滚动逻辑。"""
        last_dir = "neutral"
        platform_multiplier = system_platform.get_scroll_multiplier()
        was_active = False

        while not self._stop_event.is_set():
            (
                active,
                origin_pos,
                enable_horizontal,
                dead_zone,
                sensitivity,
                speed_factor,
                reverse_x,
                reverse_y,
            ) = self._snapshot_config()

            if active:
                # 如果惯性还在运行但用户重新激活滚动，则立即中断惯性。
                with self._inertia_lock:
                    inertia_running = self.inertia_active
                if inertia_running:
                    self.interrupt_inertia()

                try:
                    curr_x, curr_y = self.mouse_controller.position
                    dx, dy = (
                        curr_x - origin_pos[0],
                        curr_y - origin_pos[1],
                    )

                    if not enable_horizontal:
                        dx = 0

                    dist = math.hypot(dx, dy)
                    current_dir = "neutral"

                    if dist > dead_zone:
                        if abs(dx) > abs(dy):
                            current_dir = "right" if dx > 0 else "left"
                        else:
                            current_dir = "down" if dy > 0 else "up"

                    if current_dir != last_dir:
                        self.bridge.update_direction.emit(current_dir)
                        last_dir = current_dir

                    scroll_x, scroll_y = self.strategy.calculate_scroll_speed(
                        dx,
                        dy,
                        dist,
                        SimpleNamespace(
                            dead_zone=dead_zone,
                            sensitivity=sensitivity,
                            speed_factor=speed_factor,
                        ),
                        platform_multiplier,
                        reverse_x=reverse_x,
                        reverse_y=reverse_y,
                    )

                    # 累积浮点滚动量：pynput 在 Windows 截断浮点为整数，
                    # 导致低速滚动完全丢失。这里累积小数，达到 1.0 时发送整数。
                    self._scroll_accum_x += scroll_x
                    self._scroll_accum_y += scroll_y
                    int_scroll_x = int(self._scroll_accum_x)
                    int_scroll_y = int(self._scroll_accum_y)
                    self._scroll_accum_x -= int_scroll_x
                    self._scroll_accum_y -= int_scroll_y

                    if scroll_x != 0 or scroll_y != 0:
                        # 记录原始浮点速度用于惯性速度估算（反映用户真实意图）
                        now = time.monotonic()
                        with self._history_lock:
                            self._scroll_history.append((now, scroll_x, scroll_y))
                            self._prune_history(self._scroll_history, now)

                            self._mouse_pos_history.append((now, curr_x, curr_y))
                            self._prune_history(self._mouse_pos_history, now)

                        # 仅在累积到整数时才实际发送滚动事件
                        if int_scroll_x != 0 or int_scroll_y != 0:
                            self.mouse_controller.scroll(int_scroll_x, int_scroll_y)

                    was_active = True
                    time.sleep(ENGINE_TICK_INTERVAL)
                except Exception as e:
                    logger.debug(f"ScrollEngine active mode error: {e}")
                    time.sleep(ENGINE_IDLE_POLL_INTERVAL)

            elif self._is_inertia_active():
                # 惯性衰减阶段。
                try:
                    with STATE_LOCK:
                        enable_inertia = cfg.enable_inertia
                    if not enable_inertia:
                        self.interrupt_inertia()
                    else:
                        with self._inertia_lock:
                            self.inertia_vx *= self.friction
                            self.inertia_vy *= self.friction

                            speed_sq = self.inertia_vx * self.inertia_vx + self.inertia_vy * self.inertia_vy
                            if speed_sq < INERTIA_STOP_THRESHOLD:
                                do_stop = True
                                sx, sy = 0.0, 0.0
                            else:
                                do_stop = False
                                sx, sy = self.inertia_vx, self.inertia_vy

                        if do_stop:
                            self.interrupt_inertia()
                        else:
                            # 复用浮点累积器：pynput 在 Windows 截断浮点为整数，
                            # 低速惯性衰减阶段同样会丢失精度。累积小数，达到 1.0 时才发送。
                            self._scroll_accum_x += sx
                            self._scroll_accum_y += sy
                            int_sx = int(self._scroll_accum_x)
                            int_sy = int(self._scroll_accum_y)
                            self._scroll_accum_x -= int_sx
                            self._scroll_accum_y -= int_sy
                            if int_sx != 0 or int_sy != 0:
                                self.mouse_controller.scroll(int_sx, int_sy)
                    time.sleep(ENGINE_TICK_INTERVAL)
                except Exception as e:
                    logger.debug(f"ScrollEngine inertia mode error: {e}")
                    self.interrupt_inertia()

            else:
                # 检测从 active 到 inactive 的转换，必要时尝试进入惯性。
                if was_active:
                    self._try_enter_inertia()
                    was_active = False

                last_dir = "neutral"
                time.sleep(ENGINE_IDLE_POLL_INTERVAL)
