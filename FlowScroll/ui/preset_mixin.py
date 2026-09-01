"""预设管理 Mixin。

将 MainWindow 中的预设管理方法提取到独立模块，
提供预设的查询、刷新、保存、删除等功能。

使用示例::

    class MainWindow(PresetMixin, QMainWindow):
        pass

    # 在主窗口中调用
    self.refresh_preset_combo()
    self.save_preset()
    self.delete_preset()
"""

from PySide6.QtWidgets import QMessageBox, QInputDialog

from FlowScroll.core.config import (
    BUILTIN_PRESETS,
    get_preset_display_name,
    get_preset_internal_name,
)
from FlowScroll.i18n import tr


class PresetMixin:
    """提供预设管理方法的 Mixin 基类。

    依赖:
        - self.combo_presets (QComboBox): 预设下拉选择框
        - self.ctrl.preset_manager: 预设管理器实例
        - self.ctrl.current_preset_name: 当前预设名称
        - self.ctrl.presets: 预设字典
        - self.ctrl.save_new_preset(name): 保存新预设
        - self.ctrl.delete_preset(name): 删除预设
        - self.ctrl.load_selected_preset(name): 加载预设
        - self.sync_ui_from_config(): 同步 UI 控件
        - self.refresh_config_storage_ui(): 刷新配置存储 UI
    """

    def _all_preset_names(self):
        """返回所有预设的本地化显示名称列表。"""
        return self.ctrl.preset_manager.get_all_display_names()

    def _refresh_combo(self, select_name):
        """刷新预设下拉框，选中指定名称（内部键名）。"""
        self.combo_presets.blockSignals(True)
        self.combo_presets.clear()
        self.combo_presets.addItems(self._all_preset_names())
        self.combo_presets.setCurrentText(get_preset_display_name(select_name))
        self.combo_presets.blockSignals(False)

    def _confirm_preset_action(self, title, text):
        """弹出确认对话框，返回用户是否选择"是"。"""
        reply = QMessageBox.question(
            self,
            title,
            text,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return reply == QMessageBox.Yes

    def save_new_preset(self, text: str) -> None:
        """
        保存新预设，如果预设名称已存在则覆盖。
        """
        if not text or text in BUILTIN_PRESETS:
            return

        # 检查是否与现有自定义预设冲突
        if text in self.ctrl.preset_manager.presets:
            reply = QMessageBox.question(
                self,
                tr("main.preset.overwrite_title"),
                tr("main.preset.overwrite_body", name=text),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self.ctrl.preset_manager.save_preset(text)
        self.save_presets_to_file()
        self._refresh_combo_presets()

    def delete_preset(self) -> None:
        """删除当前选中的预设。

        如果选中的是内置预设，则警告用户不能删除内置预设。
        如果是自定义预设，则请求确认。
        """
        current_text = self.combo_presets.currentText()
        internal_name = get_preset_internal_name(current_text)

        # 检查是否为内置预设
        if internal_name in BUILTIN_PRESETS:
            QMessageBox.warning(
                self,
                tr("main.preset.delete_builtin_title"),
                tr("main.preset.delete_builtin_body"),
            )
            return

        # 请求确认
        reply = QMessageBox.question(
            self,
            tr("main.preset.delete_confirm_title"),
            tr("main.preset.delete_confirm_body", name=current_text),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # 删除预设
        self.ctrl.preset_manager.delete_preset(internal_name)
        self.save_presets_to_file()
        self._refresh_combo_presets()

    def load_selected_preset(self, display_name: str) -> None:
        """加载用户从下拉框选中的预设。

        将显示名称转换为内部名称，然后通知控制器加载预设并同步 UI 控件。
        ``display_name`` 为空时视为无效选择（通常由 combo.clear() 触发），
        直接跳过以避免报错。

        参数:
            display_name: 预设的显示名称（来自下拉框的 currentText）
        """
        if not display_name:
            return
        internal_name = get_preset_internal_name(display_name)
        self.ctrl.load_selected_preset(internal_name)
        self.sync_ui_from_config()
        self._refresh_combo_presets()

    def _refresh_combo_presets(self) -> None:
        """刷新预设下拉框，使其与当前的预设列表同步。

        重新填充下拉框，并选中当前加载的预设。
        clear/addItems/setCurrentIndex 期间使用 blockSignals，避免
        触发 currentTextChanged → load_selected_preset 导致的递归调用。
        """
        display_names = self.ctrl.preset_manager.get_all_display_names()
        current_internal = self.ctrl.preset_manager.current_preset_name

        self.combo_presets.blockSignals(True)
        try:
            self.combo_presets.clear()
            self.combo_presets.addItems(display_names)

            # 选中当前预设
            current_display = get_preset_display_name(current_internal)
            index = self.combo_presets.findText(current_display)
            if index >= 0:
                self.combo_presets.setCurrentIndex(index)
        finally:
            self.combo_presets.blockSignals(False)

    def prompt_new_preset_name(self) -> str:
        """弹出输入对话框让用户输入新预设名称。

        返回:
            用户输入的预设名称，如果用户取消则返回空字符串
        """
        text, ok = QInputDialog.getText(
            self,
            tr("main.preset.save_title"),
            tr("main.preset.save_prompt"),
        )
        return text.strip() if ok else ""
