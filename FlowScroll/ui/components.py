from PySide6.QtWidgets import QKeySequenceEdit
from PySide6.QtCore import Qt

class HotkeyEdit(QKeySequenceEdit):
    """自定义快捷键输入框 (防连招且支持退格清空)"""
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Backspace, Qt.Key_Delete) and event.modifiers() == Qt.NoModifier:
            self.clear() 
        else:
            super().keyPressEvent(event)
