import time

from pynput import keyboard, mouse

from FlowScroll.core.config import cfg
from FlowScroll.core.hotkeys import normalize_hotkey_part, normalize_hotkey_string
from FlowScroll.services.logging_service import logger


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
            return key.char.lower() if key.char else None
        if isinstance(key, keyboard.Key):
            return key.name
        return None

    def _normalize_key_name(self, key_name):
        if "ctrl" in key_name:
            key_name = "ctrl"
        elif "alt" in key_name:
            key_name = "alt"
        elif "shift" in key_name:
            key_name = "shift"
        elif "cmd" in key_name:
            key_name = "meta"
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
    """统筹管理鼠标和键盘的输入拦截与分发。"""

    def __init__(self, bridge, is_app_allowed_callback):
        self.bridge = bridge
        self.is_app_allowed_callback = is_app_allowed_callback
        self.mouse_listener = None
        self.key_manager = None
        self.last_activation_press_time = 0.0
        self.mouse_hotkey_map = {
            "mouse_middle": mouse.Button.middle,
            "mouse_x1": mouse.Button.x1,
            "mouse_x2": mouse.Button.x2,
        }
        self.horizontal_hotkey_active = False
        self.activation_hotkey_active = False
        self.activation_input_source = None

    def _get_keyboard_hotkey_parts(self, hotkey):
        hotkey = normalize_hotkey_string(hotkey)
        if not hotkey or hotkey.startswith("mouse_"):
            return set()
        return set(hotkey.split("+"))

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
                cfg.origin_pos = (x, y)
            cfg.active = True
            self.activation_input_source = source
            self.bridge.show_overlay.emit()
            return

        if cfg.active:
            cfg.active = False
            self.activation_input_source = None
            self.bridge.hide_overlay.emit()

    def _toggle_active(self, x, y, source):
        if cfg.active:
            self._set_active(False)
        else:
            self._set_active(True, x, y, source)

    def _handle_activation_press(self, x, y, source):
        if not self.is_app_allowed_callback():
            return

        if cfg.activation_mode == 1:
            self._set_active(True, x, y, source)
            return

        current_time = time.time()
        if current_time - self.last_activation_press_time < 0.15:
            return
        self.last_activation_press_time = current_time
        self._toggle_active(x, y, source)

    def _handle_activation_release(self, source):
        if cfg.activation_mode == 1 and self.activation_input_source == source:
            self._set_active(False)

    def _on_key_press(self, _key_name, current_keys):
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
            self._handle_activation_press(x, y, "keyboard")
        else:
            self.activation_hotkey_active = False

    def _on_key_release(self, _key_name, current_keys):
        if not self._is_keyboard_hotkey_active(cfg.horizontal_hotkey, current_keys):
            self.horizontal_hotkey_active = False

        activation_hotkey = self._get_activation_hotkey()
        if not self._is_keyboard_hotkey_active(activation_hotkey, current_keys):
            if self.activation_hotkey_active:
                self._handle_activation_release("keyboard")
            self.activation_hotkey_active = False

    def start(self):
        try:
            self.key_manager = KeyboardManager(self._on_key_press, self._on_key_release)
            self.key_manager.start()
        except Exception as e:
            logger.error(f"键盘钩子失败: {e}")

        kwargs = {"on_click": self.on_click}
        import platform

        if platform.system() == "Windows":
            kwargs["win32_event_filter"] = self.win32_event_filter

        self.mouse_listener = mouse.Listener(**kwargs)
        self.mouse_listener.start()

    def win32_event_filter(self, msg, _data):
        # WM_MBUTTONDOWN = 0x0207, WM_MBUTTONUP = 0x0208, WM_MBUTTONDBLCLK = 0x0209
        if (
            msg in (0x0207, 0x0208, 0x0209)
            and self.is_app_allowed_callback()
            and self._uses_default_middle_activation()
        ):
            x, y = mouse.Controller().position
            pressed = msg in (0x0207, 0x0209)
            self.on_click(x, y, mouse.Button.middle, pressed)

            if self.mouse_listener and hasattr(self.mouse_listener, "suppress_event"):
                self.mouse_listener.suppress_event()
            return False
        return True

    def on_click(self, x, y, button, pressed):
        if pressed and button == self._get_horizontal_mouse_button():
            self.bridge.toggle_horizontal.emit()
            return

        activation_button = self._get_activation_mouse_button()
        if activation_button and button == activation_button:
            if pressed:
                self._handle_activation_press(x, y, "mouse")
            else:
                self._handle_activation_release("mouse")
            return
