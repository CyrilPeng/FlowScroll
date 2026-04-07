from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen, QPainterPath

from FlowScroll.platform import OS_NAME
from FlowScroll.core.config import cfg


class ResizableOverlay(QWidget):
    MIN_RENDER_SIZE = 20  # 最小渲染尺寸，避免渲染异常

    def __init__(self):
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
        self._overlay_size = size
        size = max(size, self.MIN_RENDER_SIZE)
        self.setFixedSize(size, size)
        self.update()

    def set_direction(self, direction) -> None:
        if self.direction != direction:
            self.direction = direction
            self.update()

    def show_preview(self) -> None:
        screen = QApplication.primaryScreen().geometry()
        self.set_direction("neutral")
        self.move(
            int(screen.center().x() - self.width() / 2),
            int(screen.center().y() - self.height() / 2),
        )
        self.show()
        self.raise_()
        self.preview_timer.start(800)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.translate(self.width() / 2, self.height() / 2)
        scale = self.width() / self.base_size
        p.scale(scale, scale)

        p.setBrush(QColor(50, 50, 50))
        p.setPen(QPen(QColor(255, 255, 255, 220), 2))
        p.drawEllipse(-4, -4, 8, 8)

        def draw_arrow(painter, angle, is_active):
            painter.save()
            painter.rotate(angle)
            painter.translate(0, -12)
            path = QPainterPath()
            if is_active:
                path.moveTo(0, -7)
                path.lineTo(-9, 7)
                path.lineTo(9, 7)
                painter.setBrush(QColor(0, 0, 0))
                painter.setPen(QPen(Qt.white, 2))
            else:
                path.moveTo(0, -4)
                path.lineTo(-5, 3)
                path.lineTo(5, 3)
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
