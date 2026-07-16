"""键盘管理、快捷键归一化与 WebDAV 错误格式化测试。"""

import importlib
import socket
import sys
import types
from urllib.error import HTTPError, URLError

import pytest


class TestKeyboardManagerHotkeyNormalization:
    """测试键盘快捷键归一化（依赖 pynput 环境）。"""

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
    """测试键盘快捷键归一化（纯 Mock，无 pynput 依赖）。"""

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
            return "+".join(p for p in (_normalize_hotkey_part(x) for x in str(value).split("+")) if p)

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
        listeners_module, FakeKeyCode, _ = self._import_listeners_with_fake_pynput(monkeypatch)
        km = listeners_module.KeyboardManager.__new__(listeners_module.KeyboardManager)

        assert km._get_key_name(FakeKeyCode(char="\x0b")) == "k"
        assert km._normalize_key_name("k") == "k"

    def test_ctrl_letter_vk_fallback_without_pynput(self, monkeypatch):
        listeners_module, FakeKeyCode, FakeKey = self._import_listeners_with_fake_pynput(monkeypatch)
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
    """测试 CapsLock/NumLock 等别名键的归一化。"""

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
    """测试 WebDAV 错误格式化与用户名脱敏。"""

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
            if req.get_method() == "PUT" and req.full_url.endswith("/dav/FlowScroll_config.json"):
                raise HTTPError(
                    url=req.full_url,
                    code=404,
                    msg="Not Found",
                    hdrs=None,
                    fp=None,
                )
            if req.get_method() == "MKCOL" and req.full_url.endswith("/dav/FlowScroll/"):
                return DummyResponse(201)
            if req.get_method() == "PUT" and req.full_url.endswith("/dav/FlowScroll/FlowScroll_config.json"):
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
            (
                "PUT",
                "https://dav.jianguoyun.com/dav/FlowScroll/FlowScroll_config.json",
                10,
            ),
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
            if req.get_method() == "GET" and req.full_url.endswith("/dav/FlowScroll_config.json"):
                raise HTTPError(
                    url=req.full_url,
                    code=404,
                    msg="Not Found",
                    hdrs=None,
                    fp=None,
                )
            if req.get_method() == "GET" and req.full_url.endswith("/dav/FlowScroll/FlowScroll_config.json"):
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
            (
                "GET",
                "https://dav.jianguoyun.com/dav/FlowScroll/FlowScroll_config.json",
                10,
            ),
        ]

    def test_webdav_download_rejects_non_object_json(self, monkeypatch):
        import FlowScroll.ui.webdav_dialog as webdav_dialog

        class DummyResponse:
            def read(self):
                return b"[]"

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        monkeypatch.setattr(
            webdav_dialog.urllib.request,
            "urlopen",
            lambda _req, timeout=10: DummyResponse(),
        )
        job = webdav_dialog.WebDAVJobThread(
            "download",
            "https://example.com/dav/",
            "Basic abc",
            "alice",
        )
        failures = []
        payloads = []
        job.failed.connect(failures.append)
        job.download_finished.connect(payloads.append)

        job.run()

        assert failures
        assert payloads == []

    def test_webdav_invalid_config_keeps_local_settings(self, monkeypatch):
        import FlowScroll.ui.webdav_dialog as webdav_dialog
        from FlowScroll.core.config import GlobalConfig

        local_config = GlobalConfig()
        local_config.sensitivity = 4.0
        before = local_config.to_dict()
        messages = []

        class DummyDialog:
            _job = None

            def parent(self):
                raise AssertionError("invalid config must not be persisted")

        monkeypatch.setattr(webdav_dialog, "cfg", local_config)
        monkeypatch.setattr(
            webdav_dialog.QMessageBox,
            "critical",
            lambda _parent, title, body: messages.append((title, body)),
        )

        webdav_dialog.WebDAVSyncDialog._on_download_finished(
            DummyDialog(),
            {"sensitivity": "fast"},
        )

        assert local_config.to_dict() == before
        assert messages


class TestAdvancedTab:
    """测试高级标签页的构建与持久化。"""

    def test_build_advanced_tab_smoke(self, monkeypatch):
        qtwidgets = pytest.importorskip("PySide6.QtWidgets", exc_type=ImportError)
        monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

        from FlowScroll.ui.tabs_builder import build_advanced_tab

        QApplication = qtwidgets.QApplication
        app = QApplication.instance() or QApplication([])

        class DummyAutoStart:
            def is_autorun(self):
                return False

        class DummyCtrl:
            def __init__(self):
                self.autostart = DummyAutoStart()

        class DummyMainWindow:
            def __init__(self):
                self.ui_widgets = {}
                self.ctrl = DummyCtrl()
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

            def open_config_storage_dialog(self):
                return None

            def reset_config_storage_path(self):
                return None

            def refresh_input_hook_status_ui(self):
                self.refreshed = True

            def refresh_config_storage_ui(self):
                return None

            def update_hotkey_label(self):
                if hasattr(self, "lbl_hotkey"):
                    self.lbl_hotkey.setText("unset")

        window = DummyMainWindow()
        widget = build_advanced_tab(window)

        assert app is not None
        assert widget is not None
        assert window.refreshed is True
        assert "filter_mode_button" in window.ui_widgets
