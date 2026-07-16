import importlib
import sys
import types


def _import_listeners_with_fake_pynput(monkeypatch):
    fake_pynput = types.ModuleType("pynput")

    fake_keyboard = types.ModuleType("pynput.keyboard")

    class FakeKeyboardListener:
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

    fake_keyboard.Listener = FakeKeyboardListener
    fake_keyboard.KeyCode = FakeKeyCode
    fake_keyboard.Key = FakeKey

    fake_mouse = types.ModuleType("pynput.mouse")

    class FakeButton:
        left = object()
        right = object()
        middle = object()
        x1 = object()
        x2 = object()

    class FakeController:
        position = (0, 0)

        def __init__(self):
            self.clicked = []

        def click(self, button):
            self.clicked.append(button)

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
    return module, FakeController


class _DummySignal:
    def __init__(self):
        self.count = 0

    def emit(self, *_args, **_kwargs):
        self.count += 1


class _DummyBridge:
    def __init__(self):
        self.show_overlay = _DummySignal()
        self.hide_overlay = _DummySignal()
        self.toggle_horizontal = _DummySignal()


class _SuppressingMouseListener:
    def __init__(self):
        self.suppressed = 0

    def suppress_event(self):
        self.suppressed += 1


def test_delayed_activation_uses_realtime_mouse_position(monkeypatch):
    listeners_module, FakeController = _import_listeners_with_fake_pynput(monkeypatch)
    from FlowScroll.core.config import STATE_LOCK, cfg, runtime

    class FakeTimer:
        last_instance = None

        def __init__(self, _delay, callback):
            self.callback = callback
            self.daemon = False
            self.started = False
            FakeTimer.last_instance = self

        def start(self):
            self.started = True

        def cancel(self):
            return None

    monkeypatch.setattr(listeners_module, "Timer", FakeTimer)

    with STATE_LOCK:
        cfg.activation_mode = 0
        cfg.activation_compat_mode = True
        cfg.activation_delay_ms = 120
        runtime.active = False
        runtime.origin_pos = (0, 0)

    listener = listeners_module.GlobalInputListener(_DummyBridge(), lambda: True, None)

    FakeController.position = (10, 20)
    listener._handle_activation_press(10, 20, "mouse")
    assert FakeTimer.last_instance is not None
    assert FakeTimer.last_instance.started is True

    # 在定时器触发前移动鼠标，起点应使用最新位置。
    FakeController.position = (200, 300)
    FakeTimer.last_instance.callback()

    with STATE_LOCK:
        assert runtime.active is True
        assert runtime.origin_pos == (200, 300)


def test_click_mode_debounce_uses_monotonic(monkeypatch):
    listeners_module, _ = _import_listeners_with_fake_pynput(monkeypatch)
    from FlowScroll.core.config import STATE_LOCK, cfg, runtime

    bridge = _DummyBridge()
    listener = listeners_module.GlobalInputListener(bridge, lambda: True, None)

    class _FakeTime:
        def __init__(self):
            self.values = [100.0, 100.05]

        def monotonic(self):
            return self.values.pop(0)

        def time(self):
            raise AssertionError("time.time should not be used for debounce")

    fake_time = _FakeTime()
    monkeypatch.setattr(listeners_module.time, "monotonic", fake_time.monotonic)
    monkeypatch.setattr(listeners_module.time, "time", fake_time.time)

    with STATE_LOCK:
        cfg.activation_mode = 0
        runtime.active = False
        runtime.origin_pos = (0, 0)

    listener._activate_now(1, 1, "mouse")
    with STATE_LOCK:
        assert runtime.active is True
        assert runtime.origin_pos == (1, 1)
    assert bridge.show_overlay.count == 1

    listener._activate_now(2, 2, "mouse")
    with STATE_LOCK:
        assert runtime.active is True
        assert runtime.origin_pos == (1, 1)
    assert bridge.show_overlay.count == 1


def test_delayed_activation_cancelled_before_timer_fire_does_not_activate(monkeypatch):
    listeners_module, FakeController = _import_listeners_with_fake_pynput(monkeypatch)
    from FlowScroll.core.config import STATE_LOCK, cfg, runtime

    class FakeTimer:
        last_instance = None

        def __init__(self, _delay, callback):
            self.callback = callback
            self.daemon = False
            self.started = False
            self.cancelled = False
            FakeTimer.last_instance = self

        def start(self):
            self.started = True

        def cancel(self):
            self.cancelled = True

    monkeypatch.setattr(listeners_module, "Timer", FakeTimer)

    with STATE_LOCK:
        cfg.activation_mode = 1
        cfg.activation_compat_mode = True
        cfg.activation_delay_ms = 120
        runtime.active = False
        runtime.origin_pos = (0, 0)

    bridge = _DummyBridge()
    listener = listeners_module.GlobalInputListener(bridge, lambda: True, None)

    FakeController.position = (10, 20)
    listener._handle_activation_press(10, 20, "mouse")
    listener._handle_activation_release("mouse")

    assert FakeTimer.last_instance is not None
    assert FakeTimer.last_instance.cancelled is True

    FakeController.position = (200, 300)
    FakeTimer.last_instance.callback()

    with STATE_LOCK:
        assert runtime.active is False
        assert runtime.origin_pos == (0, 0)
    assert bridge.show_overlay.count == 0


def test_left_or_right_click_cancels_active_scroll_without_suppressing(monkeypatch):
    listeners_module, _ = _import_listeners_with_fake_pynput(monkeypatch)
    from FlowScroll.core.config import STATE_LOCK, cfg, runtime

    bridge = _DummyBridge()
    listener = listeners_module.GlobalInputListener(bridge, lambda: True, None)

    with STATE_LOCK:
        cfg.activation_mode = 0
        runtime.active = True
        runtime.origin_pos = (100, 100)

    listener.on_click(120, 130, listeners_module.mouse.Button.left, True)

    with STATE_LOCK:
        assert runtime.active is False
    assert bridge.hide_overlay.count == 1

    with STATE_LOCK:
        runtime.active = True

    listener.on_click(120, 130, listeners_module.mouse.Button.right, True)

    with STATE_LOCK:
        assert runtime.active is False
    assert bridge.hide_overlay.count == 2


def test_win32_delayed_middle_short_click_is_suppressed_then_replayed(monkeypatch):
    listeners_module, _ = _import_listeners_with_fake_pynput(monkeypatch)
    from FlowScroll.core.config import STATE_LOCK, cfg, runtime

    class FakeTimer:
        def __init__(self, _delay, _callback):
            self.daemon = False

        def start(self):
            return None

        def cancel(self):
            return None

    monkeypatch.setattr(listeners_module, "Timer", FakeTimer)

    bridge = _DummyBridge()
    listener = listeners_module.GlobalInputListener(bridge, lambda: True, None)
    listener.mouse_listener = _SuppressingMouseListener()

    with STATE_LOCK:
        cfg.activation_mode = 0
        cfg.activation_compat_mode = True
        cfg.activation_delay_ms = 120
        cfg.activation_hotkey_click = ""
        runtime.active = False
        runtime.origin_pos = (0, 0)

    assert listener.win32_event_filter(0x0207, None) is None
    assert listener.win32_event_filter(0x0208, None) is None

    assert listener.mouse_listener.suppressed == 2
    assert listener._mouse_controller.clicked == [listeners_module.mouse.Button.middle]
    assert bridge.show_overlay.count == 0
    assert bridge.hide_overlay.count == 0
    with STATE_LOCK:
        assert runtime.active is False
        assert runtime.origin_pos == (0, 0)


def test_win32_delayed_middle_hold_does_not_replay_after_activation(monkeypatch):
    listeners_module, FakeController = _import_listeners_with_fake_pynput(monkeypatch)
    from FlowScroll.core.config import STATE_LOCK, cfg, runtime

    class FakeTimer:
        last_instance = None

        def __init__(self, _delay, callback):
            self.callback = callback
            self.daemon = False
            FakeTimer.last_instance = self

        def start(self):
            return None

        def cancel(self):
            return None

    monkeypatch.setattr(listeners_module, "Timer", FakeTimer)

    bridge = _DummyBridge()
    listener = listeners_module.GlobalInputListener(bridge, lambda: True, None)
    listener.mouse_listener = _SuppressingMouseListener()

    with STATE_LOCK:
        cfg.activation_mode = 0
        cfg.activation_compat_mode = True
        cfg.activation_delay_ms = 120
        cfg.activation_hotkey_click = ""
        runtime.active = False

    FakeController.position = (30, 40)
    assert listener.win32_event_filter(0x0207, None) is None
    FakeTimer.last_instance.callback()
    assert listener.win32_event_filter(0x0208, None) is None

    assert listener.mouse_listener.suppressed == 2
    assert listener._mouse_controller.clicked == []
    with STATE_LOCK:
        assert runtime.active is True
        assert runtime.origin_pos == (30, 40)


def test_win32_replayed_middle_callbacks_do_not_reactivate(monkeypatch):
    listeners_module, _ = _import_listeners_with_fake_pynput(monkeypatch)
    from FlowScroll.core.config import STATE_LOCK, cfg, runtime

    bridge = _DummyBridge()
    listener = listeners_module.GlobalInputListener(bridge, lambda: True, None)

    with STATE_LOCK:
        cfg.activation_mode = 0
        runtime.active = False

    with listener._activation_state_lock:
        listener._middle_replay_active = True
    assert listener.win32_event_filter(0x0207, None) is True
    with listener._activation_state_lock:
        listener._middle_replay_active = False

    listener.on_click(0, 0, listeners_module.mouse.Button.middle, True)

    with STATE_LOCK:
        assert runtime.active is False
    assert bridge.show_overlay.count == 0


def test_win32_active_delayed_middle_click_is_suppressed_to_close(monkeypatch):
    listeners_module, FakeController = _import_listeners_with_fake_pynput(monkeypatch)
    from FlowScroll.core.config import STATE_LOCK, cfg, runtime

    bridge = _DummyBridge()
    listener = listeners_module.GlobalInputListener(bridge, lambda: True, None)
    listener.mouse_listener = _SuppressingMouseListener()

    with STATE_LOCK:
        cfg.activation_mode = 0
        cfg.activation_compat_mode = True
        cfg.activation_delay_ms = 120
        cfg.activation_hotkey_click = ""
        runtime.active = True
        runtime.origin_pos = (10, 20)

    FakeController.position = (200, 300)

    assert listener.win32_event_filter(0x0207, None) is None

    assert listener.mouse_listener.suppressed == 1
    assert bridge.hide_overlay.count == 1
    with STATE_LOCK:
        assert runtime.active is False
