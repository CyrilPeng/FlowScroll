"""激活模式设置对话框（点击/长按）。

允许用户选择滚动功能的激活方式：
* **点击切换模式（mode_id=0）**：按下激活键一次开启，再按一次关闭。
* **长按激活模式（mode_id=1）**：按住激活键时保持激活状态，松开即关闭。

同时提供延迟启动（兼容模式）选项，可在激活键按下后延迟若干毫秒
才真正启动滚动，避免与应用程序自身的单击/中键点击事件冲突。
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QCheckBox,
    QRadioButton,
    QButtonGroup,
    QPushButton,
    QSlider,
)
from PySide6.QtCore import Qt

from FlowScroll.core.config import cfg, set_config_attr
from FlowScroll.i18n import tr
from FlowScroll.ui.components import HotkeyEdit
from FlowScroll.ui.helpers import create_card, create_h_line
from FlowScroll.ui.styles import (
    get_dialog_stylesheet,
    get_checkbox_style,
    get_radiobutton_style,
    get_value_label_style,
    get_description_style,
    get_dialog_title_style,
    get_dialog_subtitle_style,
)
from FlowScroll.constants import (
    WORK_MODE_DIALOG_WIDTH,
    WORK_MODE_DIALOG_HEIGHT,
)


class WorkModeDialog(QDialog):
    """激活模式与延迟启动设置对话框。

    属性:
        activation_group (QButtonGroup): 互斥的激活模式单选按钮组。
        activation_hotkey_edit_click (HotkeyEdit): 点击模式的快捷键绑定输入框。
        activation_hotkey_edit_hold (HotkeyEdit): 长按模式的快捷键绑定输入框。
        chk_activation_compat_mode (QCheckBox): 是否启用延迟启动（兼容模式）。
        activation_delay_slider (QSlider): 延迟时间滑块（0-500ms）。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dialog.work.title"))
        self.setMinimumSize(WORK_MODE_DIALOG_WIDTH, WORK_MODE_DIALOG_HEIGHT)
        self.setSizeGripEnabled(True)

        self.setStyleSheet(get_dialog_stylesheet() + get_radiobutton_style() + get_checkbox_style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        mode_card, mode_layout = create_card()
        mode_layout.setContentsMargins(16, 16, 16, 16)
        mode_layout.setSpacing(12)

        title = QLabel(tr("dialog.work.header_title"))
        title.setStyleSheet(get_dialog_title_style())
        subtitle = QLabel(tr("dialog.work.subtitle"))
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(get_dialog_subtitle_style())
        mode_layout.addWidget(title)
        mode_layout.addWidget(subtitle)

        self.activation_group = QButtonGroup(self)
        self._build_mode_block(
            mode_layout,
            mode_id=0,
            title=tr("dialog.work.mode_click_title"),
            desc=tr("dialog.work.mode_click_desc"),
            key_name="click",
            hotkey_value=cfg.activation_hotkey_click,
        )
        self._build_mode_block(
            mode_layout,
            mode_id=1,
            title=tr("dialog.work.mode_hold_title"),
            desc=tr("dialog.work.mode_hold_desc"),
            key_name="hold",
            hotkey_value=cfg.activation_hotkey_hold,
        )
        self.radio_click_toggle.setChecked(cfg.activation_mode == 0)
        self.radio_hold.setChecked(cfg.activation_mode == 1)
        layout.addWidget(mode_card)

        policy_card, policy_layout = create_card()
        policy_layout.setContentsMargins(16, 16, 16, 16)
        policy_layout.setSpacing(10)

        self.chk_activation_compat_mode = QCheckBox(tr("dialog.work.compat_mode"))
        self.chk_activation_compat_mode.setChecked(cfg.activation_compat_mode)
        self.chk_activation_compat_mode.setCursor(Qt.PointingHandCursor)
        self.chk_activation_compat_mode.toggled.connect(self._on_compat_mode_changed)
        policy_layout.addWidget(self.chk_activation_compat_mode)

        delay_row = QHBoxLayout()
        delay_row.setContentsMargins(8, 0, 0, 0)
        delay_row.setSpacing(10)
        self.delay_title = QLabel(tr("dialog.work.delay_title"))
        self.delay_title.setStyleSheet(get_dialog_subtitle_style())
        self.delay_value_label = QLabel()
        self.delay_value_label.setStyleSheet(get_value_label_style())

        self.activation_delay_slider = QSlider(Qt.Horizontal)
        self.activation_delay_slider.setRange(0, 500)
        self.activation_delay_slider.setSingleStep(10)
        self.activation_delay_slider.setValue(int(cfg.activation_delay_ms))
        self.activation_delay_slider.valueChanged.connect(self._update_delay_label)
        self.activation_delay_slider.setCursor(Qt.PointingHandCursor)
        self.activation_delay_slider.setFixedHeight(22)

        delay_row.addWidget(self.delay_title)
        delay_row.addWidget(self.activation_delay_slider, 1)
        delay_row.addWidget(self.delay_value_label)
        policy_layout.addLayout(delay_row)

        self.compat_hint = QLabel(tr("dialog.work.compat_hint"))
        self.compat_hint.setWordWrap(True)
        self.compat_hint.setContentsMargins(8, 0, 0, 0)
        self.compat_hint.setStyleSheet(get_description_style())
        policy_layout.addWidget(self.compat_hint)

        layout.addWidget(policy_card)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_save = QPushButton(tr("dialog.work.save"))
        btn_save.setObjectName("BtnPrimary")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.clicked.connect(self.save_and_close)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

        self._update_delay_label()
        self._on_compat_mode_changed(self.chk_activation_compat_mode.isChecked())

        adaptive_height = max(WORK_MODE_DIALOG_HEIGHT, self.sizeHint().height())
        self.resize(WORK_MODE_DIALOG_WIDTH, adaptive_height)

    def _build_mode_block(self, parent_layout, mode_id, title, desc, key_name, hotkey_value):
        """构造单个激活模式区块（单选按钮 + 说明 + 快捷键绑定行）。

        参数:
            parent_layout: 父布局，用于向其中追加控件。
            mode_id (int): 模式标识（0=点击切换，1=长按激活）。
            title (str): 单选按钮显示文本。
            desc (str): 模式说明文本。
            key_name (str): 快捷键绑定属性名后缀，将构造
                ``self.activation_hotkey_edit_{key_name}`` 属性。
            hotkey_value (str): 当前已绑定的快捷键字符串。
        """
        block = QLabel()
        block.setFixedHeight(1)
        if parent_layout.count() > 0:
            parent_layout.addWidget(create_h_line())

        radio = QRadioButton(title)
        radio.setCursor(Qt.PointingHandCursor)
        self.activation_group.addButton(radio, mode_id)
        parent_layout.addWidget(radio)

        if mode_id == 0:
            self.radio_click_toggle = radio
        else:
            self.radio_hold = radio

        desc_lbl = QLabel(desc)
        desc_lbl.setWordWrap(True)
        desc_lbl.setContentsMargins(24, 0, 0, 0)
        desc_lbl.setStyleSheet(get_description_style())
        parent_layout.addWidget(desc_lbl)
        parent_layout.addLayout(self._create_hotkey_row(key_name, hotkey_value))

    def _create_hotkey_row(self, key_name, hotkey_value):
        """构造快捷键绑定行（输入框 + "恢复默认"按钮）。

        将生成的 :class:`HotkeyEdit` 实例以
        ``activation_hotkey_edit_{key_name}`` 的属性名保存在 self 上，
        供 :meth:`save_and_close` 读取最终绑定的快捷键。
        """
        wrapper = QVBoxLayout()
        wrapper.setContentsMargins(24, 0, 0, 0)
        wrapper.setSpacing(8)

        row = QHBoxLayout()
        row.setSpacing(8)

        edit = HotkeyEdit()
        edit.set_hotkey(hotkey_value)
        edit.setMaximumSequenceLength(1)
        row.addWidget(edit, 1)

        btn_clear = QPushButton(tr("dialog.work.default"))
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.clicked.connect(edit.clear)
        row.addWidget(btn_clear)

        wrapper.addLayout(row)
        setattr(self, f"activation_hotkey_edit_{key_name}", edit)
        return wrapper

    def _update_delay_label(self):
        """根据滑块当前值刷新延迟时间标签（形如 ``"150 ms"``）。"""
        self.delay_value_label.setText(f"{self.activation_delay_slider.value()} ms")

    def _on_compat_mode_changed(self, checked):
        """切换兼容模式复选框时，启用/禁用延迟滑块及其关联标签。"""
        self.activation_delay_slider.setEnabled(checked)
        self.delay_title.setEnabled(checked)
        self.delay_value_label.setEnabled(checked)
        self.compat_hint.setEnabled(checked)

    def save_and_close(self) -> None:
        """将激活模式、快捷键绑定及延迟设置写入配置并关闭对话框。"""
        set_config_attr("activation_mode", self.activation_group.checkedId())
        set_config_attr("activation_hotkey_click", self.activation_hotkey_edit_click.hotkey_text())
        set_config_attr("activation_hotkey_hold", self.activation_hotkey_edit_hold.hotkey_text())
        set_config_attr("activation_compat_mode", self.chk_activation_compat_mode.isChecked())
        set_config_attr("activation_delay_ms", int(self.activation_delay_slider.value()))
        self.accept()
