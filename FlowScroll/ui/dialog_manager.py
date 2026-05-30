"""对话框管理器 Mixin。

将 MainWindow 中的对话框打开逻辑提取到独立的 Mixin 类，
实现对话框的延迟导入和统一管理。

使用示例::

    class MainWindow(DialogMixin, QMainWindow):
        pass

    # 在主窗口中调用
    self.open_hotkey_dialog()
    self.show_help_dialog()
    self.open_webdav_settings()
    self.open_work_mode_dialog()
    self.open_filter_mode_dialog()
    self.open_reverse_mode_dialog()
    self.open_inertia_settings_dialog()
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QMessageBox,
)
from PySide6.QtCore import Qt

from FlowScroll.core.config import STATE_LOCK, cfg, runtime, set_config_attr
from FlowScroll.i18n import tr
from FlowScroll.ui.components import HotkeyEdit
from FlowScroll.ui.utils import resource_path
from FlowScroll.ui.styles import (
    get_hint_block_style,
    get_dialog_stylesheet,
    get_textedit_style,
)

import os


class DialogMixin:
    """提供对话框管理方法的 Mixin 基类。

    所有对话框方法都使用延迟导入，只有在实际打开对话框时
    才 import 对应的对话框类，减少启动时间。

    依赖:
        - self.ui_widgets (dict): UI 控件字典
        - self.save_presets_to_file(): 保存配置方法
        - self.update_hotkey_label(): 更新快捷键标签方法
        - self.ctrl.on_inertia_settings_accepted(): 惯性设置回调
    """

    def open_hotkey_dialog(self) -> None:
        """打开横向滚动快捷键设置对话框。"""
        dialog = QDialog(self)
        dialog.setWindowTitle(tr("main.hotkey_dialog.title"))
        dialog.setMinimumWidth(300)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        hint_label = QLabel(tr("main.hotkey_dialog.hint"))
        hint_label.setWordWrap(True)
        hint_label.setTextFormat(Qt.RichText)
        hint_label.setStyleSheet(get_hint_block_style())
        layout.addWidget(hint_label)

        hotkey_edit = HotkeyEdit()
        hotkey_edit.set_hotkey(cfg.horizontal_hotkey)
        hotkey_edit.setMaximumSequenceLength(1)
        layout.addWidget(hotkey_edit)

        btn_layout = QHBoxLayout()

        btn_clear = QPushButton(tr("main.hotkey_dialog.clear"))
        btn_clear.setObjectName("BtnDanger")
        btn_clear.clicked.connect(lambda: hotkey_edit.clear())
        btn_layout.addWidget(btn_clear)

        btn_layout.addStretch()

        btn_cancel = QPushButton(tr("main.hotkey_dialog.cancel"))
        btn_cancel.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_cancel)

        btn_ok = QPushButton(tr("main.hotkey_dialog.ok"))
        btn_ok.setObjectName("BtnPrimary")
        btn_ok.clicked.connect(dialog.accept)
        btn_layout.addWidget(btn_ok)

        layout.addLayout(btn_layout)

        if dialog.exec() == QDialog.Accepted:
            set_config_attr("horizontal_hotkey", hotkey_edit.hotkey_text())
            self.update_hotkey_label()
            self.save_presets_to_file()

    def show_help_dialog(self) -> None:
        """显示帮助对话框（含参数说明和图标）。"""
        dialog = QDialog(self)
        dialog.setWindowTitle(tr("main.help.title"))
        dialog.setMinimumSize(520, 420)
        dialog.resize(620, 500)
        dialog.setSizeGripEnabled(True)
        dialog.setStyleSheet(get_dialog_stylesheet() + get_textedit_style())

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        def img(name):
            """辅助函数：构建资源图片的 HTML img 标签。"""
            path = resource_path(os.path.join("FlowScroll", "resources", name)).replace("\\", "/")
            return f"<img src='{path}' width='14' height='14'>"

        help_text = tr(
            "main.help.html",
            speed_icon=img("ic_speed.svg"),
            power_icon=img("ic_power.svg"),
            target_icon=img("ic_target.svg"),
            move_icon=img("ic_move.svg"),
        )

        help_view = QTextEdit(dialog)
        help_view.setReadOnly(True)
        help_view.setAcceptRichText(True)
        help_view.setHtml(help_text)
        help_view.setMinimumHeight(280)
        layout.addWidget(help_view)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_close = QPushButton(tr("main.hotkey_dialog.ok"))
        btn_close.setObjectName("BtnPrimary")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(dialog.accept)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

        dialog.exec()

    def open_webdav_settings(self) -> None:
        """打开 WebDAV 云同步设置对话框。"""
        from FlowScroll.ui.webdav_dialog import WebDAVSyncDialog

        dialog = WebDAVSyncDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.save_presets_to_file()

    def open_work_mode_dialog(self) -> None:
        """打开工作模式设置对话框。"""
        from FlowScroll.ui.dialogs import WorkModeDialog

        dialog = WorkModeDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.save_presets_to_file()

    def open_filter_mode_dialog(self) -> None:
        """打开应用过滤模式设置对话框，进程名不可用时给出提示。"""
        from FlowScroll.ui.dialogs import AppFilterDialog

        with STATE_LOCK:
            process_name_status = runtime.process_name_status
            filter_mode = cfg.filter_mode
        if filter_mode in (1, 2) and process_name_status == "unavailable":
            QMessageBox.information(
                self,
                tr("dialog.filter.process_name_unavailable_title"),
                tr("dialog.filter.process_name_unavailable"),
            )
        dialog = AppFilterDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.save_presets_to_file()

    def open_reverse_mode_dialog(self) -> None:
        """打开滚轮方向反转设置对话框。"""
        from FlowScroll.ui.dialogs import ReverseModeDialog

        dialog = ReverseModeDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.save_presets_to_file()

    def open_inertia_settings_dialog(self) -> None:
        """打开惯性滚动设置对话框。"""
        from FlowScroll.ui.dialogs import InertiaSettingsDialog

        dialog = InertiaSettingsDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.ctrl.on_inertia_settings_accepted()
