"""配置系统与凭据服务的基础 smoke test。

不依赖 GUI，可在 CI 中运行。
"""

import json
import os
import tempfile


# ---------------------------------------------------------------------------
# GlobalConfig 持久化配置
# ---------------------------------------------------------------------------


class TestGlobalConfig:
    def test_default_values(self):
        from FlowScroll.core.config import GlobalConfig

        c = GlobalConfig()
        assert c.sensitivity == 2.0
        assert c.speed_factor == 2.0
        assert c.dead_zone == 20.0
        assert c.enable_horizontal is True
        assert c.enable_inertia is False
        assert c.activation_mode == 0

    def test_to_dict_roundtrip(self):
        from FlowScroll.core.config import GlobalConfig

        c = GlobalConfig()
        c.sensitivity = 3.5
        c.speed_factor = 1.0
        c.reverse_y = True

        d = c.to_dict()
        c2 = GlobalConfig()
        c2.from_dict(d)

        assert c2.sensitivity == 3.5
        assert c2.speed_factor == 1.0
        assert c2.reverse_y is True

    def test_to_dict_excludes_credentials(self):
        from FlowScroll.core.config import GlobalConfig

        c = GlobalConfig()
        c.webdav_url = "https://example.com/dav/"
        c.webdav_username = "user"

        d = c.to_dict()
        assert "webdav_password" not in d

    def test_from_dict_missing_keys_use_defaults(self):
        from FlowScroll.core.config import GlobalConfig

        c = GlobalConfig()
        c.from_dict({"sensitivity": 9.0})
        assert c.sensitivity == 9.0
        # 其他字段保持默认
        assert c.speed_factor == 2.0
        assert c.dead_zone == 20.0


# ---------------------------------------------------------------------------
# RuntimeState 运行时状态
# ---------------------------------------------------------------------------


class TestRuntimeState:
    def test_defaults(self):
        from FlowScroll.core.config import RuntimeState

        r = RuntimeState()
        assert r.active is False
        assert r.origin_pos == (0, 0)
        assert r.current_window_name == ""
        assert r.is_fullscreen is False

    def test_runtime_is_separate_from_config(self):
        from FlowScroll.core.config import GlobalConfig, RuntimeState

        c = GlobalConfig()
        r = RuntimeState()
        r.active = True
        r.current_window_name = "TestApp"

        # config 不受影响
        assert not hasattr(c, "active") or c.__dict__.get("active", None) is None


# ---------------------------------------------------------------------------
# BUILTIN_PRESETS
# ---------------------------------------------------------------------------


class TestBuiltinPresets:
    def test_all_presets_have_required_keys(self):
        from FlowScroll.core.config import BUILTIN_PRESETS

        required = {"sensitivity", "speed_factor", "dead_zone", "overlay_size"}
        for name, preset in BUILTIN_PRESETS.items():
            assert required.issubset(preset.keys()), (
                f"预设 '{name}' 缺少字段: {required - preset.keys()}"
            )

    def test_default_preset_exists(self):
        from FlowScroll.core.config import BUILTIN_PRESETS, DEFAULT_PRESET_NAME

        assert DEFAULT_PRESET_NAME in BUILTIN_PRESETS


# ---------------------------------------------------------------------------
# PresetManager 文件加载/保存
# ---------------------------------------------------------------------------


class TestPresetManager:
    def _make_temp_config(self, data):
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return path

    def test_load_and_save_roundtrip(self, monkeypatch):
        import FlowScroll.core.config as config_module
        import FlowScroll.ui.preset_manager as pm_module
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
            monkeypatch.setattr(pm_module, "CONFIG_FILE", path)
            pm = PresetManager()
            pm.load_from_file()
            assert pm.current_preset_name == "MyPreset"
            assert "MyPreset" in pm.presets
        finally:
            os.unlink(path)

    def test_password_not_saved_to_file(self, monkeypatch):
        import FlowScroll.core.config as config_module
        import FlowScroll.ui.preset_manager as pm_module
        from FlowScroll.ui.preset_manager import PresetManager

        path = self._make_temp_config({"presets": {}, "last_used": "长文档/表格"})

        try:
            monkeypatch.setattr(config_module, "CONFIG_FILE", path)
            monkeypatch.setattr(pm_module, "CONFIG_FILE", path)
            pm = PresetManager()
            pm.load_from_file()
            pm.save_preset("LeakTest")

            with open(path, "r", encoding="utf-8") as f:
                saved = json.load(f)

            for name, data in saved.get("presets", {}).items():
                assert "webdav_password" not in data, (
                    f"预设 '{name}' 包含 webdav_password"
                )
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# CredentialService (不依赖系统 keyring 的场景)
# ---------------------------------------------------------------------------


class TestCredentialService:
    def test_memory_fallback(self):
        from FlowScroll.services.credential_service import CredentialService

        cs = CredentialService()
        # 不论 keyring 是否可用，内存 fallback 都应能工作
        cs.save_password("test123")
        assert cs.load_password() == "test123"

        cs.delete_password()
        assert cs.load_password() == ""

    def test_empty_password(self):
        from FlowScroll.services.credential_service import CredentialService

        cs = CredentialService()
        cs.save_password("")
        assert cs.load_password() == ""


# ---------------------------------------------------------------------------
# Rules 非 GUI 逻辑
# ---------------------------------------------------------------------------


class TestRules:
    def test_global_mode_allows_everything(self):
        from FlowScroll.core.config import cfg, runtime
        from FlowScroll.core.rules import is_current_app_allowed

        cfg.filter_mode = 0
        cfg.disable_fullscreen = False
        runtime.is_fullscreen = False
        assert is_current_app_allowed() is True

    def test_fullscreen_blocked(self):
        from FlowScroll.core.config import cfg, runtime
        from FlowScroll.core.rules import is_current_app_allowed

        cfg.disable_fullscreen = True
        runtime.is_fullscreen = True
        assert is_current_app_allowed() is False

    def test_blacklist_mode(self):
        from FlowScroll.core.config import cfg, runtime
        from FlowScroll.core.rules import is_current_app_allowed

        cfg.filter_mode = 1
        cfg.filter_list = ["potplayer", "vlc"]
        runtime.current_window_name = "PotPlayer"
        runtime.is_fullscreen = False
        assert is_current_app_allowed() is False

        runtime.current_window_name = "Chrome"
        assert is_current_app_allowed() is True


# ---------------------------------------------------------------------------
# Constants 基础检查
# ---------------------------------------------------------------------------


class TestConstants:
    def test_config_version_is_int(self):
        from FlowScroll.constants import CONFIG_VERSION

        assert isinstance(CONFIG_VERSION, int)
        assert CONFIG_VERSION > 0
