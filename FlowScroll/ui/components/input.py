"""输入类组件：快捷键输入框与向上弹出下拉框。

提供两类常见的用户输入控件：

* :class:`HotkeyEdit` —— 用于绑定键盘快捷键或鼠标侧键（X1/X2）的输入控件，
  继承 :class:`QKeySequenceEdit`，扩展了对鼠标按钮的支持。
* :class:`UpwardComboBox` —— 向上弹出下拉框，避免在屏幕底部显示时先向下展开
  再向上重定位的视觉闪烁问题。

典型用法::

    from FlowScroll.ui.components import HotkeyEdit, UpwardComboBox

    hotkey_edit = HotkeyEdit(parent)
    hotkey_edit.set_hotkey("ctrl+shift+p")

    preset_combo = UpwardComboBox(parent)
    preset_combo.addItems(["预设 A", "预设 B"])
"""

from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import QComboBox, QKeySequenceEdit, QLineEdit

from FlowScroll.core.hotkeys import (
    hotkey_from_key_event,
    hotkey_to_display,
    normalize_hotkey_string,
)
from FlowScroll.i18n import tr


class HotkeyEdit(QKeySequenceEdit):
    """支持键盘快捷键和鼠标侧键绑定的输入控件。

    继承 :class:`QKeySequenceEdit`，新增以下能力：

    * 识别鼠标 X1/X2（侧键）并转换为 ``mouse_x1`` / ``mouse_x2`` 字符串。
    * 允许用户按 ``Backspace`` 或 ``Delete``（无修饰键）清空绑定。
    * 输入框首次显示时自动设置多语言占位提示文本。

    内部状态:
        _mouse_hotkey (str): 归一化后的快捷键字符串（如 ``"ctrl+shift+a"``）。
        _placeholder_set (bool): 占位文本是否已设置，避免多次初始化。

    常量:
        MOUSE_HOTKEYS (dict): 鼠标按钮枚举 → 内部标识字符串的映射。
    """

    MOUSE_HOTKEYS = {
        Qt.BackButton: "mouse_x1",
        Qt.ForwardButton: "mouse_x2",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mouse_hotkey = ""
        self._placeholder_set = False

    def showEvent(self, event) -> None:
        """首次显示时将多语言占位提示写入内部 ``QLineEdit``。

        参数:
            event (QShowEvent): 显示事件。
        """
        super().showEvent(event)
        if not self._placeholder_set:
            editor = self.findChild(QLineEdit)
            if editor is not None:
                editor.setPlaceholderText(tr("main.hotkey.input_placeholder"))
                self._placeholder_set = True

    def set_hotkey(self, hotkey) -> None:
        """程序化设置当前绑定的快捷键并刷新显示。

        参数:
            hotkey (str): 快捷键字符串，会被归一化后存储。
        """
        self._mouse_hotkey = normalize_hotkey_string(hotkey)
        self._set_display_text(hotkey_to_display(self._mouse_hotkey))

    def hotkey_text(self):
        """返回归一化后的快捷键字符串（用于持久化存储）。

        返回:
            str: 如 ``"ctrl+shift+a"`` 或空字符串（未绑定）。
        """
        return self._mouse_hotkey

    def clear(self) -> None:
        """清空快捷键绑定并重置显示。"""
        self._mouse_hotkey = ""
        super().clear()

    def keyPressEvent(self, event) -> None:
        """处理按键事件：``Backspace``/``Delete`` 清空，其他按键绑定为新快捷键。

        参数:
            event (QKeyEvent): 按键事件。
        """
        if event.key() in (Qt.Key_Backspace, Qt.Key_Delete) and event.modifiers() == Qt.NoModifier:
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
        """处理鼠标按键事件：识别 X1/X2 侧键并绑定为快捷键。

        参数:
            event (QMouseEvent): 鼠标按下事件。
        """
        mouse_hotkey = self.MOUSE_HOTKEYS.get(event.button())
        if mouse_hotkey:
            self._mouse_hotkey = mouse_hotkey
            self._set_display_text(hotkey_to_display(mouse_hotkey))
            event.accept()
            return
        super().mousePressEvent(event)

    def _set_display_text(self, text):
        """将用户可读的快捷键文本写入内部输入框。"""
        editor = self.findChild(QLineEdit)
        if editor is not None:
            editor.setText(text)


class UpwardComboBox(QComboBox):
    """向上弹出的下拉框。

    Qt 默认的下拉框向下展开后会向上"抖动"以对齐控件底部，
    在屏幕底部使用时会出现明显的视觉闪烁。本控件通过安装事件过滤器，
    在下拉框弹出窗口显示前直接将其定位到控件上方（向上展开），
    从而避免重定位抖动。

    内部状态:
        _popup_window (QWidget): 弹出窗口句柄（通过 ``view().window()`` 获取）。
        _popup_visible (bool): 弹出窗口是否当前可见。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._popup_window = self.view().window()
        self._popup_window.installEventFilter(self)
        self._popup_visible = False

    def showPopup(self) -> None:
        """标记弹出为可见状态并调用基类实现。"""
        self._popup_visible = True
        super().showPopup()

    def hidePopup(self) -> None:
        """标记弹出为隐藏状态并调用基类实现。"""
        self._popup_visible = False
        super().hidePopup()

    def eventFilter(self, watched, event):
        """拦截弹出窗口的 ``QEvent.Show`` 事件，触发向上定位逻辑。"""
        if watched is self._popup_window and self._popup_visible and event.type() == QEvent.Show:
            self._move_popup_up()
        return super().eventFilter(watched, event)

    def _move_popup_up(self):
        """将弹出窗口移动到下拉框控件正上方（向上展开）。"""
        popup_height = self._popup_window.height() or self._popup_window.sizeHint().height()
        combo_bottom = self.mapToGlobal(self.rect().bottomLeft())
        self._popup_window.move(combo_bottom.x(), combo_bottom.y() - popup_height - self.height())
