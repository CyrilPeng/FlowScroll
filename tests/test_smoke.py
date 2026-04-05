"""配置系统与凭据服务的基础 smoke test。"""

import importlib
import json
import os
import socket
import shutil
import sys
import tempfile
import types
from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest


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


class TestRuntimeState:
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


class TestPresetManager:
    def _make_temp_config(self, data):
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
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

    def test_load_failure_clears_stale_presets(self, monkeypatch):
        import FlowScroll.core.config as config_module
        import FlowScroll.ui.preset_manager as pm_module
        from FlowScroll.ui.preset_manager import PresetManager

        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        with open(path, "w", encoding="utf-8") as f:
            f.write("{ invalid json")

        try:
            monkeypatch.setattr(config_module, "CONFIG_FILE", path)
            monkeypatch.setattr(pm_module, "CONFIG_FILE", path)
            pm = PresetManager()
            pm.presets = {"StalePreset": {"sensitivity": 3.0}}
            pm.current_preset_name = "StalePreset"

            pm.load_from_file()

            assert pm.presets == {}
            assert pm.current_preset_name == config_module.DEFAULT_PRESET_NAME
        finally:
            os.unlink(path)

    def test_save_includes_current_config(self, monkeypatch):
        import FlowScroll.core.config as config_module
        import FlowScroll.ui.preset_manager as pm_module
        from FlowScroll.core.config import cfg
        from FlowScroll.ui.preset_manager import PresetManager

        path = self._make_temp_config({"presets": {}, "last_used": config_module.DEFAULT_PRESET_NAME})

        try:
            monkeypatch.setattr(config_module, "CONFIG_FILE", path)
            monkeypatch.setattr(pm_module, "CONFIG_FILE", path)
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
        import FlowScroll.ui.preset_manager as pm_module
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
            monkeypatch.setattr(pm_module, "CONFIG_FILE", path)
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
        import FlowScroll.ui.preset_manager as pm_module
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
            monkeypatch.setattr(pm_module, "CONFIG_FILE", path)
            pm = PresetManager()

            pm.load_from_file()

            assert config_module.cfg.sensitivity == 4.5
            assert config_module.cfg.webdav_url == "https://dav.example.com/root/"
            assert config_module.cfg.webdav_username == "alice"
        finally:
            os.unlink(path)

    def test_load_migrates_legacy_webdav_settings(self, monkeypatch):
        import FlowScroll.core.config as config_module
        import FlowScroll.ui.preset_manager as pm_module
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
            monkeypatch.setattr(pm_module, "CONFIG_FILE", path)
            pm = PresetManager()

            pm.load_from_file()

            assert config_module.cfg.sensitivity == 4.5
            assert config_module.cfg.webdav_url == "https://legacy.example.com/dav/"
            assert config_module.cfg.webdav_username == "bob"
        finally:
            os.unlink(path)

    def test_invalid_preset_structure_falls_back_to_defaults(self, monkeypatch):
        import FlowScroll.core.config as config_module
        import FlowScroll.ui.preset_manager as pm_module
        from FlowScroll.ui.preset_manager import PresetManager

        path = self._make_temp_config({"presets": [], "last_used": []})

        try:
            monkeypatch.setattr(config_module, "CONFIG_FILE", path)
            monkeypatch.setattr(pm_module, "CONFIG_FILE", path)
            pm = PresetManager()

            pm.load_from_file()

            assert pm.presets == {}
            assert pm.current_preset_name == config_module.DEFAULT_PRESET_NAME
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
                assert "webdav_url" not in data
                assert "webdav_username" not in data
        finally:
            os.unlink(path)

    def test_loading_preset_does_not_override_webdav_settings(self, monkeypatch):
        import FlowScroll.core.config as config_module
        import FlowScroll.ui.preset_manager as pm_module
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
            monkeypatch.setattr(pm_module, "CONFIG_FILE", path)
            pm = PresetManager()
            pm.load_from_file()

            assert pm.load_preset("MyPreset") is True
            assert config_module.cfg.sensitivity == 3.0
            assert config_module.cfg.webdav_url == "https://dav.example.com/root/"
            assert config_module.cfg.webdav_username == "alice"
        finally:
            os.unlink(path)


class TestCredentialService:
    def test_memory_fallback(self):
        from FlowScroll.services.credential_service import CredentialService

        cs = CredentialService()
        cs.save_password("test123")
        assert cs.load_password() == "test123"

        cs.delete_password()
        assert cs.load_password() == ""

    def test_empty_password(self):
        from FlowScroll.services.credential_service import CredentialService

        cs = CredentialService()
        cs.save_password("")
        assert cs.load_password() == ""


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
        runtime.current_process_name = "potplayer"
        runtime.process_name_status = "available"
        runtime.is_fullscreen = False
        assert is_current_app_allowed() is False

        runtime.current_process_name = "chrome"
        assert is_current_app_allowed() is True

    def test_whitelist_mode(self):
        from FlowScroll.core.config import cfg, runtime
        from FlowScroll.core.rules import is_current_app_allowed

        cfg.filter_mode = 2
        cfg.filter_blacklist = []
        cfg.filter_whitelist = ["chrome", "code"]
        runtime.is_fullscreen = False

        runtime.current_process_name = "chrome"
        runtime.process_name_status = "available"
        assert is_current_app_allowed() is True

        runtime.current_process_name = "potplayer"
        runtime.process_name_status = "available"
        assert is_current_app_allowed() is False

    def test_filter_falls_back_to_window_name_when_process_name_missing(self):
        from FlowScroll.core.config import cfg, runtime
        from FlowScroll.core.rules import is_current_app_allowed

        cfg.filter_mode = 1
        cfg.filter_blacklist = ["chrome"]
        cfg.filter_whitelist = []
        runtime.current_process_name = ""
        runtime.process_name_status = "unavailable"
        runtime.current_window_name = "Google Chrome"
        runtime.is_fullscreen = False

        assert is_current_app_allowed() is False

    def test_filter_prefers_process_name_over_window_name(self):
        from FlowScroll.core.config import cfg, runtime
        from FlowScroll.core.rules import is_current_app_allowed

        cfg.filter_mode = 1
        cfg.filter_blacklist = ["code"]
        cfg.filter_whitelist = []
        runtime.current_process_name = "code"
        runtime.process_name_status = "available"
        runtime.current_window_name = "Unrelated Window Title"
        runtime.is_fullscreen = False

        assert is_current_app_allowed() is False

    def test_filter_unknown_status_does_not_block_before_first_snapshot(self):
        from FlowScroll.core.config import cfg, runtime
        from FlowScroll.core.rules import is_current_app_allowed

        cfg.filter_mode = 2
        cfg.filter_blacklist = []
        cfg.filter_whitelist = ["chrome"]
        runtime.current_process_name = ""
        runtime.current_window_name = ""
        runtime.process_name_status = "unknown"
        runtime.last_match_target = "chrome"
        runtime.is_fullscreen = False

        assert is_current_app_allowed() is True

    def test_filter_stale_status_does_not_reuse_old_target(self):
        from FlowScroll.core.config import cfg, runtime
        from FlowScroll.core.rules import is_current_app_allowed

        cfg.filter_mode = 2
        cfg.filter_blacklist = []
        cfg.filter_whitelist = ["chrome"]
        runtime.current_process_name = ""
        runtime.current_window_name = ""
        runtime.process_name_status = "stale"
        runtime.last_match_target = ""
        runtime.is_fullscreen = False

        assert is_current_app_allowed() is True

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

    def test_prerelease_version_detection(self):
        from FlowScroll.services.update_checker import is_prerelease_version

        assert is_prerelease_version("1.6.3.dev0") is True
        assert is_prerelease_version("1.6.3") is False

    def test_stable_release_is_not_newer_than_dev_build(self):
        from FlowScroll.services.update_checker import is_newer_version

        assert is_newer_version("1.6.2", "1.6.3.dev0") is False

    def test_stable_release_is_newer_than_same_dev_line(self):
        from FlowScroll.services.update_checker import is_newer_version

        assert is_newer_version("1.6.3", "1.6.3.dev0") is True

    def test_stable_release_is_newer_than_release_candidate(self):
        from FlowScroll.services.update_checker import is_newer_version

        assert is_newer_version("1.6.3", "1.6.3rc1") is True


class TestConstants:
    def test_config_version_is_int(self):
        from FlowScroll.constants import CONFIG_VERSION

        assert isinstance(CONFIG_VERSION, int)
        assert CONFIG_VERSION > 0


class TestSingleInstanceManager:
    def test_server_name_is_stable_for_same_app_id(self):
        from FlowScroll.services.single_instance import SingleInstanceManager

        left = SingleInstanceManager._build_server_name("cyrilpeng.FlowScroll")
        right = SingleInstanceManager._build_server_name("cyrilpeng.FlowScroll")

        assert left == right
        assert left.startswith("FlowScroll.")

    def test_server_name_changes_with_app_id(self):
        from FlowScroll.services.single_instance import SingleInstanceManager

        left = SingleInstanceManager._build_server_name("FlowScroll.A")
        right = SingleInstanceManager._build_server_name("FlowScroll.B")

        assert left != right

    def test_module_imports_without_pyside6(self, monkeypatch):
        monkeypatch.delitem(sys.modules, "FlowScroll.services.single_instance", raising=False)
        monkeypatch.setitem(sys.modules, "PySide6", None)
        monkeypatch.setitem(sys.modules, "PySide6.QtCore", None)
        monkeypatch.setitem(sys.modules, "PySide6.QtNetwork", None)

        module = importlib.import_module("FlowScroll.services.single_instance")

        assert module.QT_IPC_AVAILABLE is False
        manager = module.SingleInstanceManager("cyrilpeng.FlowScroll")
        assert manager.acquire() is True


class TestResourcePath:
    def test_resource_path_does_not_depend_on_cwd(self, monkeypatch):
        from FlowScroll.ui.utils import resource_path

        project_root = Path(__file__).resolve().parents[1]
        monkeypatch.chdir(project_root / "tests")

        resolved = Path(resource_path("FlowScroll/resources/FlowScroll.svg")).resolve()
        assert resolved == (project_root / "FlowScroll" / "resources" / "FlowScroll.svg").resolve()


class TestLinuxPlatform:
    def test_frontmost_window_info_parsing(self, monkeypatch):
        from FlowScroll.platform.linux import LinuxPlatform

        platform = LinuxPlatform()

        responses = {
            ("xprop", "-root", "_NET_ACTIVE_WINDOW"): "_NET_ACTIVE_WINDOW(WINDOW): window id # 0x3a00007",
            ("xprop", "-id", "0x3a00007", "_NET_WM_NAME", "WM_NAME"): '_NET_WM_NAME(UTF8_STRING) = "Terminal"',
            ("xprop", "-id", "0x3a00007", "WM_CLASS"): 'WM_CLASS(STRING) = "gnome-terminal-server", "Gnome-terminal"',
            ("xprop", "-id", "0x3a00007", "_NET_WM_PID"): "_NET_WM_PID(CARDINAL) = 4321",
            ("xprop", "-id", "0x3a00007", "_NET_WM_STATE"): "_NET_WM_STATE(ATOM) = _NET_WM_STATE_FULLSCREEN",
        }

        monkeypatch.setattr(platform, "_run_command", lambda command: responses.get(tuple(command), ""))
        monkeypatch.setattr(platform, "_read_process_name", lambda pid: "gnome-terminal-server" if pid == "4321" else "")

        info = platform.get_frontmost_window_info()

        assert info == ("Terminal", "gnome-terminal-server", "Gnome-terminal", True)

    def test_autostart_roundtrip(self):
        from FlowScroll.platform.linux import LinuxPlatform

        temp_dir = Path(__file__).resolve().parent / ".tmp_linux_platform"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir()
        platform = LinuxPlatform()
        platform.autostart_dir = temp_dir
        platform.desktop_file = temp_dir / "FlowScroll.desktop"

        assert platform.set_autostart("FlowScroll", "/opt/flowscroll/FlowScroll.AppImage", True) is True
        assert platform.desktop_file.exists()
        assert platform.is_autostart_enabled("FlowScroll", "/opt/flowscroll/FlowScroll.AppImage") is True
        assert platform.set_autostart("FlowScroll", "/opt/flowscroll/FlowScroll.AppImage", False) is True
        assert platform.desktop_file.exists() is False
        shutil.rmtree(temp_dir)


class TestWindowsPlatform:
    def test_is_autostart_enabled_missing_value_is_silent(self, monkeypatch):
        fake_winreg = types.SimpleNamespace(
            HKEY_CURRENT_USER=object(),
            KEY_READ=0,
            KEY_ALL_ACCESS=0,
            OpenKey=None,
            QueryValueEx=None,
        )
        monkeypatch.setitem(sys.modules, "winreg", fake_winreg)
        monkeypatch.delitem(sys.modules, "FlowScroll.platform.windows", raising=False)

        windows_module = importlib.import_module("FlowScroll.platform.windows")

        logged = []

        class DummyLogger:
            def warning(self, message, *args):
                logged.append(message % args if args else message)

            def debug(self, message, *args):
                logged.append(message % args if args else message)

        class DummyKey:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        monkeypatch.setattr(windows_module, "logger", DummyLogger())
        monkeypatch.setattr(
            windows_module.winreg, "OpenKey", lambda *_args, **_kwargs: DummyKey()
        )
        monkeypatch.setattr(
            windows_module.winreg,
            "QueryValueEx",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(FileNotFoundError(2, "not found")),
        )

        platform = windows_module.WindowsPlatform.__new__(windows_module.WindowsPlatform)

        assert platform.is_autostart_enabled("FlowScroll", "C:\\FlowScroll.exe") is False
        assert logged == []


class TestAutoStartManager:
    @pytest.mark.parametrize("os_name", ["Linux", "Darwin"])
    def test_source_run_uses_python_interpreter_on_posix(self, monkeypatch, os_name):
        import FlowScroll.services.autostart as autostart_module

        monkeypatch.setattr(autostart_module, "OS_NAME", os_name)
        monkeypatch.setattr(autostart_module.os.path, "abspath", lambda value: value)
        monkeypatch.setattr(sys, "executable", "/usr/bin/python3")
        monkeypatch.setattr(sys, "argv", ["/tmp/Flow Scroll/main.py"])
        monkeypatch.setattr(sys, "frozen", False, raising=False)

        manager = autostart_module.AutoStartManager()

        assert manager.app_path == "/usr/bin/python3 '/tmp/Flow Scroll/main.py'"

    def test_windows_source_run_uses_python_for_script(self, monkeypatch):
        import FlowScroll.services.autostart as autostart_module

        monkeypatch.setattr(autostart_module, "OS_NAME", "Windows")
        monkeypatch.setattr(autostart_module.os.path, "abspath", lambda value: value)
        monkeypatch.setattr(sys, "executable", "C:\\Python312\\python.exe")
        monkeypatch.setattr(sys, "argv", ["D:\\FlowScroll\\main.py"])
        monkeypatch.setattr(sys, "frozen", False, raising=False)

        manager = autostart_module.AutoStartManager()

        assert manager.app_path == '"C:\\Python312\\python.exe" "D:\\FlowScroll\\main.py"'

    def test_windows_non_frozen_exe_uses_executable_directly(self, monkeypatch):
        import FlowScroll.services.autostart as autostart_module

        monkeypatch.setattr(autostart_module, "OS_NAME", "Windows")
        monkeypatch.setattr(autostart_module.os.path, "abspath", lambda value: value)
        monkeypatch.setattr(
            sys, "executable", "C:\\Temp\\onefile-runtime\\python.exe"
        )
        monkeypatch.setattr(
            sys, "argv", ["C:\\Program Files\\FlowScroll\\FlowScroll.exe"]
        )
        monkeypatch.setattr(sys, "frozen", False, raising=False)

        manager = autostart_module.AutoStartManager()

        assert manager.app_path == '"C:\\Program Files\\FlowScroll\\FlowScroll.exe"'

    def test_windows_frozen_exe_path_with_spaces_is_quoted(self, monkeypatch):
        import FlowScroll.services.autostart as autostart_module

        monkeypatch.setattr(autostart_module, "OS_NAME", "Windows")
        monkeypatch.setattr(autostart_module.os.path, "abspath", lambda value: value)
        monkeypatch.setattr(
            sys, "executable", "C:\\Program Files\\FlowScroll\\FlowScroll.exe"
        )
        monkeypatch.setattr(sys, "argv", ["C:\\Program Files\\FlowScroll\\FlowScroll.exe"])
        monkeypatch.setattr(sys, "frozen", True, raising=False)

        manager = autostart_module.AutoStartManager()

        assert manager.app_path == '"C:\\Program Files\\FlowScroll\\FlowScroll.exe"'


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
        km.on_press(FakeKeyCode(vk=75))

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


class TestWebDAVErrorFormatting:
    def test_mask_webdav_username(self):
        from FlowScroll.ui.webdav_dialog import mask_webdav_username

        assert mask_webdav_username("") == "<empty>"
        assert mask_webdav_username("a") == "a*"
        assert mask_webdav_username("bob") == "b*b"
        assert mask_webdav_username("alice") == "al**e"

    def test_validate_webdav_url_requires_http_scheme(self):
        from FlowScroll.ui.webdav_dialog import validate_webdav_url

        assert validate_webdav_url("dav.jianguoyun.com/dav/") is not None
        assert validate_webdav_url("https://dav.jianguoyun.com/dav/") is None

    def test_build_webdav_urls_normalize_root_directory(self):
        from FlowScroll.ui.webdav_dialog import (
            build_legacy_webdav_file_url,
            build_preferred_webdav_file_url,
        )

        assert (
            build_legacy_webdav_file_url("https://dav.jianguoyun.com/dav")
            == "https://dav.jianguoyun.com/dav/FlowScroll_config.json"
        )
        assert (
            build_preferred_webdav_file_url("https://dav.jianguoyun.com/dav/")
            == "https://dav.jianguoyun.com/dav/FlowScroll/FlowScroll_config.json"
        )

    def test_format_connection_refused_error(self):
        from FlowScroll.ui.webdav_dialog import format_webdav_error

        err = URLError(ConnectionRefusedError(10061, "actively refused"))
        message = format_webdav_error(err)
        assert "refused" in message.lower() or "拒绝" in message

    def test_format_timeout_error(self):
        from FlowScroll.ui.webdav_dialog import format_webdav_error

        message = format_webdav_error(URLError(socket.timeout("timed out")))
        lowered = message.lower()
        assert "timeout" in lowered or "timed out" in lowered or "超时" in message

    def test_format_http_error(self):
        from FlowScroll.ui.webdav_dialog import format_webdav_error

        err = HTTPError(
            url="https://example.com/dav/FlowScroll_config.json",
            code=401,
            msg="Unauthorized",
            hdrs=None,
            fp=None,
        )
        message = format_webdav_error(err)
        assert "401" in message

    def test_webdav_job_logs_http_error(self, monkeypatch):
        import FlowScroll.ui.webdav_dialog as webdav_dialog

        logged = []

        class DummyLogger:
            def info(self, message, *args):
                logged.append(message % args if args else message)

            def warning(self, message, *args):
                logged.append(message % args if args else message)

            def error(self, message, *args):
                logged.append(message % args if args else message)

        def fake_urlopen(_req, timeout=10):
            raise HTTPError(
                url="https://example.com/dav/FlowScroll_config.json",
                code=401,
                msg="Unauthorized",
                hdrs=None,
                fp=None,
            )

        monkeypatch.setattr(webdav_dialog, "logger", DummyLogger())
        monkeypatch.setattr(webdav_dialog.urllib.request, "urlopen", fake_urlopen)

        job = webdav_dialog.WebDAVJobThread(
            "upload",
            "https://example.com/dav/FlowScroll_config.json",
            "Basic abc",
            "alice",
            {"ok": True},
        )
        failures = []
        job.failed.connect(failures.append)

        job.run()

        assert failures
        assert any("event=failed" in entry for entry in logged)
        assert any("mode=upload" in entry for entry in logged)
        assert any("username=al**e" in entry for entry in logged)
        assert any("status=401" in entry for entry in logged)
        assert any(
            "event=failed mode=upload url=https://example.com/dav/FlowScroll_config.json username=al**e status=401"
            in entry
            for entry in logged
        )

    def test_webdav_job_logs_non_http_error(self, monkeypatch):
        import FlowScroll.ui.webdav_dialog as webdav_dialog

        logged = []

        class DummyLogger:
            def info(self, message, *args):
                logged.append(message % args if args else message)

            def warning(self, message, *args):
                logged.append(message % args if args else message)

            def error(self, message, *args):
                logged.append(message % args if args else message)

        def fake_urlopen(_req, timeout=10):
            raise URLError(ConnectionRefusedError(10061, "actively refused"))

        monkeypatch.setattr(webdav_dialog, "logger", DummyLogger())
        monkeypatch.setattr(webdav_dialog.urllib.request, "urlopen", fake_urlopen)

        job = webdav_dialog.WebDAVJobThread(
            "download",
            "https://example.com/dav/FlowScroll_config.json",
            "Basic abc",
            "bob",
        )
        failures = []
        job.failed.connect(failures.append)

        job.run()

        assert failures
        assert any("event=failed" in entry for entry in logged)
        assert any("mode=download" in entry for entry in logged)
        assert any("username=b*b" in entry for entry in logged)
        assert any("url=https://example.com/dav/FlowScroll_config.json" in entry for entry in logged)

    def test_webdav_job_logs_start_finish_and_duration(self, monkeypatch):
        import FlowScroll.ui.webdav_dialog as webdav_dialog

        logged = []

        class DummyLogger:
            def info(self, message, *args):
                logged.append(message % args if args else message)

            def warning(self, message, *args):
                logged.append(message % args if args else message)

            def error(self, message, *args):
                logged.append(message % args if args else message)

        class DummyResponse:
            status = 204

            def read(self):
                return b"{}"

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        times = iter([100.0, 100.25])

        monkeypatch.setattr(webdav_dialog, "logger", DummyLogger())
        monkeypatch.setattr(webdav_dialog.time, "monotonic", lambda: next(times))
        monkeypatch.setattr(
            webdav_dialog.urllib.request,
            "urlopen",
            lambda _req, timeout=10: DummyResponse(),
        )

        job = webdav_dialog.WebDAVJobThread(
            "upload",
            "https://example.com/dav/FlowScroll_config.json",
            "Basic abc",
            "alice",
            {"ok": True},
        )
        statuses = []
        job.upload_finished.connect(statuses.append)

        job.run()

        assert statuses == [204]
        assert logged == []

    def test_webdav_upload_falls_back_to_app_subdir_after_root_404(self, monkeypatch):
        import FlowScroll.ui.webdav_dialog as webdav_dialog

        requests = []

        class DummyResponse:
            def __init__(self, status):
                self.status = status

            def read(self):
                return b"{}"

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        def fake_urlopen(req, timeout=10):
            requests.append((req.get_method(), req.full_url, timeout))
            if req.get_method() == "PUT" and req.full_url.endswith(
                "/dav/FlowScroll_config.json"
            ):
                raise HTTPError(
                    url=req.full_url,
                    code=404,
                    msg="Not Found",
                    hdrs=None,
                    fp=None,
                )
            if req.get_method() == "MKCOL" and req.full_url.endswith("/dav/FlowScroll/"):
                return DummyResponse(201)
            if req.get_method() == "PUT" and req.full_url.endswith(
                "/dav/FlowScroll/FlowScroll_config.json"
            ):
                return DummyResponse(201)
            raise AssertionError(f"unexpected request: {req.get_method()} {req.full_url}")

        monkeypatch.setattr(webdav_dialog.urllib.request, "urlopen", fake_urlopen)

        job = webdav_dialog.WebDAVJobThread(
            "upload",
            "https://dav.jianguoyun.com/dav/",
            "Basic abc",
            "alice",
            {"ok": True},
        )
        statuses = []
        job.upload_finished.connect(statuses.append)

        job.run()

        assert statuses == [201]
        assert requests == [
            ("PUT", "https://dav.jianguoyun.com/dav/FlowScroll_config.json", 10),
            ("MKCOL", "https://dav.jianguoyun.com/dav/FlowScroll/", 10),
            ("PUT", "https://dav.jianguoyun.com/dav/FlowScroll/FlowScroll_config.json", 10),
        ]

    def test_webdav_download_falls_back_to_app_subdir_after_legacy_404(self, monkeypatch):
        import FlowScroll.ui.webdav_dialog as webdav_dialog

        requests = []

        class DummyResponse:
            status = 200

            def read(self):
                return b'{"sensitivity": 2.5}'

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        def fake_urlopen(req, timeout=10):
            requests.append((req.get_method(), req.full_url, timeout))
            if req.get_method() == "GET" and req.full_url.endswith(
                "/dav/FlowScroll_config.json"
            ):
                raise HTTPError(
                    url=req.full_url,
                    code=404,
                    msg="Not Found",
                    hdrs=None,
                    fp=None,
                )
            if req.get_method() == "GET" and req.full_url.endswith(
                "/dav/FlowScroll/FlowScroll_config.json"
            ):
                return DummyResponse()
            raise AssertionError(f"unexpected request: {req.get_method()} {req.full_url}")

        monkeypatch.setattr(webdav_dialog.urllib.request, "urlopen", fake_urlopen)

        job = webdav_dialog.WebDAVJobThread(
            "download",
            "https://dav.jianguoyun.com/dav/",
            "Basic abc",
            "alice",
        )
        payloads = []
        job.download_finished.connect(payloads.append)

        job.run()

        assert payloads == [{"sensitivity": 2.5}]
        assert requests == [
            ("GET", "https://dav.jianguoyun.com/dav/FlowScroll_config.json", 10),
            ("GET", "https://dav.jianguoyun.com/dav/FlowScroll/FlowScroll_config.json", 10),
        ]


class TestMainTabPersistence:
    def test_persist_config_change_updates_cfg_and_saves(self):
        from FlowScroll.core.config import cfg
        from FlowScroll.ui.tabs_builder import _persist_config_change

        class DummyWindow:
            def __init__(self):
                self.saved = 0

            def save_presets_to_file(self):
                self.saved += 1

        window = DummyWindow()
        original_overlay_size = cfg.overlay_size

        try:
            _persist_config_change(window, "overlay_size", 88)

            assert cfg.overlay_size == 88
            assert window.saved == 1
        finally:
            cfg.overlay_size = original_overlay_size


class TestLoggingService:
    def test_source_run_uses_debug_console_logging(self, monkeypatch):
        import FlowScroll.services.logging_service as logging_service

        monkeypatch.setattr(sys, "frozen", False, raising=False)

        assert logging_service.is_frozen_binary() is False
        assert logging_service.get_logger_level() == logging_service.logging.DEBUG
        assert logging_service.get_console_log_level() == logging_service.logging.DEBUG

    def test_binary_run_keeps_error_only_logging(self, monkeypatch):
        import FlowScroll.services.logging_service as logging_service

        monkeypatch.setattr(sys, "frozen", True, raising=False)

        assert logging_service.is_frozen_binary() is True
        assert logging_service.get_logger_level() == logging_service.logging.ERROR
        assert logging_service.get_console_log_level() == logging_service.logging.ERROR


class TestAdvancedTab:
    def test_build_advanced_tab_smoke(self, monkeypatch):
        qtwidgets = pytest.importorskip("PySide6.QtWidgets", exc_type=ImportError)
        monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

        from FlowScroll.ui.tabs_builder import build_advanced_tab

        QApplication = qtwidgets.QApplication
        app = QApplication.instance() or QApplication([])

        class DummyAutoStart:
            def is_autorun(self):
                return False

        class DummyMainWindow:
            def __init__(self):
                self.ui_widgets = {}
                self.autostart = DummyAutoStart()
                self.refreshed = False

            def toggle_autorun(self, *_args):
                return None

            def open_hotkey_dialog(self):
                return None

            def open_inertia_settings_dialog(self):
                return None

            def open_reverse_mode_dialog(self):
                return None

            def open_work_mode_dialog(self):
                return None

            def open_filter_mode_dialog(self):
                return None

            def open_webdav_settings(self):
                return None

            def refresh_input_hook_status_ui(self):
                self.refreshed = True

            def update_hotkey_label(self):
                if hasattr(self, "lbl_hotkey"):
                    self.lbl_hotkey.setText("unset")

        window = DummyMainWindow()
        widget = build_advanced_tab(window)

        assert app is not None
        assert widget is not None
        assert window.refreshed is True
        assert "filter_mode_button" in window.ui_widgets
