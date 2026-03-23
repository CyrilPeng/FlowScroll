import math
import time
import threading
from FlowScroll.core.config import cfg
from FlowScroll.core.scroller import default_scroll_strategy
from FlowScroll.platform import system_platform


class ScrollEngine(threading.Thread):
    def __init__(self, bridge, mouse_controller):
        super().__init__(daemon=True)
        self.bridge = bridge
        self.mouse_controller = mouse_controller
        self.strategy = default_scroll_strategy

    def run(self):
        last_dir = "neutral"
        platform_multiplier = system_platform.get_scroll_multiplier()

        while True:
            if cfg.active:
                try:
                    curr_x, curr_y = self.mouse_controller.position
                    dx, dy = curr_x - cfg.origin_pos[0], curr_y - cfg.origin_pos[1]

                    if not cfg.enable_horizontal:
                        dx = 0

                    dist = math.hypot(dx, dy)
                    current_dir = "neutral"

                    if dist > cfg.dead_zone:
                        if abs(dx) > abs(dy):
                            current_dir = "right" if dx > 0 else "left"
                        else:
                            current_dir = "down" if dy > 0 else "up"

                    # 仅在方向改变时发射信号更新 UI
                    if current_dir != last_dir:
                        self.bridge.update_direction.emit(current_dir)
                        last_dir = current_dir

                    # 计算并注入滚动
                    scroll_x, scroll_y = self.strategy.calculate_scroll_speed(
                        dx, dy, dist, cfg, platform_multiplier
                    )

                    if scroll_x != 0 or scroll_y != 0:
                        self.mouse_controller.scroll(scroll_x, scroll_y)

                    time.sleep(0.01)
                except Exception:
                    pass
            else:
                last_dir = "neutral"
                time.sleep(0.05)
