"""配置存储位置设置对话框。

允许用户查看并修改 FlowScroll 配置文件（``FlowScroll_config.json``）
的实际磁盘存储路径。支持三种路径来源，按优先级从高到低：

1. **环境变量**（``FLOWSCROLL_CONFIG_FILE`` / ``FLOWSCROLL_CONFIG_DIR``）：
   锁定模式，对话框禁止编辑。
2. **自定义路径**（通过 ``config_path.json`` 指针文件持久化）：
   用户手动指定的路径，可通过对话框修改或重置。
3. **平台默认路径**（如 Windows ``%APPDATA%/FlowScroll``）。

对话框提供文本输入、文件浏览、复制到剪贴板及重置到默认路径等操作。
"""

import os

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QMessageBox,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

from FlowScroll.core.config import (
    get_default_config_file,
    get_config_file,
    get_config_override_source,
    normalize_config_file_path,
    set_persisted_config_file,
)
from FlowScroll.i18n import tr
from FlowScroll.ui.helpers import create_card, create_h_line
from FlowScroll.ui.utils import resource_path
from FlowScroll.ui.styles import (
    get_dialog_stylesheet,
    get_hint_block_style,
    get_warning_banner_style,
    get_card_title_style,
)


class ConfigStorageDialog(QDialog):
    """配置存储路径设置对话框。

    属性:
        path_edit (QLineEdit): 显示/编辑当前配置路径。
        locked_label (QLabel): 环境变量锁定时的黄色警告横幅。
        btn_pick_path (QPushButton): 通过文件浏览器选择新路径的按钮。
        btn_reset (QPushButton): 重置到默认路径的按钮。
        btn_copy_path (QPushButton): 复制当前路径到剪贴板的按钮。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._changed = False
        self._last_applied_path = get_config_file()

        self.setWindowTitle(tr("dialog.config_path.title"))
        self.setMinimumWidth(520)
        self.setStyleSheet(get_dialog_stylesheet())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        card, card_layout = create_card()

        hint_label = QLabel(tr("dialog.config_path.hint"))
        hint_label.setWordWrap(True)
        hint_label.setStyleSheet(get_hint_block_style())
        card_layout.addWidget(hint_label)

        self.locked_label = QLabel(tr("tab.advanced.config_path_env_locked"))
        self.locked_label.setWordWrap(True)
        self.locked_label.setStyleSheet(get_warning_banner_style())
        card_layout.addWidget(self.locked_label)

        card_layout.addWidget(create_h_line())

        path_title = QLabel(tr("dialog.config_path.current_path_label"))
        path_title.setStyleSheet(get_card_title_style())
        card_layout.addWidget(path_title)

        path_row = QHBoxLayout()
        path_row.setSpacing(10)

        self.path_edit = QLineEdit()
        self.path_edit.setClearButtonEnabled(True)
        self.path_edit.returnPressed.connect(self.apply_path_from_input_with_notice)
        self.path_edit.editingFinished.connect(self.apply_path_from_input)
        path_row.addWidget(self.path_edit, 1)

        self.btn_pick_path = QPushButton()
        self.btn_pick_path.setObjectName("BtnIcon")
        self.btn_pick_path.setCursor(Qt.PointingHandCursor)
        self.btn_pick_path.setToolTip(tr("dialog.config_path.change_btn"))
        folder_icon_path = resource_path(os.path.join("FlowScroll", "resources", "ic_folder.svg"))
        if os.path.exists(folder_icon_path):
            self.btn_pick_path.setIcon(QIcon(folder_icon_path))
            self.btn_pick_path.setIconSize(QSize(18, 18))
        else:
            self.btn_pick_path.setText("...")
        self.btn_pick_path.clicked.connect(self.choose_path)
        path_row.addWidget(self.btn_pick_path)

        card_layout.addLayout(path_row)

        layout.addWidget(card)
        layout.addStretch()

        self.btn_reset = QPushButton(tr("tab.advanced.config_path_reset_btn"))
        self.btn_reset.setObjectName("BtnDanger")
        self.btn_reset.setCursor(Qt.PointingHandCursor)
        self.btn_reset.clicked.connect(self.reset_to_default)
        self.btn_reset.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.btn_reset)

        self.btn_copy_path = QPushButton(tr("dialog.config_path.copy_btn"))
        self.btn_copy_path.setObjectName("BtnPrimary")
        self.btn_copy_path.setCursor(Qt.PointingHandCursor)
        self.btn_copy_path.clicked.connect(self.copy_current_path)
        self.btn_copy_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.btn_copy_path)

        self.refresh_state()
        self.resize(560, max(260, self.sizeHint().height()))

    def _save_parent_config(self, target_path: str) -> bool:
        """通知父窗口（通常为 :class:`MainWindow`）持久化当前配置。"""
        parent = self.parent()
        if parent is not None and hasattr(parent, "save_presets_to_file"):
            return bool(parent.save_presets_to_file(target_path))
        return False

    def _apply_path(self, path: str | None) -> bool:
        """写入指针文件，更新内部状态，并刷新界面。

        参数:
            path: 新的配置路径（绝对路径字符串），或 ``None`` 表示重置为默认。
        """
        target_path = normalize_config_file_path(path) if path else get_default_config_file()
        if not self._save_parent_config(target_path):
            return False

        try:
            set_persisted_config_file(path)
        except OSError:
            QMessageBox.warning(
                self,
                tr("main.settings_failed.title"),
                tr("main.settings_failed.body"),
            )
            return False

        self._changed = True
        self._last_applied_path = get_config_file()
        self.refresh_state()
        return True

    def refresh_state(self) -> None:
        """根据当前路径来源（环境变量/自定义/默认）刷新控件启用/禁用状态。"""
        source = get_config_override_source()
        env_override = source.startswith("env_")

        if self.path_edit.text().strip() != self._last_applied_path:
            self.path_edit.setText(self._last_applied_path)
        self.locked_label.setVisible(env_override)
        self.btn_pick_path.setEnabled(not env_override)
        self.path_edit.setEnabled(not env_override)
        self.btn_reset.setEnabled(source == "custom")
        self.btn_copy_path.setEnabled(True)

    def choose_path(self) -> None:
        """弹出保存对话框让用户选择新的配置文件路径并应用。"""
        selected_path, _ = QFileDialog.getSaveFileName(
            self,
            tr("tab.advanced.config_path_dialog_title"),
            get_config_file(),
            tr("tab.advanced.config_path_dialog_filter"),
        )
        if not selected_path:
            return

        if not self._apply_path(selected_path):
            return
        QMessageBox.information(
            self,
            tr("webdav.success_title"),
            tr("tab.advanced.config_path_changed", path=get_config_file()),
        )

    def apply_path_from_input(self) -> bool:
        """读取文本框中的路径并写入指针文件。

        返回:
            bool: ``True`` 表示路径已变更；``False`` 表示与上次相同，未变更。
        """
        text = self.path_edit.text().strip()
        if not text or text == self._last_applied_path:
            self.path_edit.setText(self._last_applied_path)
            return False
        return self._apply_path(text)

    def apply_path_from_input_with_notice(self) -> None:
        """在 :meth:`apply_path_from_input` 基础上，成功时弹出信息提示。"""
        if not self.apply_path_from_input():
            return
        QMessageBox.information(
            self,
            tr("webdav.success_title"),
            tr("tab.advanced.config_path_changed", path=get_config_file()),
        )

    def reset_to_default(self) -> None:
        """清除自定义路径指针文件并恢复为平台默认配置路径。"""
        if get_config_override_source() != "custom":
            return

        if not self._apply_path(None):
            return
        QMessageBox.information(
            self,
            tr("webdav.success_title"),
            tr("tab.advanced.config_path_reset_done", path=get_config_file()),
        )

    def copy_current_path(self) -> None:
        """将当前配置路径复制到系统剪贴板，并弹出成功提示。"""
        QApplication.clipboard().setText(self.path_edit.text().strip() or get_config_file())
        QMessageBox.information(
            self,
            tr("webdav.success_title"),
            tr("dialog.config_path.copy_done"),
        )
