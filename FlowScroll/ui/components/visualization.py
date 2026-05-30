"""可视化类组件：速度曲线可视化"""
import math
from types import SimpleNamespace

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import (
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import QWidget

from FlowScroll.core.scroller import PowerCurveStrategy
from FlowScroll.ui.styles import (
    COLOR_ACCENT,
    COLOR_BG_INPUT,
    COLOR_BORDER,
)


class SpeedCurveWidget(QWidget):
    """迷你速度-距离曲线可视化组件。

    用于参数调校卡片尾部，实时反映 sensitivity / dead_zone / speed_factor
    三个核心参数如何组合影响滚动速度。曲线越陡表示灵敏度越高。

    横轴: 鼠标到准星中心的距离 (0 到最大显示距离)
    纵轴: 计算得到的滚动速度 (相对标度)
    死区段以虚线标注 (曲线在死区内为水平轴)。
    """

    CANVAS_HEIGHT = 80          # 组件高度 (像素)
    MAX_DISTANCE = 300.0         # 横轴最大值，模拟最大鼠标偏移
    PLATFORM_MULTIPLIER = 1.0    # 平台倍率固定为 1.0 (仅用于相对可视化)
    SAMPLE_STEP = 3.0            # 曲线采样步进 (像素，越小越平滑)
    CURVE_WIDTH = 2.0            # 曲线描边宽度

    def __init__(self, parent=None):
        super().__init__(parent)
        # 默认值，外部应尽快通过 update_params 更新
        self._sensitivity = 2.0
        self._dead_zone = 20.0
        self._speed_factor = 2.0
        self._strategy = PowerCurveStrategy()
        self.setMinimumHeight(self.CANVAS_HEIGHT)
        self.setFixedHeight(self.CANVAS_HEIGHT)

    def update_params(
        self, sensitivity: float, dead_zone: float, speed_factor: float
    ) -> None:
        """由 UI 滑块回调驱动；参数变化时触发重绘。"""
        self._sensitivity = float(sensitivity)
        self._dead_zone = float(dead_zone)
        self._speed_factor = float(speed_factor)
        self.update()  # 调度重绘

    def paintEvent(self, event):
        """绘制坐标网格 + 死区标尺 + 速度曲线 + 渐变填充。"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        rect = self.rect()
        w, h = rect.width(), rect.height()
        if w <= 0 or h <= 0:
            painter.end()
            return

        # 背景填充
        painter.fillRect(rect, QColor(COLOR_BG_INPUT))

        # 1) 绘制垂直参考网格
        grid_pen = QPen(QColor(COLOR_BORDER), 1, Qt.DashLine)
        grid_pen.setCosmetic(True)
        painter.setPen(grid_pen)
        for frac in (0.25, 0.50, 0.75):
            x = int(w * frac)
            painter.drawLine(QPoint(x, 0), QPoint(x, h))

        # 2) 曲线预计算
        config = SimpleNamespace(
            dead_zone=self._dead_zone,
            sensitivity=self._sensitivity,
            speed_factor=self._speed_factor,
        )
        samples: list[tuple[float, float]] = []   # (横轴位置比例, 速度)
        dist = 0.0
        max_speed = 1e-9
        while dist <= self.MAX_DISTANCE:
            _, sy = self._strategy.calculate_scroll_speed(
                0.0, dist, dist, config, self.PLATFORM_MULTIPLIER,
            )
            speed = abs(sy)
            samples.append((dist, speed))
            if speed > max_speed:
                max_speed = speed
            dist += self.SAMPLE_STEP

        # 3) 构建 QPainterPath
        def dist_to_px(d: float) -> float:
            return (d / self.MAX_DISTANCE) * w

        def speed_to_py(s: float) -> float:
            # 留出上下各 4px 内边距，0 速度在底部，最大速度在顶部
            margin = 4.0
            usable = h - 2 * margin
            if max_speed <= 0:
                return h - margin
            return h - margin - (s / max_speed) * usable

        path = QPainterPath()
        for i, (d, s) in enumerate(samples):
            px, py = dist_to_px(d), speed_to_py(s)
            if i == 0:
                path.moveTo(px, py)
            else:
                path.lineTo(px, py)

        # 4) 曲线下方填充渐变
        fill_path = QPainterPath(path)
        fill_path.lineTo(dist_to_px(samples[-1][0]), h)
        fill_path.lineTo(0, h)
        fill_path.closeSubpath()

        gradient = QLinearGradient(0.0, 0.0, 0.0, float(h))
        accent_qc = QColor(COLOR_ACCENT)
        gradient.setColorAt(0.0, QColor(accent_qc.red(), accent_qc.green(), accent_qc.blue(), 90))
        gradient.setColorAt(1.0, QColor(accent_qc.red(), accent_qc.green(), accent_qc.blue(), 0))
        painter.fillPath(fill_path, gradient)

        # 5) 绘制曲线主体
        curve_pen = QPen(QColor(COLOR_ACCENT), self.CURVE_WIDTH)
        curve_pen.setCapStyle(Qt.RoundCap)
        curve_pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(curve_pen)
        painter.drawPath(path)

        # 6) 死区标尺 (虚线 + 半透明覆盖)
        dead_zone_px = dist_to_px(self._dead_zone)
        if 0 < dead_zone_px < w:
            dz_pen = QPen(QColor(COLOR_ACCENT), 1, Qt.DashLine)
            dz_pen.setCosmetic(True)
            painter.setPen(dz_pen)
            painter.drawLine(QPointF(dead_zone_px, 0), QPointF(dead_zone_px, h))

        painter.end()
