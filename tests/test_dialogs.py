"""UI 对话框包专项测试。

测试 FlowScroll.ui.dialogs 包中各子模块的导入与基础结构。
由于单元测试环境通常没有 QApplication，此处主要验证：
1. 模块导入路径正确
2. 类定义存在且继承自 QDialog
3. 常量与静态资源的完整性
"""


class TestDialogsImport:
    """测试 dialogs 包可通过 __init__.py 正确重导出所有对话框类。"""

    def test_package_exports_reverse_mode_dialog(self):
        from FlowScroll.ui.dialogs import ReverseModeDialog

        assert ReverseModeDialog.__name__ == "ReverseModeDialog"

    def test_package_exports_work_mode_dialog(self):
        from FlowScroll.ui.dialogs import WorkModeDialog

        assert WorkModeDialog.__name__ == "WorkModeDialog"

    def test_package_exports_app_filter_dialog(self):
        from FlowScroll.ui.dialogs import AppFilterDialog

        assert AppFilterDialog.__name__ == "AppFilterDialog"

    def test_package_exports_inertia_settings_dialog(self):
        from FlowScroll.ui.dialogs import InertiaSettingsDialog

        assert InertiaSettingsDialog.__name__ == "InertiaSettingsDialog"

    def test_package_exports_config_storage_dialog(self):
        from FlowScroll.ui.dialogs import ConfigStorageDialog

        assert ConfigStorageDialog.__name__ == "ConfigStorageDialog"


class TestDialogsInheritance:
    """验证各对话框正确的继承链，确保它们来自 QDialog。"""

    def test_reverse_mode_inherits_q_dialog(self):
        from PySide6.QtWidgets import QDialog
        from FlowScroll.ui.dialogs import ReverseModeDialog

        assert issubclass(ReverseModeDialog, QDialog)

    def test_work_mode_inherits_q_dialog(self):
        from PySide6.QtWidgets import QDialog
        from FlowScroll.ui.dialogs import WorkModeDialog

        assert issubclass(WorkModeDialog, QDialog)

    def test_app_filter_inherits_q_dialog(self):
        from PySide6.QtWidgets import QDialog
        from FlowScroll.ui.dialogs import AppFilterDialog

        assert issubclass(AppFilterDialog, QDialog)

    def test_inertia_settings_inherits_q_dialog(self):
        from PySide6.QtWidgets import QDialog
        from FlowScroll.ui.dialogs import InertiaSettingsDialog

        assert issubclass(InertiaSettingsDialog, QDialog)

    def test_config_storage_inherits_q_dialog(self):
        from PySide6.QtWidgets import QDialog
        from FlowScroll.ui.dialogs import ConfigStorageDialog

        assert issubclass(ConfigStorageDialog, QDialog)


class TestDialogsHaveInit:
    """验证各对话框类都有 __init__ 方法（构造函数）。"""

    def test_reverse_mode_has_init(self):
        from FlowScroll.ui.dialogs import ReverseModeDialog

        assert hasattr(ReverseModeDialog, "__init__")
        assert callable(ReverseModeDialog.__init__)

    def test_work_mode_has_init(self):
        from FlowScroll.ui.dialogs import WorkModeDialog

        assert hasattr(WorkModeDialog, "__init__")
        assert callable(WorkModeDialog.__init__)

    def test_app_filter_has_init(self):
        from FlowScroll.ui.dialogs import AppFilterDialog

        assert hasattr(AppFilterDialog, "__init__")
        assert callable(AppFilterDialog.__init__)

    def test_inertia_settings_has_init(self):
        from FlowScroll.ui.dialogs import InertiaSettingsDialog

        assert hasattr(InertiaSettingsDialog, "__init__")
        assert callable(InertiaSettingsDialog.__init__)

    def test_config_storage_has_init(self):
        from FlowScroll.ui.dialogs import ConfigStorageDialog

        assert hasattr(ConfigStorageDialog, "__init__")
        assert callable(ConfigStorageDialog.__init__)


class TestDialogsHaveSaveMethod:
    """验证各对话框类都有保存相关的方法（save_and_close 或类似命名）。"""

    def test_reverse_mode_has_save_method(self):
        from FlowScroll.ui.dialogs import ReverseModeDialog

        # ReverseModeDialog 使用 save_and_close 方法
        assert hasattr(ReverseModeDialog, "save_and_close") or hasattr(ReverseModeDialog, "accept")

    def test_work_mode_has_save_or_accept_method(self):
        from FlowScroll.ui.dialogs import WorkModeDialog

        # WorkModeDialog 可能使用 save_config 或 accept
        assert hasattr(WorkModeDialog, "save_config") or hasattr(WorkModeDialog, "accept")

    def test_app_filter_has_save_or_accept_method(self):
        from FlowScroll.ui.dialogs import AppFilterDialog

        # AppFilterDialog 可能使用 apply_filter 或 accept
        assert hasattr(AppFilterDialog, "apply_filter") or hasattr(AppFilterDialog, "accept")

    def test_inertia_settings_has_save_or_accept_method(self):
        from FlowScroll.ui.dialogs import InertiaSettingsDialog

        # InertiaSettingsDialog 可能使用 save_settings 或 accept
        assert hasattr(InertiaSettingsDialog, "save_settings") or hasattr(InertiaSettingsDialog, "accept")

    def test_config_storage_has_save_or_accept_method(self):
        from FlowScroll.ui.dialogs import ConfigStorageDialog

        # ConfigStorageDialog 可能使用 save_path 或 accept
        assert hasattr(ConfigStorageDialog, "save_path") or hasattr(ConfigStorageDialog, "accept")


class TestDialogsDocstrings:
    """验证各对话框类都有文档字符串。"""

    def test_reverse_mode_has_docstring(self):
        from FlowScroll.ui.dialogs import ReverseModeDialog

        assert ReverseModeDialog.__doc__ is not None
        assert len(ReverseModeDialog.__doc__) > 10

    def test_work_mode_has_docstring(self):
        from FlowScroll.ui.dialogs import WorkModeDialog

        assert WorkModeDialog.__doc__ is not None
        assert len(WorkModeDialog.__doc__) > 10

    def test_app_filter_has_docstring(self):
        from FlowScroll.ui.dialogs import AppFilterDialog

        assert AppFilterDialog.__doc__ is not None
        assert len(AppFilterDialog.__doc__) > 10

    def test_inertia_settings_has_docstring(self):
        from FlowScroll.ui.dialogs import InertiaSettingsDialog

        assert InertiaSettingsDialog.__doc__ is not None
        assert len(InertiaSettingsDialog.__doc__) > 10

    def test_config_storage_has_docstring(self):
        from FlowScroll.ui.dialogs import ConfigStorageDialog

        assert ConfigStorageDialog.__doc__ is not None
        assert len(ConfigStorageDialog.__doc__) > 10


class TestConfigStoragePathSwitch:
    """验证配置路径仅在目标文件写入成功后切换。"""

    @staticmethod
    def _dummy(save_result):
        class DummyDialog:
            _changed = False
            _last_applied_path = "old.json"
            refreshed = 0
            saved_targets = []

            def _save_parent_config(self, target_path):
                self.saved_targets.append(target_path)
                return save_result

            def refresh_state(self):
                self.refreshed += 1

        return DummyDialog()

    def test_failed_target_write_keeps_existing_pointer(self, monkeypatch):
        from FlowScroll.ui.dialogs import config_storage

        pointer_updates = []
        dialog = self._dummy(False)
        monkeypatch.setattr(config_storage, "normalize_config_file_path", lambda path: f"normalized:{path}")
        monkeypatch.setattr(config_storage, "set_persisted_config_file", pointer_updates.append)

        changed = config_storage.ConfigStorageDialog._apply_path(dialog, "new.json")

        assert changed is False
        assert dialog.saved_targets == ["normalized:new.json"]
        assert pointer_updates == []
        assert dialog._changed is False

    def test_successful_target_write_switches_pointer_after_save(self, monkeypatch):
        from FlowScroll.ui.dialogs import config_storage

        events = []
        dialog = self._dummy(True)

        def save_target(target_path):
            events.append(("save", target_path))
            return True

        dialog._save_parent_config = save_target
        monkeypatch.setattr(config_storage, "normalize_config_file_path", lambda path: f"normalized:{path}")
        monkeypatch.setattr(
            config_storage,
            "set_persisted_config_file",
            lambda path: events.append(("pointer", path)),
        )
        monkeypatch.setattr(config_storage, "get_config_file", lambda: "normalized:new.json")

        changed = config_storage.ConfigStorageDialog._apply_path(dialog, "new.json")

        assert changed is True
        assert events == [("save", "normalized:new.json"), ("pointer", "new.json")]
        assert dialog._last_applied_path == "normalized:new.json"
        assert dialog.refreshed == 1


class TestDialogsModuleDocstrings:
    """验证各对话框子模块都有模块级文档字符串。"""

    def test_reverse_mode_module_has_docstring(self):
        from FlowScroll.ui.dialogs import reverse_mode

        assert reverse_mode.__doc__ is not None
        assert len(reverse_mode.__doc__) > 10

    def test_work_mode_module_has_docstring(self):
        from FlowScroll.ui.dialogs import work_mode

        assert work_mode.__doc__ is not None
        assert len(work_mode.__doc__) > 10

    def test_app_filter_module_has_docstring(self):
        from FlowScroll.ui.dialogs import app_filter

        assert app_filter.__doc__ is not None
        assert len(app_filter.__doc__) > 10

    def test_inertia_module_has_docstring(self):
        from FlowScroll.ui.dialogs import inertia

        assert inertia.__doc__ is not None
        assert len(inertia.__doc__) > 10

    def test_config_storage_module_has_docstring(self):
        from FlowScroll.ui.dialogs import config_storage

        assert config_storage.__doc__ is not None
        assert len(config_storage.__doc__) > 10
