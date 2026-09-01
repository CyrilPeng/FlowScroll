"""配置系统与 RuntimeState 测试。"""

import os
import json
import tempfile
from pathlib import Path

import pytest


class TestGlobalConfig:
    """测试 GlobalConfig 的路径解析、默认值、序列化与迁移逻辑。"""

    def test_default_windows_config_dir_uses_appdata(self, monkeypatch):
        import FlowScroll.core.config as config_module

        monkeypatch.setattr(config_module.os, "name", "nt")
        monkeypatch.setattr(config_module.os.sys, "platform", "win32")
        monkeypatch.setenv("APPDATA", r"C:\Users\Test\AppData\Roaming")

        assert config_module.get_default_config_dir() == (r"C:\Users\Test\AppData\Roaming\FlowScroll")

    def test_path_module_tracks_platform_monkeypatch(self, monkeypatch):
        """路径模块不能缓存宿主平台，否则跨平台测试会被执行顺序污染。"""
        import FlowScroll.core.config as config_module

        monkeypatch.setattr(config_module.os, "name", "posix")
        monkeypatch.setattr(config_module.os.sys, "platform", "linux")
        assert config_module._join_path("/tmp", "FlowScroll") == "/tmp/FlowScroll"

        monkeypatch.setattr(config_module.os, "name", "nt")
        monkeypatch.setattr(config_module.os.sys, "platform", "win32")
        assert (
            config_module._join_path(r"C:\Users\Test\AppData\Roaming", "FlowScroll")
            == r"C:\Users\Test\AppData\Roaming\FlowScroll"
        )

    def test_join_path_prefers_windows_style_base_path(self):
        """即使宿主是 POSIX，Windows 风格基路径也应使用 ntpath 拼接。"""
        import FlowScroll.core.config as config_module

        assert (
            config_module._join_path(r"C:\Users\Test\AppData\Roaming", "FlowScroll")
            == r"C:\Users\Test\AppData\Roaming\FlowScroll"
        )

    def test_custom_config_file_env_overrides_default(self, monkeypatch):
        import FlowScroll.core.config as config_module

        monkeypatch.delenv(config_module.CONFIG_DIR_ENV_VAR, raising=False)
        monkeypatch.setenv(
            config_module.CONFIG_FILE_ENV_VAR,
            r"D:\Portable\FlowScroll\custom.json",
        )

        assert config_module.get_config_file() == r"D:\Portable\FlowScroll\custom.json"

    def test_custom_config_dir_env_builds_windows_path(self, monkeypatch):
        import FlowScroll.core.config as config_module

        monkeypatch.delenv(config_module.CONFIG_FILE_ENV_VAR, raising=False)
        monkeypatch.setenv(
            config_module.CONFIG_DIR_ENV_VAR,
            r"D:\Portable\FlowScroll",
        )

        assert config_module.get_config_file() == (r"D:\Portable\FlowScroll\FlowScroll_config.json")

    def test_persisted_config_pointer_overrides_default(self, monkeypatch, tmp_path):
        import FlowScroll.core.config as config_module

        pointer_file = tmp_path / "config_path.json"
        default_file = tmp_path / "FlowScroll" / "FlowScroll_config.json"
        custom_file = tmp_path / "Portable" / "FlowScroll.json"

        monkeypatch.delenv(config_module.CONFIG_FILE_ENV_VAR, raising=False)
        monkeypatch.delenv(config_module.CONFIG_DIR_ENV_VAR, raising=False)
        monkeypatch.setattr(config_module, "CONFIG_FILE", str(default_file))
        monkeypatch.setattr(config_module, "get_config_pointer_file", lambda: str(pointer_file))

        config_module.set_persisted_config_file(str(custom_file))

        assert config_module.get_persisted_config_file() == str(custom_file.resolve())
        assert config_module.get_config_file() == str(custom_file.resolve())
        assert config_module.get_config_override_source() == "custom"

    def test_resetting_persisted_config_pointer_returns_to_default(self, monkeypatch, tmp_path):
        import FlowScroll.core.config as config_module

        pointer_file = tmp_path / "config_path.json"
        default_file = tmp_path / "FlowScroll" / "FlowScroll_config.json"
        custom_file = tmp_path / "Portable" / "FlowScroll.json"

        monkeypatch.delenv(config_module.CONFIG_FILE_ENV_VAR, raising=False)
        monkeypatch.delenv(config_module.CONFIG_DIR_ENV_VAR, raising=False)
        monkeypatch.setattr(config_module, "CONFIG_FILE", str(default_file))
        monkeypatch.setattr(config_module, "get_config_pointer_file", lambda: str(pointer_file))

        config_module.set_persisted_config_file(str(custom_file))
        config_module.set_persisted_config_file(None)

        assert config_module.get_persisted_config_file() == ""
        assert config_module.get_config_file() == str(default_file.resolve())
        assert config_module.get_config_override_source() == "default"

    def test_default_values(self):
        from FlowScroll.core.config import GlobalConfig

        c = GlobalConfig()
        assert c.sensitivity == 2.0
        assert c.speed_factor == 2.0
        assert c.dead_zone == 20.0
        assert c.enable_horizontal is True
        assert c.enable_inertia is False
        assert c.activation_mode == 0
        assert c.activation_compat_mode is False
        assert c.activation_delay_ms == 0
        assert c.ui_language == "auto"

    def test_to_dict_roundtrip(self):
        from FlowScroll.core.config import GlobalConfig

        c = GlobalConfig()
        c.sensitivity = 3.5
        c.speed_factor = 1.0
        c.reverse_y = True
        c.activation_compat_mode = True
        c.activation_delay_ms = 180
        c.ui_language = "en-US"

        d = c.to_dict()
        c2 = GlobalConfig()
        c2.from_dict(d)

        assert c2.sensitivity == 3.5
        assert c2.speed_factor == 1.0
        assert c2.reverse_y is True
        assert c2.activation_compat_mode is True
        assert c2.activation_delay_ms == 180
        assert c2.ui_language == "en-US"

    def test_to_dict_excludes_webdav_settings(self):
        from FlowScroll.core.config import GlobalConfig

        c = GlobalConfig()
        c.webdav_url = "https://example.com/dav/"
        c.webdav_username = "user"

        d = c.to_dict()
        assert "webdav_url" not in d
        assert "webdav_username" not in d

    def test_to_dict_for_sync_excludes_webdav_settings(self):
        from FlowScroll.core.config import GlobalConfig

        c = GlobalConfig()
        c.webdav_url = "https://example.com/dav/"
        c.webdav_username = "user"

        d = c.to_dict_for_sync()
        assert d == c.to_dict()
        assert "webdav_url" not in d
        assert "webdav_username" not in d

    def test_preset_display_name_follows_language_change(self):
        from FlowScroll.core.config import GlobalConfig, get_preset_display_name
        import FlowScroll.core.config as config_module

        original_cfg = config_module.cfg
        try:
            config_module.cfg = GlobalConfig()
            config_module.cfg.ui_language = "en-US"
            assert get_preset_display_name("网页阅读") == "Web Reading"

            config_module.cfg.ui_language = "zh-CN"
            assert get_preset_display_name("网页阅读") == "网页阅读"
        finally:
            config_module.cfg = original_cfg

    def test_webdav_settings_roundtrip(self):
        from FlowScroll.core.config import GlobalConfig

        c = GlobalConfig()
        c.webdav_url = "https://example.com/dav/"
        c.webdav_username = "alice"

        d = c.to_webdav_dict()
        c2 = GlobalConfig()
        c2.from_webdav_dict(d)

        assert c2.webdav_url == "https://example.com/dav/"
        assert c2.webdav_username == "alice"

    def test_from_dict_missing_keys_use_defaults(self):
        from FlowScroll.core.config import GlobalConfig

        c = GlobalConfig()
        c.from_dict({"sensitivity": 9.0})
        assert c.sensitivity == 9.0
        assert c.speed_factor == 2.0
        assert c.dead_zone == 20.0

    def test_from_dict_rejects_invalid_values_without_partial_mutation(self):
        from FlowScroll.core.config import GlobalConfig

        c = GlobalConfig()
        c.sensitivity = 4.0
        before = c.to_dict()

        with pytest.raises(ValueError, match="activation_delay_ms"):
            c.from_dict(
                {
                    "sensitivity": 3.0,
                    "activation_delay_ms": "invalid",
                }
            )

        assert c.to_dict() == before

    @pytest.mark.parametrize(
        "payload",
        [
            {"sensitivity": float("nan")},
            {"dead_zone": -1},
            {"enable_horizontal": "yes"},
            {"activation_mode": 2},
            {"filter_blacklist": "chrome"},
            {"filter_whitelist": ["chrome", 123]},
            {"ui_language": "unknown"},
        ],
    )
    def test_from_dict_rejects_unsafe_shapes(self, payload):
        from FlowScroll.core.config import GlobalConfig

        with pytest.raises(ValueError):
            GlobalConfig().from_dict(payload)

    def test_to_dict_contains_all_expected_fields(self):
        """to_dict 应包含所有持久化字段，且值正确。"""
        from FlowScroll.core.config import GlobalConfig

        c = GlobalConfig()
        c.sensitivity = 3.0
        c.reverse_x = True
        d = c.to_dict()
        assert d["sensitivity"] == 3.0
        assert d["reverse_x"] is True
        # 确保不含 WebDAV 凭据
        assert "webdav_url" not in d
        assert "webdav_username" not in d


class TestRuntimeState:
    """测试 RuntimeState 的默认值与窗口信息过期判定。"""

    def test_defaults(self):
        from FlowScroll.core.config import RuntimeState

        r = RuntimeState()
        assert r.active is False
        assert r.origin_pos == (0, 0)
        assert r.current_window_name == ""
        assert r.current_process_name == ""
        assert r.process_name_status == "unknown"
        assert r.last_match_target == ""
        assert r.window_info_failure_count == 0
        assert r.is_fullscreen is False

    def test_runtime_is_separate_from_config(self):
        from FlowScroll.core.config import GlobalConfig, RuntimeState

        c = GlobalConfig()
        r = RuntimeState()
        r.active = True
        r.current_window_name = "TestApp"
        r.current_process_name = "testapp"

        assert not hasattr(c, "active") or c.__dict__.get("active", None) is None


class TestBuiltinPresets:
    """测试内置预设的完整性与共享默认值。"""

    def test_all_presets_have_required_keys(self):
        from FlowScroll.core.config import BUILTIN_PRESETS

        required = {"sensitivity", "speed_factor", "dead_zone", "overlay_size"}
        for name, preset in BUILTIN_PRESETS.items():
            assert required.issubset(preset.keys()), f"预设 '{name}' 缺少字段: {required - preset.keys()}"

    def test_default_preset_exists(self):
        from FlowScroll.core.config import BUILTIN_PRESETS, DEFAULT_PRESET_NAME

        assert DEFAULT_PRESET_NAME in BUILTIN_PRESETS

    def test_all_presets_share_common_defaults(self):
        """验证 _PRESET_DEFAULTS 已正确合并到所有预设中。"""
        from FlowScroll.core.config import BUILTIN_PRESETS, _PRESET_DEFAULTS

        for name, preset in BUILTIN_PRESETS.items():
            for key in _PRESET_DEFAULTS:
                assert key in preset, f"预设 '{name}' 缺少公共字段 '{key}'"


class TestPresetManager:
    """测试 PresetManager 的保存、加载、删除与序列化逻辑。"""

    def _make_temp_config(self, data):
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        return path

    def test_load_and_save_roundtrip(self, monkeypatch):
        import FlowScroll.core.config as config_module
        from FlowScroll.ui.preset_manager import PresetManager

        presets_data = {
            "presets": {
                "MyPreset": {
                    "sensitivity": 3.0,
                    "speed_factor": 1.5,
                    "dead_zone": 10.0,
                    "overlay_size": 50.0,
                }
            },
            "last_used": "MyPreset",
        }
        path = self._make_temp_config(presets_data)

        try:
            monkeypatch.setattr(config_module, "CONFIG_FILE", path)
            pm = PresetManager()
            pm.load_from_file()
            assert pm.current_preset_name == "MyPreset"
            assert "MyPreset" in pm.presets
        finally:
            os.unlink(path)

    def test_load_failure_clears_stale_presets(self, monkeypatch):
        import FlowScroll.core.config as config_module
        from FlowScroll.ui.preset_manager import PresetManager

        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        with open(path, "w", encoding="utf-8") as f:
            f.write("{ invalid json")

        try:
            monkeypatch.setattr(config_module, "CONFIG_FILE", path)
            pm = PresetManager()
            pm.presets = {"StalePreset": {"sensitivity": 3.0}}
            pm.current_preset_name = "StalePreset"

            pm.load_from_file()

            assert pm.presets == {}
            assert pm.current_preset_name == config_module.DEFAULT_PRESET_NAME
            assert pm.last_recovery_backup_path is not None
            assert os.path.exists(pm.last_recovery_backup_path)
            with open(pm.last_recovery_backup_path, "r", encoding="utf-8") as f:
                assert f.read() == "{ invalid json"
            with open(path, "r", encoding="utf-8") as f:
                assert isinstance(json.load(f), dict)
        finally:
            if os.path.exists(path):
                os.unlink(path)
            for backup in Path(path).parent.glob(f"{Path(path).name}.invalid-*.bak*"):
                backup.unlink()

    def test_save_includes_current_config(self, monkeypatch):
        import FlowScroll.core.config as config_module
        from FlowScroll.core.config import cfg
        from FlowScroll.ui.preset_manager import PresetManager

        path = self._make_temp_config({"presets": {}, "last_used": config_module.DEFAULT_PRESET_NAME})

        try:
            monkeypatch.setattr(config_module, "CONFIG_FILE", path)
            cfg.sensitivity = 4.0
            cfg.speed_factor = 1.25
            cfg.webdav_url = "https://example.com/dav/"
            cfg.webdav_username = "alice"

            pm = PresetManager()
            pm.save_to_file()

            with open(path, "r", encoding="utf-8") as f:
                saved = json.load(f)

            assert saved["current_config"]["sensitivity"] == 4.0
            assert saved["current_config"]["speed_factor"] == 1.25
            assert "webdav_url" not in saved["current_config"]
            assert saved["webdav"] == {
                "url": "https://example.com/dav/",
                "username": "alice",
            }
        finally:
            os.unlink(path)

    def test_load_prefers_current_config_when_present(self, monkeypatch):
        import FlowScroll.core.config as config_module
        from FlowScroll.ui.preset_manager import PresetManager

        path = self._make_temp_config(
            {
                "presets": {},
                "last_used": config_module.DEFAULT_PRESET_NAME,
                "current_config": {
                    "sensitivity": 4.5,
                    "speed_factor": 1.75,
                    "dead_zone": 12.0,
                    "overlay_size": 50.0,
                    "enable_horizontal": False,
                },
            }
        )

        try:
            monkeypatch.setattr(config_module, "CONFIG_FILE", path)
            pm = PresetManager()

            pm.load_from_file()

            assert pm.current_preset_name == config_module.DEFAULT_PRESET_NAME
            assert config_module.cfg.sensitivity == 4.5
            assert config_module.cfg.speed_factor == 1.75
            assert config_module.cfg.enable_horizontal is False
        finally:
            os.unlink(path)

    def test_load_restores_separate_webdav_settings(self, monkeypatch):
        import FlowScroll.core.config as config_module
        from FlowScroll.ui.preset_manager import PresetManager

        path = self._make_temp_config(
            {
                "presets": {},
                "last_used": config_module.DEFAULT_PRESET_NAME,
                "current_config": {
                    "sensitivity": 4.5,
                    "speed_factor": 1.75,
                },
                "webdav": {
                    "url": "https://dav.example.com/root/",
                    "username": "alice",
                },
            }
        )

        try:
            monkeypatch.setattr(config_module, "CONFIG_FILE", path)
            pm = PresetManager()

            pm.load_from_file()

            assert config_module.cfg.sensitivity == 4.5
            assert config_module.cfg.webdav_url == "https://dav.example.com/root/"
            assert config_module.cfg.webdav_username == "alice"
        finally:
            os.unlink(path)

    def test_load_migrates_legacy_webdav_settings(self, monkeypatch):
        import FlowScroll.core.config as config_module
        from FlowScroll.ui.preset_manager import PresetManager

        path = self._make_temp_config(
            {
                "presets": {},
                "last_used": config_module.DEFAULT_PRESET_NAME,
                "current_config": {
                    "sensitivity": 4.5,
                    "webdav_url": "https://legacy.example.com/dav/",
                    "webdav_username": "bob",
                },
            }
        )

        try:
            monkeypatch.setattr(config_module, "CONFIG_FILE", path)
            pm = PresetManager()

            pm.load_from_file()

            assert config_module.cfg.sensitivity == 4.5
            assert config_module.cfg.webdav_url == "https://legacy.example.com/dav/"
            assert config_module.cfg.webdav_username == "bob"
        finally:
            os.unlink(path)

    def test_invalid_preset_structure_falls_back_to_defaults(self, monkeypatch):
        import FlowScroll.core.config as config_module
        from FlowScroll.ui.preset_manager import PresetManager

        path = self._make_temp_config({"presets": [], "last_used": []})

        try:
            monkeypatch.setattr(config_module, "CONFIG_FILE", path)
            pm = PresetManager()

            pm.load_from_file()

            assert pm.presets == {}
            assert pm.current_preset_name == config_module.DEFAULT_PRESET_NAME
            assert pm.last_recovery_backup_path is not None
            assert os.path.exists(pm.last_recovery_backup_path)
        finally:
            if os.path.exists(path):
                os.unlink(path)
            for backup in Path(path).parent.glob(f"{Path(path).name}.invalid-*.bak*"):
                backup.unlink()

    def test_invalid_config_backup_failure_preserves_original(self, monkeypatch):
        import FlowScroll.core.config as config_module
        import FlowScroll.ui.preset_manager as preset_manager_module
        from FlowScroll.ui.preset_manager import PresetManager

        path = self._make_temp_config({"presets": []})
        original = Path(path).read_text(encoding="utf-8")
        monkeypatch.setattr(config_module, "CONFIG_FILE", path)
        monkeypatch.setattr(
            preset_manager_module.os,
            "replace",
            lambda *_args: (_ for _ in ()).throw(PermissionError("read only")),
        )

        try:
            pm = PresetManager()
            pm.load_from_file()

            assert pm.last_recovery_backup_path is None
            assert Path(path).read_text(encoding="utf-8") == original
            assert pm.current_preset_name == config_module.DEFAULT_PRESET_NAME
        finally:
            os.unlink(path)

    def test_password_not_saved_to_file(self, monkeypatch):
        import FlowScroll.core.config as config_module
        from FlowScroll.ui.preset_manager import PresetManager

        path = self._make_temp_config({"presets": {}, "last_used": "长文档/表格"})

        try:
            monkeypatch.setattr(config_module, "CONFIG_FILE", path)
            pm = PresetManager()
            pm.load_from_file()
            pm.save_preset("LeakTest")

            with open(path, "r", encoding="utf-8") as f:
                saved = json.load(f)

            for name, data in saved.get("presets", {}).items():
                assert "webdav_password" not in data, f"预设 '{name}' 包含 webdav_password"
                assert "webdav_url" not in data
                assert "webdav_username" not in data
        finally:
            os.unlink(path)

    def test_loading_preset_does_not_override_webdav_settings(self, monkeypatch):
        import FlowScroll.core.config as config_module
        from FlowScroll.ui.preset_manager import PresetManager

        path = self._make_temp_config(
            {
                "presets": {
                    "MyPreset": {
                        "sensitivity": 3.0,
                        "webdav_url": "https://legacy.example.com/dav/",
                        "webdav_username": "legacy-user",
                    }
                },
                "last_used": "MyPreset",
                "current_config": {"sensitivity": 2.0},
                "webdav": {
                    "url": "https://dav.example.com/root/",
                    "username": "alice",
                },
            }
        )

        try:
            monkeypatch.setattr(config_module, "CONFIG_FILE", path)
            pm = PresetManager()
            pm.load_from_file()

            assert pm.load_preset("MyPreset") is True
            assert config_module.cfg.sensitivity == 3.0
            assert config_module.cfg.webdav_url == "https://dav.example.com/root/"
            assert config_module.cfg.webdav_username == "alice"
        finally:
            os.unlink(path)

    def test_load_migrates_legacy_home_config_to_new_default_path(self, monkeypatch, tmp_path):
        import FlowScroll.core.config as config_module
        from FlowScroll.ui.preset_manager import PresetManager

        legacy_path = tmp_path / ".FlowScroll_config.json"
        new_path = tmp_path / "AppData" / "Roaming" / "FlowScroll" / "FlowScroll_config.json"

        legacy_path.write_text(
            json.dumps(
                {
                    "presets": {},
                    "last_used": config_module.DEFAULT_PRESET_NAME,
                    "current_config": {
                        "sensitivity": 4.25,
                        "speed_factor": 1.5,
                    },
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        monkeypatch.setattr(config_module, "LEGACY_CONFIG_FILE", str(legacy_path))
        monkeypatch.setattr(config_module, "CONFIG_FILE", str(new_path))

        pm = PresetManager()
        pm.load_from_file()

        assert config_module.cfg.sensitivity == 4.25
        assert new_path.exists()
        saved = json.loads(new_path.read_text(encoding="utf-8"))
        assert saved["current_config"]["sensitivity"] == 4.25

    def test_load_does_not_rewrite_when_windows_paths_only_differ_in_case(self, monkeypatch, tmp_path):
        import builtins
        import FlowScroll.core.config as config_module
        from FlowScroll.ui.preset_manager import PresetManager

        config_path = tmp_path / "config.json"
        config_path.write_text(
            json.dumps(
                {
                    "presets": {},
                    "last_used": config_module.DEFAULT_PRESET_NAME,
                    "current_config": {"sensitivity": 3.5},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        monkeypatch.setattr(
            "FlowScroll.ui.preset_manager.get_config_load_candidates",
            lambda: [r"c:\portable\flowscroll\config.json"],
        )
        monkeypatch.setattr(
            "FlowScroll.ui.preset_manager.get_config_file",
            lambda: r"C:/Portable/FlowScroll/config.json",
        )
        monkeypatch.setattr(
            "FlowScroll.ui.preset_manager.os.path.exists",
            lambda path: str(path).lower() == r"c:\portable\flowscroll\config.json",
        )

        original_open = builtins.open

        def fake_open(path, mode="r", encoding=None):
            if "r" in mode and str(path).lower() == r"c:\portable\flowscroll\config.json":
                return original_open(config_path, mode, encoding=encoding)
            return original_open(path, mode, encoding=encoding)

        monkeypatch.setattr("builtins.open", fake_open)
        save_calls = []
        monkeypatch.setattr(
            PresetManager,
            "save_to_file",
            lambda self: save_calls.append("called"),
        )

        pm = PresetManager()
        pm.load_from_file()

        assert config_module.cfg.sensitivity == 3.5
        assert save_calls == []
