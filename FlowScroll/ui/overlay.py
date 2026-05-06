from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen, QPainterPath, QRadialGradient

from FlowScroll.platform import OS_NAME
from FlowScroll.core.config import cfg


class ResizableOverlay(QWidget):
    """可缩放的准星覆盖层，显示当前滚动方向指示箭头。"""

    MIN_RENDER_SIZE = 20  # 最小渲染尺寸，避免渲染异常

    def __init__(self):
        """初始化覆盖层窗口，设置为无边框、置顶、透明背景。"""
        super().__init__()
        flags = (
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.WindowTransparentForInput
        )
        if OS_NAME == "Windows":
            flags |= Qt.Tool
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.base_size = 60.0
        self._overlay_size = int(cfg.overlay_size)
        self.update_geometry(self._overlay_size)
        self.direction = "neutral"
        self.preview_timer = QTimer()
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self.hide)

    def update_geometry(self, size) -> None:
        """更新覆盖层尺寸并触发重绘。"""
        self._overlay_size = size
        size = max(size, self.MIN_RENDER_SIZE)
        self.setFixedSize(size, size)
        self.update()

    def set_direction(self, direction) -> None:
        """设置当前方向（neutral/up/down/left/right），方向变化时触发重绘。"""
        if self.direction != direction:
            self.direction = direction
            self.update()

    def show_preview(self) -> None:
        """在屏幕可用区域中心短暂显示预览，800ms 后自动隐藏。"""
        screen = QApplication.primaryScreen()
        available = screen.availableGeometry() if screen else screen.geometry()
        self.set_direction("neutral")
        self.move(
            int(available.center().x() - self.width() / 2),
            int(available.center().y() - self.height() / 2),
        )
        self.show()
        self.raise_()
        self.preview_timer.start(800)

    def paintEvent(self, event) -> None:
        """绘制准星：光晕中心 + 渐变方向箭头。"""
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.translate(self.width() / 2, self.height() / 2)
        scale = self.width() / self.base_size
        p.scale(scale, scale)

        # 外层光晕
        glow_outer = QRadialGradient(0, 0, 12)
        glow_outer.setColorAt(0.0, QColor(59, 130, 246, 80))
        glow_outer.setColorAt(0.6, QColor(59, 130, 246, 30))
        glow_outer.setColorAt(1.0, QColor(59, 130, 246, 0))
        p.setBrush(glow_outer)
        p.setPen(Qt.NoPen)
        p.drawEllipse(-12, -12, 24, 24)

        # 中心实心圆点
        p.setBrush(QColor(59, 130, 246, 200))
        p.setPen(QPen(QColor(255, 255, 255, 230), 1.5))
        p.drawEllipse(-3, -3, 6, 6)

        def draw_arrow(painter, angle, is_active):
            painter.save()
            painter.rotate(angle)
            painter.translate(0, -14)
            path = QPainterPath()
            if is_active:
                path.moveTo(0, -8)
                path.lineTo(-9, 6)
                path.lineTo(9, 6)
                painter.setPen(QPen(QColor(255, 255, 255, 200), 1.5))
                gradient = QRadialGradient(0, 0, 10)
                gradient.setColorAt(0.0, QColor(59, 130, 246, 220))
                gradient.setColorAt(1.0, QColor(37, 99, 235, 180))
                painter.setBrush(gradient)
            else:
                path.moveTo(0, -5)
                path.lineTo(-5, 3)
                path.lineTo(5, 3)
                painter.setPen(QPen(QColor(148, 163, 184, 140), 1))
                painter.setBrush(QColor(148, 163, 184, 50))
            path.closeSubpath()
            painter.drawPath(path)
            painter.restore()

        if self.direction == "neutral":
            draw_arrow(p, 0, False)
            draw_arrow(p, 180, False)
            draw_arrow(p, 270, False)
            draw_arrow(p, 90, False)
        elif self.direction == "up":
            draw_arrow(p, 0, True)
        elif self.direction == "down":
            draw_arrow(p, 180, True)
        elif self.direction == "left":
            draw_arrow(p, 270, True)
        elif self.direction == "right":
            draw_arrow(p, 90, True)
