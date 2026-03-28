import time
from threading import Timer

from pynput import keyboard, mouse

from FlowScroll.core.config import cfg, runtime
from FlowScroll.core.hotkeys import normalize_hotkey_part, normalize_hotkey_string
from FlowScroll.services.logging_service import logger
from FlowScroll.constants import DOUBLE_CLICK_THRESHOLD


class KeyboardManager:
    def __init__(self, on_press_callback, on_release_callback):
        self.listener = keyboard.Listener(
            on_press=self.on_press, on_release=self.on_release
        )
        self.current_keys = set()
        self.on_press_callback = on_press_callback
        self.on_release_callback = on_release_callback

    def start(self):
        self.listener.start()

    def _get_key_name(self, key):
        if isinstance(key, keyboard.KeyCode):
            if key.char:
                # Ctrl+letter on some platforms can produce control chars
                # (e.g. Ctrl+K -> '\x0b'). Convert them back to letters.
                if len(key.char) == 1 and 1 <= ord(key.char) <= 26:
                    return chr(ord(key.char) + 96)
                return key.char.lower()
            vk = getattr(key, 'vk', None)
            if isinstance(vk, int):
                # A-Z
                if 65 <= vk <= 90:
                    return chr(vk + 32)
                # 0-9
                if 48 <= vk <= 57:
                    return chr(vk)
            return None
        if isinstance(key, keyboard.Key):
            return key.name
        return None

    def _normalize_key_name(self, key_name):
        if 'ctrl' in key_name:
            key_name = 'ctrl'
        elif 'alt' in key_name:
            key_name = 'alt'
        elif 'shift' in key_name:
            key_name = 'shift'
        elif 'cmd' in key_name:
            key_name = 'meta'
        return normalize_hotkey_part(key_name)

    def on_press(self, key):
        key_name = self._get_key_name(key)
        if not key_name:
            return

        normalized = self._normalize_key_name(key_name)
        self.current_keys.add(normalized)
        self.on_press_callback(normalized, set(self.current_keys))

    def on_release(self, key):
        key_name = self._get_key_name(key)
        if not key_name:
            return

        normalized = self._normalize_key_name(key_name)
        self.current_keys.discard(normalized)
        self.on_release_callback(normalized, set(self.current_keys))


class GlobalInputListener:
    """统一管理鼠标和键盘的输入拦截与分发。"""

    def __init__(self, bridge, is_app_allowed_callback, scroll_engine=None):
        self.bridge = bridge
        self.is_app_allowed_callback = is_app_allowed_callback
        self.scroll_engine = scroll_engine
        self.mouse_listener = None
        self.key_manager = None
        self.last_activation_press_time = 0.0
        self.mouse_hotkey_map = {
            'mouse_middle': mouse.Button.middle,
            'mouse_x1': mouse.Button.x1,
            'mouse_x2': mouse.Button.x2,
        }
        self.horizontal_hotkey_active = False
        self.activation_hotkey_active = False
        self.activation_input_source = None

        # Compatibility mode: delay activation until key/button is held long enough.
        self._pending_activation_timer = None
        self._pending_activation_source = None
        self._pressed_activation_sources = {'mouse': False, 'keyboard': False}

    def _get_keyboard_hotkey_parts(self, hotkey):
        hotkey = normalize_hotkey_string(hotkey)
        if not hotkey or hotkey.startswith('mouse_'):
            return set()
        return set(hotkey.split('+'))

    def _is_keyboard_hotkey_active(self, hotkey, current_keys):
        target_keys = self._get_keyboard_hotkey_parts(hotkey)
        return bool(target_keys) and target_keys.issubset(current_keys)

    def _get_horizontal_mouse_button(self):
        hotkey = normalize_hotkey_string(cfg.horizontal_hotkey)
        return self.mouse_hotkey_map.get(hotkey)

    def _get_activation_hotkey(self):
        if cfg.activation_mode == 1:
            return normalize_hotkey_string(cfg.activation_hotkey_hold)
        return normalize_hotkey_string(cfg.activation_hotkey_click)

    def _get_activation_mouse_button(self):
        hotkey = self._get_activation_hotkey()
        if not hotkey:
            return mouse.Button.middle
        return self.mouse_hotkey_map.get(hotkey)

    def _uses_default_middle_activation(self):
        return not self._get_activation_hotkey()

    def _set_active(self, active, x=None, y=None, source=None):
        if active:
            if x is not None and y is not None:
                runtime.origin_pos = (x, y)
            runtime.active = True
            self.activation_input_source = source
            self.bridge.show_overlay.emit()
            return

        if runtime.active:
            runtime.active = False
            self.activation_input_source = None
            self.bridge.hide_overlay.emit()

    def _toggle_active(self, x, y, source):
        if runtime.active:
            self._set_active(False)
        else:
            self._set_active(True, x, y, source)

    def _should_delay_activation(self):
        return bool(cfg.activation_compat_mode) and int(cfg.activation_delay_ms) > 0

    def _cancel_pending_activation(self, source=None):
        if source is not None and self._pending_activation_source != source:
            return
        if self._pending_activation_timer:
            self._pending_activation_timer.cancel()
            self._pending_activation_timer = None
            self._pending_activation_source = None

    def _activate_now(self, x, y, source):
        if not self.is_app_allowed_callback():
            return

        if cfg.activation_mode == 1:
            self._set_active(True, x, y, source)
            return

        current_time = time.time()
        if current_time - self.last_activation_press_time < DOUBLE_CLICK_THRESHOLD:
            return
        self.last_activation_press_time = current_time
        self._toggle_active(x, y, source)

    def _schedule_activation(self, x, y, source):
        self._cancel_pending_activation()
        self._pending_activation_source = source
        delay_s = max(0, int(cfg.activation_delay_ms)) / 1000.0

        def _fire():
            if self._pending_activation_source != source:
                return
            self._pending_activation_timer = None
            self._pending_activation_source = None
            if not self._pressed_activation_sources.get(source, False):
                return
            self._activate_now(x, y, source)

        self._pending_activation_timer = Timer(delay_s, _fire)
        self._pending_activation_timer.daemon = True
        self._pending_activation_timer.start()

    def _handle_activation_press(self, x, y, source):
        # Inertia running: only interrupt, do not activate.
        if self.scroll_engine and self.scroll_engine.inertia_active:
            self.scroll_engine.interrupt_inertia()
            return

        # Click mode: when already active, pressing the activation key/button
        # should close immediately even if compatibility delay is enabled.
        if cfg.activation_mode == 0 and runtime.active:
            self._cancel_pending_activation()
            self._set_active(False)
            return

        self._pressed_activation_sources[source] = True
        if self._should_delay_activation():
            self._schedule_activation(x, y, source)
            return

        self._activate_now(x, y, source)

    def _handle_activation_release(self, source):
        self._pressed_activation_sources[source] = False
        self._cancel_pending_activation(source)

        if cfg.activation_mode == 1 and self.activation_input_source == source:
            self._set_active(False)

    def _on_key_press(self, key_name, current_keys):
        # Inertia running: interrupt on non-modifier key press.
        if self.scroll_engine and self.scroll_engine.inertia_active:
            modifier_only = {'ctrl', 'alt', 'shift', 'meta'}
            if key_name not in modifier_only:
                self.scroll_engine.interrupt_inertia()

        if self._is_keyboard_hotkey_active(cfg.horizontal_hotkey, current_keys):
            if not self.horizontal_hotkey_active:
                self.horizontal_hotkey_active = True
                self.bridge.toggle_horizontal.emit()
        else:
            self.horizontal_hotkey_active = False

        activation_hotkey = self._get_activation_hotkey()
        if self._is_keyboard_hotkey_active(activation_hotkey, current_keys):
            if self.activation_hotkey_active:
                return
            self.activation_hotkey_active = True
            x, y = mouse.Controller().position
            self._handle_activation_press(x, y, 'keyboard')
        else:
            self._pressed_activation_sources['keyboard'] = False
            self._cancel_pending_activation('keyboard')
            self.activation_hotkey_active = False

    def _on_key_release(self, _key_name, current_keys):
        if not self._is_keyboard_hotkey_active(cfg.horizontal_hotkey, current_keys):
            self.horizontal_hotkey_active = False

        activation_hotkey = self._get_activation_hotkey()
        if not self._is_keyboard_hotkey_active(activation_hotkey, current_keys):
            self._pressed_activation_sources['keyboard'] = False
            if self.activation_hotkey_active:
                self._handle_activation_release('keyboard')
            self.activation_hotkey_active = False

    def start(self):
        try:
            self.key_manager = KeyboardManager(self._on_key_press, self._on_key_release)
            self.key_manager.start()
        except Exception as e:
            logger.error(f'键盘钩子失败: {e}')

        kwargs = {'on_click': self.on_click}
        import platform

        if platform.system() == 'Windows':
            kwargs['win32_event_filter'] = self.win32_event_filter

        self.mouse_listener = mouse.Listener(**kwargs)
        self.mouse_listener.start()

    def win32_event_filter(self, msg, _data):
        # WM_MBUTTONDOWN = 0x0207, WM_MBUTTONUP = 0x0208, WM_MBUTTONDBLCLK = 0x0209
        if msg in (0x0207, 0x0208, 0x0209):
            # Inertia running: middle button only interrupts inertia.
            if self.scroll_engine and self.scroll_engine.inertia_active:
                if msg == 0x0207:  # WM_MBUTTONDOWN
                    self.scroll_engine.interrupt_inertia()
                if self.mouse_listener and hasattr(self.mouse_listener, 'suppress_event'):
                    self.mouse_listener.suppress_event()
                return False

            if self.is_app_allowed_callback() and self._uses_default_middle_activation():
                x, y = mouse.Controller().position
                pressed = msg in (0x0207, 0x0209)
                self.on_click(x, y, mouse.Button.middle, pressed)

                if self.mouse_listener and hasattr(self.mouse_listener, 'suppress_event'):
                    self.mouse_listener.suppress_event()
                return False
        return True

    def on_click(self, x, y, button, pressed):
        # Inertia running: any mouse click interrupts inertia.
        if pressed and self.scroll_engine and self.scroll_engine.inertia_active:
            self.scroll_engine.interrupt_inertia()
            return

        if pressed and button == self._get_horizontal_mouse_button():
            self.bridge.toggle_horizontal.emit()
            return

        activation_button = self._get_activation_mouse_button()
        if activation_button and button == activation_button:
            if pressed:
                self._handle_activation_press(x, y, 'mouse')
            else:
                self._handle_activation_release('mouse')
            return
