"""配置系统与凭据服务的基础 smoke test。

不依赖 GUI，可在 CI 中运行。
"""

import json
import os
import tempfile
import importlib
import sys
import types
import pytest


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
        assert c.activation_compat_mode is False
        assert c.activation_delay_ms == 0

    def test_to_dict_roundtrip(self):
        from FlowScroll.core.config import GlobalConfig

        c = GlobalConfig()
        c.sensitivity = 3.5
        c.speed_factor = 1.0
        c.reverse_y = True
        c.activation_compat_mode = True
        c.activation_delay_ms = 180

        d = c.to_dict()
        c2 = GlobalConfig()
        c2.from_dict(d)

        assert c2.sensitivity == 3.5
        assert c2.speed_factor == 1.0
        assert c2.reverse_y is True
        assert c2.activation_compat_mode is True
        assert c2.activation_delay_ms == 180

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
        cfg.filter_blacklist = ["potplayer", "vlc"]
        cfg.filter_whitelist = []
        runtime.current_window_name = "PotPlayer"
        runtime.is_fullscreen = False
        assert is_current_app_allowed() is False

        runtime.current_window_name = "Chrome"
        assert is_current_app_allowed() is True

    def test_whitelist_mode(self):
        from FlowScroll.core.config import cfg, runtime
        from FlowScroll.core.rules import is_current_app_allowed

        cfg.filter_mode = 2
        cfg.filter_blacklist = []
        cfg.filter_whitelist = ["chrome", "code"]
        runtime.is_fullscreen = False

        runtime.current_window_name = "Google Chrome"
        assert is_current_app_allowed() is True

        runtime.current_window_name = "PotPlayer"
        assert is_current_app_allowed() is False

    def test_legacy_filter_list_migration(self):
        from FlowScroll.core.config import GlobalConfig

        c = GlobalConfig()
        c.from_dict({"filter_mode": 1, "filter_list": ["potplayer"]})
        assert c.filter_blacklist == ["potplayer"]
        assert c.filter_whitelist == []

        c.from_dict({"filter_mode": 2, "filter_list": ["chrome"]})
        assert c.filter_blacklist == []
        assert c.filter_whitelist == ["chrome"]


class TestUpdateChecker:
    def test_newer_version_detection(self):
        from FlowScroll.services.update_checker import is_newer_version

        assert is_newer_version("1.4.1", "1.4.0") is True
        assert is_newer_version("v1.5.0", "1.4.9") is True
        assert is_newer_version("1.4.0", "1.4.0") is False
        assert is_newer_version("1.3.9", "1.4.0") is False
        assert is_newer_version("1.4.0-beta.1", "1.4.0") is False


# ---------------------------------------------------------------------------
# Constants 基础检查
# ---------------------------------------------------------------------------


class TestConstants:
    def test_config_version_is_int(self):
        from FlowScroll.constants import CONFIG_VERSION

        assert isinstance(CONFIG_VERSION, int)
        assert CONFIG_VERSION > 0


# ---------------------------------------------------------------------------
# KeyboardManager: Ctrl+字母 归一化
# ---------------------------------------------------------------------------


class TestKeyboardManagerHotkeyNormalization:
    def _patch_keyboard_types(self, monkeypatch, listeners_module):
        class DummyListener:
            def __init__(self, on_press=None, on_release=None):
                self.on_press = on_press
                self.on_release = on_release

            def start(self):
                return None

        class FakeKeyCode:
            def __init__(self, char=None, vk=None):
                self.char = char
                self.vk = vk

        class FakeKey:
            def __init__(self, name):
                self.name = name

        monkeypatch.setattr(listeners_module.keyboard, "Listener", DummyListener)
        monkeypatch.setattr(listeners_module.keyboard, "KeyCode", FakeKeyCode)
        monkeypatch.setattr(listeners_module.keyboard, "Key", FakeKey)
        return FakeKeyCode, FakeKey

    def test_ctrl_letter_control_char_normalized(self, monkeypatch):
        pytest.importorskip("pynput", exc_type=ImportError)
        from FlowScroll.input import listeners as listeners_module

        FakeKeyCode, _ = self._patch_keyboard_types(monkeypatch, listeners_module)
        km = listeners_module.KeyboardManager.__new__(listeners_module.KeyboardManager)

        # Ctrl+K 在某些平台会上报为 \x0b
        assert km._get_key_name(FakeKeyCode(char="\x0b")) == "k"
        assert km._normalize_key_name("k") == "k"

    def test_ctrl_letter_with_vk_fallback_is_matchable(self, monkeypatch):
        pytest.importorskip("pynput", exc_type=ImportError)
        from FlowScroll.input import listeners as listeners_module

        FakeKeyCode, FakeKey = self._patch_keyboard_types(monkeypatch, listeners_module)

        pressed_events = []
        km = listeners_module.KeyboardManager(
            lambda key, keys: pressed_events.append((key, set(keys))),
            lambda _key, _keys: None,
        )

        km.on_press(FakeKey("ctrl_l"))
        km.on_press(FakeKeyCode(vk=75))  # 'K'

        assert pressed_events[-1][0] == "k"
        assert {"ctrl", "k"}.issubset(pressed_events[-1][1])


class TestKeyboardManagerHotkeyNormalizationPureMock:
    def _import_listeners_with_fake_pynput(self, monkeypatch):
        fake_pynput = types.ModuleType("pynput")

        fake_keyboard = types.ModuleType("pynput.keyboard")

        class FakeListener:
            def __init__(self, on_press=None, on_release=None):
                self.on_press = on_press
                self.on_release = on_release

            def start(self):
                return None

        class FakeKeyCode:
            def __init__(self, char=None, vk=None):
                self.char = char
                self.vk = vk

        class FakeKey:
            def __init__(self, name):
                self.name = name

        fake_keyboard.Listener = FakeListener
        fake_keyboard.KeyCode = FakeKeyCode
        fake_keyboard.Key = FakeKey

        fake_mouse = types.ModuleType("pynput.mouse")

        class FakeButton:
            middle = object()
            x1 = object()
            x2 = object()

        class FakeController:
            position = (0, 0)

        class FakeMouseListener:
            def __init__(self, **_kwargs):
                pass

            def start(self):
                return None

        fake_mouse.Button = FakeButton
        fake_mouse.Controller = FakeController
        fake_mouse.Listener = FakeMouseListener

        fake_pynput.keyboard = fake_keyboard
        fake_pynput.mouse = fake_mouse

        fake_hotkeys = types.ModuleType("FlowScroll.core.hotkeys")

        def _normalize_hotkey_part(value):
            if not value:
                return ""
            return str(value).strip().lower()

        def _normalize_hotkey_string(value):
            if not value:
                return ""
            return "+".join(
                p for p in (_normalize_hotkey_part(x) for x in str(value).split("+")) if p
            )

        fake_hotkeys.normalize_hotkey_part = _normalize_hotkey_part
        fake_hotkeys.normalize_hotkey_string = _normalize_hotkey_string

        monkeypatch.setitem(sys.modules, "pynput", fake_pynput)
        monkeypatch.setitem(sys.modules, "pynput.keyboard", fake_keyboard)
        monkeypatch.setitem(sys.modules, "pynput.mouse", fake_mouse)
        monkeypatch.setitem(sys.modules, "FlowScroll.core.hotkeys", fake_hotkeys)
        monkeypatch.delitem(sys.modules, "FlowScroll.input.listeners", raising=False)

        module = importlib.import_module("FlowScroll.input.listeners")
        # Ensure this injected module does not leak into other tests.
        monkeypatch.setitem(sys.modules, "FlowScroll.input.listeners", module)
        return module, FakeKeyCode, FakeKey

    def test_ctrl_letter_control_char_normalized_without_pynput(self, monkeypatch):
        listeners_module, FakeKeyCode, _ = self._import_listeners_with_fake_pynput(
            monkeypatch
        )
        km = listeners_module.KeyboardManager.__new__(listeners_module.KeyboardManager)

        assert km._get_key_name(FakeKeyCode(char="\x0b")) == "k"
        assert km._normalize_key_name("k") == "k"

    def test_ctrl_letter_vk_fallback_without_pynput(self, monkeypatch):
        listeners_module, FakeKeyCode, FakeKey = (
            self._import_listeners_with_fake_pynput(monkeypatch)
        )
        pressed_events = []

        km = listeners_module.KeyboardManager(
            lambda key, keys: pressed_events.append((key, set(keys))),
            lambda _key, _keys: None,
        )

        km.on_press(FakeKey("ctrl_l"))
        km.on_press(FakeKeyCode(vk=75))

        assert pressed_events[-1][0] == "k"
        assert {"ctrl", "k"}.issubset(pressed_events[-1][1])


class TestLockKeyAliasNormalization:
    def test_capslock_alias_normalized(self):
        pytest.importorskip("PySide6", exc_type=ImportError)
        from FlowScroll.core.hotkeys import normalize_hotkey_string

        assert normalize_hotkey_string("CapsLock") == "caps_lock"
        assert normalize_hotkey_string("caps_lock") == "caps_lock"

    def test_capslock_alias_matches_listener_current_keys(self):
        pytest.importorskip("PySide6", exc_type=ImportError)
        pytest.importorskip("pynput", exc_type=ImportError)
        from FlowScroll.input.listeners import GlobalInputListener

        listener = GlobalInputListener.__new__(GlobalInputListener)
        assert listener._is_keyboard_hotkey_active("capslock", {"caps_lock"}) is True
