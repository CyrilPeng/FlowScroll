from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPainter, QPen, QPainterPath, QRadialGradient

from FlowScroll.platform import OS_NAME
from FlowScroll.core.config import cfg


class ResizableOverlay(QWidget):
    """可缩放的准星覆盖层，显示当前滚动方向指示箭头。"""

    MIN_RENDER_SIZE = 20  # 最小渲染尺寸，避免渲染异常

    def __init__(self):
        """初始化覆盖层窗口，设置为无边框、透明背景，启用淡入淡出动画。"""
        super().__init__()
        flags = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowTransparentForInput
        if OS_NAME == "Windows":
            flags |= Qt.Tool
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.base_size = 60.0
        self._overlay_size = int(cfg.overlay_size)
        self.update_geometry(self._overlay_size)
        self.direction = "neutral"

        # 淡入淡出动画（用户体验优化）
        self._fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self._fade_animation.setDuration(200)  # 200ms 动画时长
        self._fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._fade_animation.finished.connect(self._on_fade_finished)
        self._is_fading = False
        self._pending_hide = False
        self._fade_mode = None

        # 预览定时器
        self.preview_timer = QTimer()
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self._start_fade_out)

        # 性能优化：预创建颜色、笔和路径对象
        self._init_drawing_resources()

    def _start_fade_out(self):
        """开始淡出动画。"""
        if self._is_fading:
            self._pending_hide = True
            return

        if not self.isVisible():
            return

        self._is_fading = True
        self._pending_hide = True
        self._fade_mode = "out"
        self._fade_animation.setStartValue(1.0)
        self._fade_animation.setEndValue(0.0)
        self._fade_animation.setDirection(QPropertyAnimation.Forward)
        self._fade_animation.start()

    def _on_fade_finished(self):
        """动画完成后重置状态；淡出完成时真正隐藏窗口。"""
        fade_mode = self._fade_mode
        self._is_fading = False
        self._fade_mode = None
        if fade_mode == "out" and self._pending_hide:
            self._pending_hide = False
            self.setWindowOpacity(1.0)
            self.hide()
            return

        if fade_mode == "in" and self._pending_hide:
            self._start_fade_out()

    def show(self):
        """显示覆盖层，带淡入效果。"""
        if self._is_fading:
            self._fade_animation.stop()
            self._is_fading = False
            self._pending_hide = False
            self._fade_mode = None

        # 设置初始透明度为 0
        self.setWindowOpacity(0.0)
        super().show()

        # 开始淡入动画
        self._is_fading = True
        self._fade_mode = "in"
        self._fade_animation.setStartValue(0.0)
        self._fade_animation.setEndValue(1.0)
        self._fade_animation.setDirection(QPropertyAnimation.Forward)
        self._fade_animation.start()
        self._init_drawing_resources()

    def _init_drawing_resources(self):
        """初始化绘制资源：预创建颜色、笔和路径对象，避免每次 paintEvent 重复创建。"""
        # 外层光晕渐变
        self.glow_outer = QRadialGradient(0, 0, 12)
        self.glow_outer.setColorAt(0.0, QColor(59, 130, 246, 80))
        self.glow_outer.setColorAt(0.6, QColor(59, 130, 246, 30))
        self.glow_outer.setColorAt(1.0, QColor(59, 130, 246, 0))

        # 中心圆点颜色
        self.center_color = QColor(59, 130, 246, 200)
        self.center_pen = QPen(QColor(255, 255, 255, 230), 1.5)

        # 活跃箭头颜色和渐变
        self.active_arrow_pen = QPen(QColor(255, 255, 255, 200), 1.5)
        self.active_arrow_gradient = QRadialGradient(0, 0, 10)
        self.active_arrow_gradient.setColorAt(0.0, QColor(59, 130, 246, 220))
        self.active_arrow_gradient.setColorAt(1.0, QColor(37, 99, 235, 180))

        # 非活跃箭头颜色和笔
        self.inactive_arrow_pen = QPen(QColor(148, 163, 184, 140), 1)
        self.inactive_arrow_color = QColor(148, 163, 184, 50)

        # 预计算活跃箭头路径
        self.active_arrow_path = QPainterPath()
        self.active_arrow_path.moveTo(0, -8)
        self.active_arrow_path.lineTo(-9, 6)
        self.active_arrow_path.lineTo(9, 6)
        self.active_arrow_path.closeSubpath()

        # 预计算非活跃箭头路径
        self.inactive_arrow_path = QPainterPath()
        self.inactive_arrow_path.moveTo(0, -5)
        self.inactive_arrow_path.lineTo(-5, 3)
        self.inactive_arrow_path.lineTo(5, 3)
        self.inactive_arrow_path.closeSubpath()

        # 方向到角度的映射
        self.direction_angles = {"up": 0, "down": 180, "left": 270, "right": 90}

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
        """绘制准星：光晕中心 + 渐变方向箭头。使用缓存的资源对象优化性能。"""
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.translate(self.width() / 2, self.height() / 2)
        scale = self.width() / self.base_size
        p.scale(scale, scale)

        # 绘制外层光晕（使用缓存对象）
        p.setBrush(self.glow_outer)
        p.setPen(Qt.NoPen)
        p.drawEllipse(-12, -12, 24, 24)

        # 绘制中心实心圆点（使用缓存对象）
        p.setBrush(self.center_color)
        p.setPen(self.center_pen)
        p.drawEllipse(-3, -3, 6, 6)

        def draw_arrow(painter, angle, is_active):
            """绘制箭头，根据 is_active 选择样式（使用缓存对象）。"""
            painter.save()
            painter.rotate(angle)
            painter.translate(0, -14)

            if is_active:
                painter.setPen(self.active_arrow_pen)
                painter.setBrush(self.active_arrow_gradient)
                painter.drawPath(self.active_arrow_path)
            else:
                painter.setPen(self.inactive_arrow_pen)
                painter.setBrush(self.inactive_arrow_color)
                painter.drawPath(self.inactive_arrow_path)

            painter.restore()

        # 根据方向绘制箭头（使用缓存的方向映射）
        if self.direction == "neutral":
            draw_arrow(p, 0, False)
            draw_arrow(p, 180, False)
            draw_arrow(p, 270, False)
            draw_arrow(p, 90, False)
        elif self.direction in self.direction_angles:
            draw_arrow(p, self.direction_angles[self.direction], True)
