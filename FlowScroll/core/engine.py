import math
import time
import threading
from FlowScroll.core.config import cfg, runtime
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

        # 惯性状态
        self.inertia_active = False
        self.inertia_vx = 0.0
        self.inertia_vy = 0.0
        self.friction = self._compute_friction(cfg.inertia_friction_ms)

        # 滚动速度历史（用于计算惯性初速度）
        self._scroll_history = []  # [(time_s, scroll_x, scroll_y), ...]
        self._scroll_history_window = SCROLL_HISTORY_WINDOW

        # 鼠标位置历史（用于计算触发阈值）
        self._mouse_pos_history = []  # [(time_s, x, y), ...]

    @staticmethod
    def _compute_friction(half_life_ms):
        """将半衰期 (ms) 转换为每帧 (4ms) 的摩擦系数。"""
        if half_life_ms <= 0:
            return 0.9
        ticks = half_life_ms / 4.0  # 4ms per tick
        return math.pow(0.5, 1.0 / ticks)

    def update_friction(self):
        """配置变更后调用，重新计算摩擦系数。"""
        self.friction = self._compute_friction(cfg.inertia_friction_ms)

    def interrupt_inertia(self):
        """立即中断惯性滑动。"""
        if self.inertia_active:
            self.inertia_active = False
            self.inertia_vx = 0.0
            self.inertia_vy = 0.0

    def _prune_history(self, history, now):
        """清理超过窗口期的历史记录。"""
        cutoff = now - self._scroll_history_window
        while history and history[0][0] < cutoff:
            history.pop(0)

    def _get_max_speed_from_history(self):
        """从滚动历史中获取最大模值对应的速度向量。"""
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
        """计算最近窗口内鼠标的平均移动速度 (px/s)。"""
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
        """尝试从 active 状态进入惯性模式。"""
        if not cfg.enable_inertia:
            self._scroll_history.clear()
            self._mouse_pos_history.clear()
            return

        # 检查鼠标速度是否超过阈值
        mouse_speed = self._get_mouse_speed_px_per_s()
        if mouse_speed < cfg.inertia_threshold:
            self._scroll_history.clear()
            self._mouse_pos_history.clear()
            return

        # 获取惯性初速度
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

    def run(self):
        last_dir = "neutral"
        platform_multiplier = system_platform.get_scroll_multiplier()
        was_active = False

        while True:
            if runtime.active:
                # 惯性运行中被激活（新滚动开始），中断惯性
                if self.inertia_active:
                    self.interrupt_inertia()

                try:
                    curr_x, curr_y = self.mouse_controller.position
                    dx, dy = (
                        curr_x - runtime.origin_pos[0],
                        curr_y - runtime.origin_pos[1],
                    )

                    if not cfg.enable_horizontal:
                        dx = 0

                    dist = math.hypot(dx, dy)
                    current_dir = "neutral"

                    if dist > cfg.dead_zone:
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
                        cfg,
                        platform_multiplier,
                        reverse_x=cfg.reverse_x,
                        reverse_y=cfg.reverse_y,
                    )

                    if scroll_x != 0 or scroll_y != 0:
                        self.mouse_controller.scroll(scroll_x, scroll_y)

                        # 记录滚动速度历史
                        now = time.time()
                        self._scroll_history.append((now, scroll_x, scroll_y))
                        self._prune_history(self._scroll_history, now)

                        # 记录鼠标位置历史
                        self._mouse_pos_history.append((now, curr_x, curr_y))
                        self._prune_history(self._mouse_pos_history, now)

                    was_active = True
                    time.sleep(ENGINE_TICK_INTERVAL)
                except Exception as e:
                    logger.debug(f"ScrollEngine active mode error: {e}")

            elif self.inertia_active:
                # 惯性衰减模式
                try:
                    if not cfg.enable_inertia:
                        self.interrupt_inertia()
                    else:
                        self.inertia_vx *= self.friction
                        self.inertia_vy *= self.friction

                        # 速度过低时停止
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
                # 检测从 active 到 inactive 的转换，尝试进入惯性
                if was_active:
                    self._try_enter_inertia()
                    was_active = False

                last_dir = "neutral"
                time.sleep(ENGINE_IDLE_POLL_INTERVAL)
