import threading
from pynput import mouse, keyboard
from FlowScroll.core.config import cfg
from FlowScroll.services.logging_service import logger


class KeyboardManager:
    def __init__(self, bridge_callback):
        self.listener = keyboard.Listener(
            on_press=self.on_press, on_release=self.on_release
        )
        self.current_keys = set()
        self.bridge_callback = bridge_callback
        self.qt_to_pynput = {
            "pgup": "page_up",
            "pgdown": "page_down",
            "ins": "insert",
            "del": "delete",
            "esc": "esc",
            "return": "enter",
        }

    def start(self):
        self.listener.start()

    def _get_key_name(self, key):
        if isinstance(key, keyboard.KeyCode):
            return key.char.lower() if key.char else None
        elif isinstance(key, keyboard.Key):
            return key.name
        return None

    def on_press(self, key):
        key_name = self._get_key_name(key)
        if key_name:
            if "ctrl" in key_name:
                key_name = "ctrl"
            elif "alt" in key_name:
                key_name = "alt"
            elif "shift" in key_name:
                key_name = "shift"
            elif "cmd" in key_name:
                key_name = "meta"

            self.current_keys.add(key_name)
            self.check_hotkey()

    def on_release(self, key):
        key_name = self._get_key_name(key)
        if key_name:
            if "ctrl" in key_name:
                key_name = "ctrl"
            elif "alt" in key_name:
                key_name = "alt"
            elif "shift" in key_name:
                key_name = "shift"
            elif "cmd" in key_name:
                key_name = "meta"

            if key_name in self.current_keys:
                self.current_keys.remove(key_name)

    def check_hotkey(self):
        if not cfg.horizontal_hotkey:
            return

        qt_keys = cfg.horizontal_hotkey.lower().split("+")
        target_keys = set()
        for k in qt_keys:
            k = self.qt_to_pynput.get(k, k)
            target_keys.add(k)

        if self.current_keys == target_keys:
            self.bridge_callback()


class GlobalInputListener:
    """
    统筹管理鼠标和键盘的输入拦截与分发
    """

    def __init__(self, bridge, is_app_allowed_callback):
        self.bridge = bridge
        self.is_app_allowed_callback = is_app_allowed_callback
        self.mouse_listener = None
        self.key_manager = None

    def start(self):
        try:
            self.key_manager = KeyboardManager(
                lambda: self.bridge.toggle_horizontal.emit()
            )
            self.key_manager.start()
        except Exception as e:
            logger.error(f"键盘钩子失败: {e}")

        kwargs = {"on_click": self.on_click}
        import platform
        if platform.system() == "Windows":
            kwargs["win32_event_filter"] = self.win32_event_filter

        # [微软商店过审护盾：捕获无 runFullTrust 权限时的崩溃并抛出供上层处理]
        self.mouse_listener = mouse.Listener(**kwargs)
        self.mouse_listener.start()

    def win32_event_filter(self, msg, data):
        # WM_MBUTTONDOWN = 0x0207, WM_MBUTTONUP = 0x0208
        if msg in (0x0207, 0x0208):
            if self.is_app_allowed_callback():
                # OS 级拦截中键，防止浏览器等软件原生滚动 UI 弹出
                x, y = mouse.Controller().position
                pressed = (msg == 0x0207)
                self.on_click(x, y, mouse.Button.middle, pressed)
                return False
        return True

    def on_click(self, x, y, button, pressed):
        if button == mouse.Button.middle:
            if pressed:
                if not self.is_app_allowed_callback():
                    return
                cfg.active = not cfg.active
                if cfg.active:
                    cfg.origin_pos = (x, y)
                    self.bridge.show_overlay.emit()
                else:
                    self.bridge.hide_overlay.emit()
        elif pressed and (button == mouse.Button.left or button == mouse.Button.right):
            if cfg.active:
                cfg.active = False
                self.bridge.hide_overlay.emit()
