from PySide6.QtWidgets import QKeySequenceEdit, QComboBox, QSlider, QDoubleSpinBox
from PySide6.QtCore import Qt, QTimer


class HotkeyEdit(QKeySequenceEdit):
    """自定义快捷键输入框 (防连招且支持退格清空)"""

    def keyPressEvent(self, event):
        if (
            event.key() in (Qt.Key_Backspace, Qt.Key_Delete)
            and event.modifiers() == Qt.NoModifier
        ):
            self.clear()
        else:
            super().keyPressEvent(event)


class UpwardComboBox(QComboBox):
    """下拉框向上弹出"""

    def showPopup(self):
        super().showPopup()
        QTimer.singleShot(1, self._move_popup_up)

    def _move_popup_up(self):
        popup = self.view().window()
        combo_bottom = self.mapToGlobal(self.rect().bottomLeft())
        popup.move(combo_bottom.x(), combo_bottom.y() - popup.height() - self.height())


class NoWheelSlider(QSlider):
    """禁止滚轮调整的滑块"""

    def wheelEvent(self, event):
        event.ignore()


class NoWheelSpinBox(QDoubleSpinBox):
    """禁止滚轮调整的数值框"""

    def wheelEvent(self, event):
        event.ignore()
