from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QKeySequenceEdit,
    QLineEdit,
    QSlider,
)
from FlowScroll.core.hotkeys import (
    hotkey_from_key_event,
    hotkey_to_display,
    normalize_hotkey_string,
)
from FlowScroll.i18n import tr


class HotkeyEdit(QKeySequenceEdit):
    """自定义快捷键输入框，支持用 Backspace/Delete 清空。"""

    MOUSE_HOTKEYS = {
        Qt.BackButton: "mouse_x1",
        Qt.ForwardButton: "mouse_x2",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mouse_hotkey = ""
        self._placeholder_set = False

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._placeholder_set:
            editor = self.findChild(QLineEdit)
            if editor is not None:
                editor.setPlaceholderText(tr("main.hotkey.input_placeholder"))
                self._placeholder_set = True

    def set_hotkey(self, hotkey) -> None:
        self._mouse_hotkey = normalize_hotkey_string(hotkey)
        self._set_display_text(hotkey_to_display(self._mouse_hotkey))

    def hotkey_text(self):
        return self._mouse_hotkey

    def clear(self) -> None:
        self._mouse_hotkey = ""
        super().clear()

    def keyPressEvent(self, event) -> None:
        if (
            event.key() in (Qt.Key_Backspace, Qt.Key_Delete)
            and event.modifiers() == Qt.NoModifier
        ):
            self.clear()
        else:
            hotkey = hotkey_from_key_event(event)
            if hotkey:
                self._mouse_hotkey = hotkey
                self._set_display_text(hotkey_to_display(hotkey))
                event.accept()
                return
            super().keyPressEvent(event)

    def mousePressEvent(self, event) -> None:
        mouse_hotkey = self.MOUSE_HOTKEYS.get(event.button())
        if mouse_hotkey:
            self._mouse_hotkey = mouse_hotkey
            self._set_display_text(hotkey_to_display(mouse_hotkey))
            event.accept()
            return
        super().mousePressEvent(event)

    def _set_display_text(self, text):
        editor = self.findChild(QLineEdit)
        if editor is not None:
            editor.setText(text)


class UpwardComboBox(QComboBox):
    """向上弹出下拉列表，避免先向下再重定位的闪烁。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._popup_window = self.view().window()
        self._popup_window.installEventFilter(self)
        self._popup_visible = False

    def showPopup(self) -> None:
        self._popup_visible = True
        super().showPopup()

    def hidePopup(self) -> None:
        self._popup_visible = False
        super().hidePopup()

    def eventFilter(self, watched, event):
        if (
            watched is self._popup_window
            and self._popup_visible
            and event.type() == QEvent.Show
        ):
            self._move_popup_up()
        return super().eventFilter(watched, event)

    def _move_popup_up(self):
        popup_height = (
            self._popup_window.height() or self._popup_window.sizeHint().height()
        )
        combo_bottom = self.mapToGlobal(self.rect().bottomLeft())
        self._popup_window.move(
            combo_bottom.x(), combo_bottom.y() - popup_height - self.height()
        )


class NoWheelSlider(QSlider):
    """禁用滚轮调整的滑块。"""

    def wheelEvent(self, event) -> None:
        event.ignore()


class NoWheelSpinBox(QDoubleSpinBox):
    """禁用滚轮调整的数值框。"""

    def wheelEvent(self, event) -> None:
        event.ignore()
