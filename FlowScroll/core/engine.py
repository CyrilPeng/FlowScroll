import math
import time
import threading
from types import SimpleNamespace
from FlowScroll.core.config import STATE_LOCK, cfg, runtime
from FlowScroll.core.scroller import default_scroll_strategy
from FlowScroll.platform import system_platform
from FlowScroll.services.logging_service import logger
from FlowScroll.constants import (
    ENGINE_TICK_INTERVAL,
    ENGINE_IDLE_POLL_INTERVAL,
    INERTIA_STOP_THRESHOLD,
    SCROLL_HISTORY_WINDOW,
)


class ScrollEngine(threading.Thread):
    def __init__(self, bridge, mouse_controller):
        super().__init__(daemon=True)
        self.bridge = bridge
        self.mouse_controller = mouse_controller
        self.strategy = default_scroll_strategy

        # 惯性状态。
        self.inertia_active = False
        self.inertia_vx = 0.0
        self.inertia_vy = 0.0
        with STATE_LOCK:
            self.friction = self._compute_friction(cfg.inertia_friction_ms)

        # 滚动速度历史，用于估算惯性初速度。
        self._scroll_history = []  # 格式: [(时间戳秒, 横向滚动, 纵向滚动), ...]
        self._scroll_history_window = SCROLL_HISTORY_WINDOW

        # 鼠标位置历史，用于计算触发惯性的速度阈值。
        self._mouse_pos_history = []  # 格式: [(时间戳秒, x, y), ...]

    @staticmethod
    def _compute_friction(half_life_ms):
        """将半衰期毫秒值换算为每帧的摩擦系数。"""
        if half_life_ms <= 0:
            return 0.9
        ticks = half_life_ms / 4.0  # 每帧按 4ms 计算。
        return math.pow(0.5, 1.0 / ticks)

    def update_friction(self) -> None:
        """配置变化后重新计算摩擦系数。"""
        with STATE_LOCK:
            self.friction = self._compute_friction(cfg.inertia_friction_ms)

    def interrupt_inertia(self) -> None:
        """立即中断惯性滚动。"""
        if self.inertia_active:
            self.inertia_active = False
            self.inertia_vx = 0.0
            self.inertia_vy = 0.0

    def _prune_history(self, history, now):
        """清理超出时间窗口的历史记录。"""
        cutoff = now - self._scroll_history_window
        while history and history[0][0] < cutoff:
            history.pop(0)

    def _get_max_speed_from_history(self):
        """从滚动历史中取出模长最大的速度向量。"""
        if not self._scroll_history:
            return 0.0, 0.0

        max_speed_sq = 0.0
        best_vx, best_vy = 0.0, 0.0
        for _, vx, vy in self._scroll_history:
            speed_sq = vx * vx + vy * vy
            if speed_sq > max_speed_sq:
                max_speed_sq = speed_sq
                best_vx, best_vy = vx, vy

        return best_vx, best_vy

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
        """尝试从激活状态切换到惯性模式。"""
        with STATE_LOCK:
            enable_inertia = cfg.enable_inertia
            inertia_threshold = cfg.inertia_threshold
        if not enable_inertia:
            self._scroll_history.clear()
            self._mouse_pos_history.clear()
            return

        # 先检查鼠标速度是否达到进入惯性的阈值。
        mouse_speed = self._get_mouse_speed_px_per_s()
        if mouse_speed < inertia_threshold:
            self._scroll_history.clear()
            self._mouse_pos_history.clear()
            return

        # 从最近滚动历史中提取惯性初速度。
        vx, vy = self._get_max_speed_from_history()
        speed_sq = vx * vx + vy * vy
        if speed_sq < 0.01:
            self._scroll_history.clear()
            self._mouse_pos_history.clear()
            return

        self.inertia_vx = vx
        self.inertia_vy = vy
        self.inertia_active = True
        self._scroll_history.clear()
        self._mouse_pos_history.clear()

    def run(self) -> None:
        last_dir = "neutral"
        platform_multiplier = system_platform.get_scroll_multiplier()
        was_active = False

        while True:
            with STATE_LOCK:
                active = runtime.active
                origin_pos = runtime.origin_pos
                enable_horizontal = cfg.enable_horizontal
                dead_zone = cfg.dead_zone
                sensitivity = cfg.sensitivity
                speed_factor = cfg.speed_factor
                reverse_x = cfg.reverse_x
                reverse_y = cfg.reverse_y

            if active:
                # 如果惯性还在运行但用户重新激活滚动，则立即中断惯性。
                if self.inertia_active:
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

                    if scroll_x != 0 or scroll_y != 0:
                        self.mouse_controller.scroll(scroll_x, scroll_y)

                        # 记录滚动速度历史。
                        now = time.monotonic()
                        self._scroll_history.append((now, scroll_x, scroll_y))
                        self._prune_history(self._scroll_history, now)

                        # 记录鼠标位置历史。
                        self._mouse_pos_history.append((now, curr_x, curr_y))
                        self._prune_history(self._mouse_pos_history, now)

                    was_active = True
                    time.sleep(ENGINE_TICK_INTERVAL)
                except Exception as e:
                    logger.debug(f"ScrollEngine active mode error: {e}")

            elif self.inertia_active:
                # 惯性衰减阶段。
                try:
                    with STATE_LOCK:
                        enable_inertia = cfg.enable_inertia
                    if not enable_inertia:
                        self.interrupt_inertia()
                    else:
                        self.inertia_vx *= self.friction
                        self.inertia_vy *= self.friction

                        # 速度过低时停止惯性。
                        speed_sq = (
                            self.inertia_vx * self.inertia_vx
                            + self.inertia_vy * self.inertia_vy
                        )
                        if speed_sq < INERTIA_STOP_THRESHOLD:
                            self.interrupt_inertia()
                        else:
                            self.mouse_controller.scroll(
                                self.inertia_vx, self.inertia_vy
                            )
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
