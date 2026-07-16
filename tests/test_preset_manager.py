"""preset_manager.py 的回归测试。

补充 test_config.py::TestPresetManager 未覆盖的边界：
- save_preset 与 delete_preset 的返回值语义
- get_all_names / get_all_display_names 的列表合并
- _serialize_state 结构完整性
- PresetManager 初始化默认值
- 自定义预设的完整保存-加载往返
"""

import json


from FlowScroll.core.config import (
    BUILTIN_PRESETS,
    DEFAULT_PRESET_NAME,
    cfg,
)
from FlowScroll.core.config import STATE_LOCK
from FlowScroll.ui.preset_manager import PresetManager


class TestPresetManagerDefaults:
    """新建的 PresetManager 应处于干净的初始状态。"""

    def test_new_manager_has_empty_presets_dict(self):
        mgr = PresetManager()
        assert mgr.presets == {}

    def test_new_manager_current_name_is_default(self):
        mgr = PresetManager()
        assert mgr.current_preset_name == DEFAULT_PRESET_NAME

    def test_default_preset_name_is_builtin(self):
        assert DEFAULT_PRESET_NAME in BUILTIN_PRESETS


# ---- save_preset / delete_preset 返回值 ----


class TestSaveDeleteReturnValues:
    """验证 save_preset / delete_preset 的成功与失败条件。"""

    def test_save_preset_returns_false_for_builtin_names(self, tmp_path, monkeypatch):
        """试图覆盖内置预设名时应返回 False 且不落盘。"""
        mgr = PresetManager()
        # 将配置文件重定向到 tmp_path，避免污染真实磁盘
        fake_config = tmp_path / "FlowScroll_config.json"
        monkeypatch.setattr("FlowScroll.ui.preset_manager.get_config_file", lambda: str(fake_config))
        monkeypatch.setattr("FlowScroll.ui.preset_manager.ensure_config_dir", lambda: str(fake_config))

        for name in BUILTIN_PRESETS:
            assert mgr.save_preset(name) is False
        assert mgr.presets == {}  # 内置预设未被"保存"

    def test_save_preset_returns_true_for_custom_name(self, tmp_path, monkeypatch):
        mgr = PresetManager()
        fake_config = tmp_path / "FlowScroll_config.json"
        monkeypatch.setattr("FlowScroll.ui.preset_manager.get_config_file", lambda: str(fake_config))
        monkeypatch.setattr("FlowScroll.ui.preset_manager.ensure_config_dir", lambda: str(fake_config))

        assert mgr.save_preset("我的预设") is True
        assert "我的预设" in mgr.presets
        assert mgr.current_preset_name == "我的预设"

    def test_delete_preset_returns_false_for_builtin(self, tmp_path, monkeypatch):
        mgr = PresetManager()
        fake_config = tmp_path / "FlowScroll_config.json"
        monkeypatch.setattr("FlowScroll.ui.preset_manager.get_config_file", lambda: str(fake_config))
        monkeypatch.setattr("FlowScroll.ui.preset_manager.ensure_config_dir", lambda: str(fake_config))

        for name in BUILTIN_PRESETS:
            assert mgr.delete_preset(name) is False

    def test_delete_preset_returns_false_for_missing_custom(self, tmp_path, monkeypatch):
        mgr = PresetManager()
        fake_config = tmp_path / "FlowScroll_config.json"
        monkeypatch.setattr("FlowScroll.ui.preset_manager.get_config_file", lambda: str(fake_config))
        monkeypatch.setattr("FlowScroll.ui.preset_manager.ensure_config_dir", lambda: str(fake_config))

        assert mgr.delete_preset("不存在") is False

    def test_delete_preset_returns_true_for_existing_custom(self, tmp_path, monkeypatch):
        mgr = PresetManager()
        fake_config = tmp_path / "FlowScroll_config.json"
        monkeypatch.setattr("FlowScroll.ui.preset_manager.get_config_file", lambda: str(fake_config))
        monkeypatch.setattr("FlowScroll.ui.preset_manager.ensure_config_dir", lambda: str(fake_config))

        mgr.save_preset("to_remove")
        assert "to_remove" in mgr.presets

        assert mgr.delete_preset("to_remove") is True
        assert "to_remove" not in mgr.presets
        assert mgr.current_preset_name == DEFAULT_PRESET_NAME


# ---- load_preset 行为 ----


class TestLoadPreset:
    """验证切换预设时的行为。"""

    def test_load_preset_builtin(self):
        """加载内置预设应更新 cfg 并返回 True。"""
        # 记录初始 sensitivity
        original = cfg.sensitivity
        try:
            with STATE_LOCK:
                cfg.sensitivity = 0.0001  # 人为设置一个异常值便于后续断言

            mgr = PresetManager()
            # 选一个非默认的内置预设
            non_default = next(k for k in BUILTIN_PRESETS if k != DEFAULT_PRESET_NAME)
            result = mgr.load_preset(non_default)
            assert result is True
            assert mgr.current_preset_name == non_default
            # cfg 应被覆写为该内置预设的值
            assert cfg.sensitivity == BUILTIN_PRESETS[non_default]["sensitivity"]
        finally:
            # 还原
            with STATE_LOCK:
                cfg.sensitivity = original

    def test_load_preset_custom_after_save(self, tmp_path, monkeypatch):
        """保存自定义预设后再加载，其配置应完全保留。"""
        fake_config = tmp_path / "FlowScroll_config.json"
        monkeypatch.setattr("FlowScroll.ui.preset_manager.get_config_file", lambda: str(fake_config))
        monkeypatch.setattr("FlowScroll.ui.preset_manager.ensure_config_dir", lambda: str(fake_config))

        original_sensitivity = cfg.sensitivity
        try:
            mgr = PresetManager()
            # 设置一个独特值并保存为自定义预设
            with STATE_LOCK:
                cfg.sensitivity = 4.25
            mgr.save_preset("special_preset")

            # 修改 cfg 使其与刚保存的预设不一致
            with STATE_LOCK:
                cfg.sensitivity = 1.0

            # 加载回 special_preset，sensitivity 应恢复为 4.25
            assert mgr.load_preset("special_preset") is True
            assert cfg.sensitivity == 4.25
        finally:
            with STATE_LOCK:
                cfg.sensitivity = original_sensitivity

    def test_load_preset_unknown_returns_false(self):
        mgr = PresetManager()
        result = mgr.load_preset("definitely_not_registered")
        assert result is False


# ---- 序列化结构 ----


class TestSerializeState:
    def test_serialize_state_has_all_required_keys(self, tmp_path, monkeypatch):
        fake_config = tmp_path / "FlowScroll_config.json"
        monkeypatch.setattr("FlowScroll.ui.preset_manager.get_config_file", lambda: str(fake_config))
        monkeypatch.setattr("FlowScroll.ui.preset_manager.ensure_config_dir", lambda: str(fake_config))

        mgr = PresetManager()
        mgr.save_preset("custom_a")
        state = mgr._serialize_state()

        expected_keys = {"presets", "last_used", "current_config", "webdav"}
        assert expected_keys.issubset(set(state.keys()))
        assert "custom_a" in state["presets"]
        assert state["last_used"] == "custom_a"
        assert isinstance(state["current_config"], dict)
        assert isinstance(state["webdav"], dict)


# ---- 列表查询 ----


class TestGetAllNames:
    def test_get_all_names_includes_builtin_and_custom(self, tmp_path, monkeypatch):
        fake_config = tmp_path / "FlowScroll_config.json"
        monkeypatch.setattr("FlowScroll.ui.preset_manager.get_config_file", lambda: str(fake_config))
        monkeypatch.setattr("FlowScroll.ui.preset_manager.ensure_config_dir", lambda: str(fake_config))

        mgr = PresetManager()
        mgr.save_preset("user_aaa")
        mgr.save_preset("user_bbb")

        names = mgr.get_all_names()
        # 全部内置都在
        for builtin in BUILTIN_PRESETS:
            assert builtin in names
        # 自定义也在
        assert "user_aaa" in names
        assert "user_bbb" in names

    def test_get_all_display_names_length_matches_names(self, tmp_path, monkeypatch):
        fake_config = tmp_path / "FlowScroll_config.json"
        monkeypatch.setattr("FlowScroll.ui.preset_manager.get_config_file", lambda: str(fake_config))
        monkeypatch.setattr("FlowScroll.ui.preset_manager.ensure_config_dir", lambda: str(fake_config))

        mgr = PresetManager()
        mgr.save_preset("my_preset")

        names = mgr.get_all_names()
        display_names = mgr.get_all_display_names()
        assert len(names) == len(display_names)


# ---- atomic write ----


class TestAtomicWrite:
    def test_save_to_file_produces_valid_json(self, tmp_path, monkeypatch):
        fake_config = tmp_path / "FlowScroll_config.json"
        monkeypatch.setattr("FlowScroll.ui.preset_manager.get_config_file", lambda: str(fake_config))
        # ensure_config_dir 在 preset_manager 里被直接导入，
        # 必须返回目标文件路径（不是目录），因为 save_to_file 用它作为写入目标。
        monkeypatch.setattr("FlowScroll.ui.preset_manager.ensure_config_dir", lambda: str(fake_config))

        mgr = PresetManager()
        mgr.save_preset("roundtrip")
        assert mgr.save_to_file() is True

        assert fake_config.exists()
        with open(fake_config, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "presets" in data
        assert data["last_used"] == "roundtrip"
        assert "roundtrip" in data["presets"]

        # 没有残留 *.tmp 文件（原子写入应在成功后清除临时文件）
        tmp_files = list(tmp_path.glob("*.tmp"))
        assert tmp_files == []

    def test_save_to_file_can_target_new_path(self, tmp_path):
        target = tmp_path / "nested" / "migrated.json"
        mgr = PresetManager()

        assert mgr.save_to_file(str(target)) is True
        assert target.exists()

    def test_save_to_file_reports_atomic_replace_failure(self, tmp_path, monkeypatch):
        target = tmp_path / "FlowScroll_config.json"
        target.write_text('{"existing": true}', encoding="utf-8")
        monkeypatch.setattr(
            "FlowScroll.ui.preset_manager.os.replace",
            lambda *_args: (_ for _ in ()).throw(PermissionError("read only")),
        )
        mgr = PresetManager()

        assert mgr.save_to_file(str(target)) is False
        assert target.read_text(encoding="utf-8") == '{"existing": true}'
        assert list(tmp_path.glob("*.tmp")) == []
