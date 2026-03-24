import math
from abc import ABC, abstractmethod

class ScrollStrategy(ABC):
    @abstractmethod
    def calculate_scroll_speed(self, dx, dy, distance, config, platform_multiplier):
        """
        计算滚动速度。
        :param dx: X轴位移
        :param dy: Y轴位移
        :param distance: 距离原点的直线距离
        :param config: 全局配置对象 (GlobalConfig)
        :param platform_multiplier: 平台相关的滚动乘数 (来自 system_platform)
        :return: (scroll_x, scroll_y)
        """
        pass

class PowerCurveStrategy(ScrollStrategy):
    """
    幂函数曲线策略 (目前项目的默认行为)
    公式: speed = (distance - dead_zone)^sensitivity * multiplier * speed_factor
    """
    def calculate_scroll_speed(self, dx, dy, distance, config, platform_multiplier):
        if distance <= config.dead_zone:
            return 0.0, 0.0
            
        eff_dist = distance - config.dead_zone
        speed_scalar = math.pow(eff_dist, config.sensitivity) * platform_multiplier * config.speed_factor
        
        # 将标量速度按方向分配到 X 和 Y 轴
        scroll_x = (dx / distance) * speed_scalar
        scroll_y = (dy / distance) * speed_scalar * -1  # 反转Y轴因为鼠标坐标向下为正，滚轮向上为正
        
        return scroll_x, scroll_y

# 目前先使用原版算法
default_scroll_strategy = PowerCurveStrategy()
