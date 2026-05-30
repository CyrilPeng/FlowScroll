import sys
import types
import importlib
from unittest.mock import MagicMock


def test_start_threads_returns_message_list_when_scroll_engine_fails(monkeypatch):
    fake_pynput = types.ModuleType("pynput")
    fake_mouse = types.ModuleType("pynput.mouse")

    class FakeController:
        pass

    fake_mouse.Controller = FakeController
    fake_pynput.mouse = fake_mouse

    monkeypatch.setitem(sys.modules, "pynput", fake_pynput)
    monkeypatch.setitem(sys.modules, "pynput.mouse", fake_mouse)

    fake_qtcore = types.ModuleType("PySide6.QtCore")

    class QObject:
        def __init__(self, *_args, **_kwargs):
            pass

    class Signal:
        def __init__(self, *_args, **_kwargs):
            self._callbacks = []

        def connect(self, callback):
            self._callbacks.append(callback)

        def emit(self, *args, **kwargs):
            for callback in list(self._callbacks):
                callback(*args, **kwargs)

    class QThread:
        def __init__(self, *_args, **_kwargs):
            pass

        def start(self):
            return None

    fake_qtcore.QObject = QObject
    fake_qtcore.Signal = Signal
    fake_qtcore.QThread = QThread

    fake_pyside6 = types.ModuleType("PySide6")
    fake_pyside6.QtCore = fake_qtcore

    monkeypatch.setitem(sys.modules, "PySide6", fake_pyside6)
    monkeypatch.setitem(sys.modules, "PySide6.QtCore", fake_qtcore)

    import FlowScroll.ui.app_controller as app_controller_module

    controller = app_controller_module.ApplicationController.__new__(
        app_controller_module.ApplicationController
    )
    controller.bridge = MagicMock()
    controller.mouse_controller = MagicMock()

    class DummyWindowMonitor:
        def start(self):
            return None

    class FailingScrollEngine:
        def __init__(self, *_args, **_kwargs):
            raise RuntimeError("boom")

    monkeypatch.setattr(app_controller_module, "WindowMonitor", DummyWindowMonitor)
    monkeypatch.setattr(app_controller_module, "ScrollEngine", FailingScrollEngine)

    messages = app_controller_module.ApplicationController.start_threads(
        controller, None
    )

    assert isinstance(messages, list)
    assert len(messages) == 1
    level, title, body = messages[0]
    assert level == "critical"
    assert title
    assert body


def test_hotkeys_module_imports_without_qt(monkeypatch):
    fake_qtcore = types.ModuleType("PySide6.QtCore")
    fake_pyside6 = types.ModuleType("PySide6")
    fake_pyside6.QtCore = fake_qtcore

    monkeypatch.setitem(sys.modules, "PySide6", fake_pyside6)
    monkeypatch.setitem(sys.modules, "PySide6.QtCore", fake_qtcore)
    monkeypatch.delitem(sys.modules, "FlowScroll.core.hotkeys", raising=False)

    hotkeys = importlib.import_module("FlowScroll.core.hotkeys")

    assert hotkeys.Qt is None
    assert hotkeys.MODIFIER_KEYS == set()
    assert hotkeys.normalize_hotkey_string("Ctrl+K") == "ctrl+k"


def test_delete_preset_uses_preset_manager_storage(monkeypatch):
    fake_pynput = types.ModuleType("pynput")
    fake_mouse = types.ModuleType("pynput.mouse")

    class FakeController:
        pass

    fake_mouse.Controller = FakeController
    fake_pynput.mouse = fake_mouse

    monkeypatch.setitem(sys.modules, "pynput", fake_pynput)
    monkeypatch.setitem(sys.modules, "pynput.mouse", fake_mouse)

    fake_qtcore = types.ModuleType("PySide6.QtCore")

    class QObject:
        def __init__(self, *_args, **_kwargs):
            pass

    class Signal:
        def __init__(self, *_args, **_kwargs):
            pass

    class QThread:
        pass

    fake_qtcore.QObject = QObject
    fake_qtcore.Signal = Signal
    fake_qtcore.QThread = QThread
    fake_pyside6 = types.ModuleType("PySide6")
    fake_pyside6.QtCore = fake_qtcore

    monkeypatch.setitem(sys.modules, "PySide6", fake_pyside6)
    monkeypatch.setitem(sys.modules, "PySide6.QtCore", fake_qtcore)

    import FlowScroll.ui.app_controller as app_controller_module

    controller = app_controller_module.ApplicationController.__new__(
        app_controller_module.ApplicationController
    )
    controller.preset_manager = MagicMock()
    controller.preset_manager.presets = {"custom": {}}
    controller.preset_manager.delete_preset.return_value = True
    controller.save_presets_to_file = MagicMock()

    assert app_controller_module.ApplicationController.delete_preset(
        controller, "custom"
    ) is True
    controller.preset_manager.delete_preset.assert_called_once_with("custom")
    controller.save_presets_to_file.assert_called_once_with()
