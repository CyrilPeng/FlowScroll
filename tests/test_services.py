"""凭据服务、规则、更新检测、常量、单实例、资源路径、平台与自启动测试。"""

import importlib
import shutil
import sys
import types
from pathlib import Path

import pytest


class TestCredentialService:
    """测试凭据服务的内存回退机制。"""

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
    """测试应用过滤规则：全局模式、黑名单、白名单与全屏检测。"""

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
    """测试版本比较逻辑。"""

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
    """测试常量定义的完整性。"""

    def test_config_version_is_int(self):
        from FlowScroll.constants import CONFIG_VERSION

        assert isinstance(CONFIG_VERSION, int)
        assert CONFIG_VERSION > 0


class TestSingleInstanceManager:
    """测试单实例管理器的服务名生成与 IPC 逻辑。"""

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
    """测试资源路径解析。"""

    def test_resource_path_does_not_depend_on_cwd(self, monkeypatch):
        from FlowScroll.ui.utils import resource_path

        project_root = Path(__file__).resolve().parents[1]
        monkeypatch.chdir(project_root / "tests")

        resolved = Path(resource_path("FlowScroll/resources/FlowScroll.svg")).resolve()
        assert resolved == (project_root / "FlowScroll" / "resources" / "FlowScroll.svg").resolve()


class TestLinuxPlatform:
    """测试 Linux 平台的窗口信息解析。"""

    def test_frontmost_window_info_parsing(self, monkeypatch):
        from FlowScroll.platform.linux import LinuxPlatform

        platform = LinuxPlatform()

        responses = {
            (
                "xprop",
                "-root",
                "_NET_ACTIVE_WINDOW",
            ): "_NET_ACTIVE_WINDOW(WINDOW): window id # 0x3a00007",
            (
                "xprop",
                "-id",
                "0x3a00007",
                "_NET_WM_NAME",
                "WM_NAME",
                "WM_CLASS",
                "_NET_WM_PID",
                "_NET_WM_STATE",
            ): '_NET_WM_NAME(UTF8_STRING) = "Terminal"\n'
            'WM_CLASS(STRING) = "gnome-terminal-server", "Gnome-terminal"\n'
            "_NET_WM_PID(CARDINAL) = 4321\n"
            "_NET_WM_STATE(ATOM) = _NET_WM_STATE_FULLSCREEN",
        }

        monkeypatch.setattr(platform, "_run_command", lambda command: responses.get(tuple(command), ""))
        monkeypatch.setattr(
            platform,
            "_read_process_name",
            lambda pid: "gnome-terminal-server" if pid == "4321" else "",
        )

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


class TestMacOSPlatform:
    """测试 macOS launchd 自启动参数。"""

    def test_autostart_writes_split_program_arguments(self, tmp_path):
        import plistlib

        from FlowScroll.platform.macos import MacOSPlatform

        platform = MacOSPlatform()
        platform.plist_path = str(tmp_path / "com.cyrilpeng.flowscroll.plist")
        command = "'/Applications/Flow Scroll.app/Contents/MacOS/FlowScroll' --silent"

        assert platform.set_autostart("FlowScroll", command, True) is True

        with open(platform.plist_path, "rb") as f:
            data = plistlib.load(f)
        assert data["ProgramArguments"] == [
            "/Applications/Flow Scroll.app/Contents/MacOS/FlowScroll",
            "--silent",
        ]
        assert platform.is_autostart_enabled("FlowScroll", command) is True

    def test_autostart_detects_stale_program_arguments(self, tmp_path):
        from FlowScroll.platform.macos import MacOSPlatform

        platform = MacOSPlatform()
        platform.plist_path = str(tmp_path / "com.cyrilpeng.flowscroll.plist")
        old_command = "'/Applications/Flow Scroll.app/Contents/MacOS/FlowScroll' --silent"
        new_command = "'/Applications/FlowScroll.app/Contents/MacOS/FlowScroll' --silent"

        assert platform.set_autostart("FlowScroll", old_command, True) is True
        assert platform.is_autostart_enabled("FlowScroll", new_command) is False


class TestWindowsPlatform:
    """测试 Windows 平台的自启动与窗口检测。"""

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
        monkeypatch.setattr(windows_module.winreg, "OpenKey", lambda *_args, **_kwargs: DummyKey())
        monkeypatch.setattr(
            windows_module.winreg,
            "QueryValueEx",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(FileNotFoundError(2, "not found")),
        )

        platform = windows_module.WindowsPlatform.__new__(windows_module.WindowsPlatform)

        assert platform.is_autostart_enabled("FlowScroll", "C:\\FlowScroll.exe") is False
        assert logged == []


class TestAutoStartManager:
    """测试自启动管理器。"""

    @pytest.mark.parametrize("os_name", ["Linux", "Darwin"])
    def test_source_run_uses_python_interpreter_on_posix(self, monkeypatch, os_name):
        import FlowScroll.services.autostart as autostart_module

        monkeypatch.setattr(autostart_module, "OS_NAME", os_name)
        monkeypatch.setattr(autostart_module.os.path, "abspath", lambda value: value)
        monkeypatch.setattr(sys, "executable", "/usr/bin/python3")
        monkeypatch.setattr(sys, "argv", ["/tmp/Flow Scroll/main.py"])
        monkeypatch.setattr(sys, "frozen", False, raising=False)

        manager = autostart_module.AutoStartManager()

        assert manager.app_path == "/usr/bin/python3 '/tmp/Flow Scroll/main.py' --silent"

    def test_windows_source_run_uses_python_for_script(self, monkeypatch):
        import FlowScroll.services.autostart as autostart_module

        monkeypatch.setattr(autostart_module, "OS_NAME", "Windows")
        monkeypatch.setattr(autostart_module.os.path, "abspath", lambda value: value)
        monkeypatch.setattr(sys, "executable", "C:\\Python312\\python.exe")
        monkeypatch.setattr(sys, "argv", ["D:\\FlowScroll\\main.py"])
        monkeypatch.setattr(sys, "frozen", False, raising=False)

        manager = autostart_module.AutoStartManager()

        assert manager.app_path == '"C:\\Python312\\python.exe" "D:\\FlowScroll\\main.py" --silent'

    def test_windows_non_frozen_exe_uses_executable_directly(self, monkeypatch):
        import FlowScroll.services.autostart as autostart_module

        monkeypatch.setattr(autostart_module, "OS_NAME", "Windows")
        monkeypatch.setattr(autostart_module.os.path, "abspath", lambda value: value)
        monkeypatch.setattr(sys, "executable", "C:\\Temp\\onefile-runtime\\python.exe")
        monkeypatch.setattr(sys, "argv", ["C:\\Program Files\\FlowScroll\\FlowScroll.exe"])
        monkeypatch.setattr(sys, "frozen", False, raising=False)

        manager = autostart_module.AutoStartManager()

        assert manager.app_path == '"C:\\Program Files\\FlowScroll\\FlowScroll.exe" --silent'

    def test_windows_frozen_exe_path_with_spaces_is_quoted(self, monkeypatch):
        import FlowScroll.services.autostart as autostart_module

        monkeypatch.setattr(autostart_module, "OS_NAME", "Windows")
        monkeypatch.setattr(autostart_module.os.path, "abspath", lambda value: value)
        monkeypatch.setattr(sys, "executable", "C:\\Program Files\\FlowScroll\\FlowScroll.exe")
        monkeypatch.setattr(sys, "argv", ["C:\\Program Files\\FlowScroll\\FlowScroll.exe"])
        monkeypatch.setattr(sys, "frozen", True, raising=False)

        manager = autostart_module.AutoStartManager()

        assert manager.app_path == '"C:\\Program Files\\FlowScroll\\FlowScroll.exe" --silent'

    def test_macos_frozen_executable_path_with_spaces_is_shell_quoted(self, monkeypatch):
        import FlowScroll.services.autostart as autostart_module

        monkeypatch.setattr(autostart_module, "OS_NAME", "Darwin")
        monkeypatch.setattr(autostart_module.os.path, "abspath", lambda value: value)
        monkeypatch.setattr(
            sys,
            "executable",
            "/Applications/Flow Scroll.app/Contents/MacOS/FlowScroll",
        )
        monkeypatch.setattr(sys, "argv", ["/Applications/Flow Scroll.app"])
        monkeypatch.setattr(sys, "frozen", True, raising=False)

        manager = autostart_module.AutoStartManager()

        assert manager.app_path == "'/Applications/Flow Scroll.app/Contents/MacOS/FlowScroll' --silent"


class TestMainTabPersistence:
    """测试配置持久化与 UI 同步。"""

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
    """测试日志服务。"""

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
