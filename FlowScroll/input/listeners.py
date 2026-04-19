import platform
import threading
import time
from importlib import import_module
from threading import Timer

try:
    keyboard = import_module("pynput.keyboard")
except ImportError:
    keyboard = None

try:
    mouse = import_module("pynput.mouse")
except ImportError:
    mouse = None

from FlowScroll.core.config import STATE_LOCK, cfg, runtime
from FlowScroll.core.hotkeys import normalize_hotkey_part, normalize_hotkey_string
from FlowScroll.services.logging_service import logger
from FlowScroll.constants import DOUBLE_CLICK_THRESHOLD


class KeyboardManager:
    """键盘监听管理器：捕获按键按下/释放事件并分发回调。"""

    def __init__(self, on_press_callback, on_release_callback):
        """初始化键盘管理器，绑定按下和释放回调。"""
        if keyboard is None:
            raise ImportError("pynput.keyboard is unavailable")
        self.listener = keyboard.Listener(
            on_press=self.on_press, on_release=self.on_release
        )
        self.current_keys = set()
        self.on_press_callback = on_press_callback
        self.on_release_callback = on_release_callback

    def start(self):
        """启动键盘监听线程。"""
        self.listener.start()

    def _get_key_name(self, key):
        """将 pynput 的 KeyCode / Key 转换为标准化的键名字符串。"""
        if isinstance(key, keyboard.KeyCode):
            if key.char:
                # 某些平台上，Ctrl+字母可能会产生控制字符，
                # 例如 Ctrl+K -> '\x0b'，这里将其还原为字母。
                if len(key.char) == 1 and 1 <= ord(key.char) <= 26:
                    return chr(ord(key.char) + 96)
                return key.char.lower()
            vk = getattr(key, "vk", None)
            if isinstance(vk, int):
                # 大写字母 A-Z。
                if 65 <= vk <= 90:
                    return chr(vk + 32)
                # 数字 0-9。
                if 48 <= vk <= 57:
                    return chr(vk)
            return None
        if isinstance(key, keyboard.Key):
            return key.name
        return None

    def _normalize_key_name(self, key_name):
        """将修饰键别名统一为 ctrl/alt/shift/meta，再通过 hotkey 模块归一化。"""
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
        """按键按下回调：归一化键名后添加到当前按键集合并分发。"""
        key_name = self._get_key_name(key)
        if not key_name:
            return

        normalized = self._normalize_key_name(key_name)
        self.current_keys.add(normalized)
        self.on_press_callback(normalized, set(self.current_keys))

    def on_release(self, key):
        """按键释放回调：归一化键名后从当前按键集合移除并分发。"""
        key_name = self._get_key_name(key)
        if not key_name:
            return

        normalized = self._normalize_key_name(key_name)
        self.current_keys.discard(normalized)
        self.on_release_callback(normalized, set(self.current_keys))


class GlobalInputListener:
    """统一管理鼠标和键盘的输入拦截与分发。"""

    def __init__(self, bridge, is_app_allowed_callback, scroll_engine=None):
        """初始化全局输入监听器，配置热键映射和延迟启动参数。"""
        if mouse is None:
            raise ImportError("pynput.mouse is unavailable")
        self.bridge = bridge
        self.is_app_allowed_callback = is_app_allowed_callback
        self.scroll_engine = scroll_engine
        self.mouse_listener = None
        self.key_manager = None
        self.keyboard_hook_available = True
        self.mouse_hook_available = True
        self.last_activation_press_time = 0.0
        self.mouse_hotkey_map = {
            "mouse_middle": mouse.Button.middle,
            "mouse_x1": mouse.Button.x1,
            "mouse_x2": mouse.Button.x2,
        }
        self.horizontal_hotkey_active = False
        self.activation_hotkey_active = False
        self.activation_input_source = None

        # 延迟启动模式：按键或鼠标按住达到阈值后才真正启用。
        self._pending_activation_timer = None
        self._pending_activation_source = None
        self._pressed_activation_sources = {"mouse": False, "keyboard": False}
        # 复用单个鼠标控制器实例，避免每次读取位置时重新创建。
        self._activation_state_lock = threading.Lock()
        self._mouse_controller = mouse.Controller()

    def _get_keyboard_hotkey_parts(self, hotkey):
        """解析键盘快捷键字符串为标准化按键集合，鼠标热键返回空集。"""
        hotkey = normalize_hotkey_string(hotkey)
        if not hotkey or hotkey.startswith("mouse_"):
            return set()
        alias_fallback = {
            "capslock": "caps_lock",
            "numlock": "num_lock",
            "scrolllock": "scroll_lock",
        }
        normalized_parts = []
        for raw_part in hotkey.split("+"):
            part = normalize_hotkey_part(raw_part)
            part = alias_fallback.get(part, part)
            if part:
                normalized_parts.append(part)
        return set(normalized_parts)

    def _is_keyboard_hotkey_active(self, hotkey, current_keys):
        """判断指定键盘快捷键组合是否全部处于按下状态。"""
        target_keys = self._get_keyboard_hotkey_parts(hotkey)
        return bool(target_keys) and target_keys.issubset(current_keys)

    def _get_horizontal_mouse_button(self):
        """获取横向滚动热键对应的鼠标按钮，非鼠标热键时返回 None。"""
        with STATE_LOCK:
            hotkey = normalize_hotkey_string(cfg.horizontal_hotkey)
        return self.mouse_hotkey_map.get(hotkey)

    def _get_activation_hotkey(self):
        """根据激活模式（点击/长按）返回当前启用的快捷键字符串。"""
        with STATE_LOCK:
            if cfg.activation_mode == 1:
                return normalize_hotkey_string(cfg.activation_hotkey_hold)
            return normalize_hotkey_string(cfg.activation_hotkey_click)

    def _get_activation_mouse_button(self):
        """获取激活热键对应的鼠标按钮，默认为中键。"""
        hotkey = self._get_activation_hotkey()
        if not hotkey:
            return mouse.Button.middle
        return self.mouse_hotkey_map.get(hotkey)

    def _uses_default_middle_activation(self):
        """判断是否使用默认的中键激活（即未自定义激活快捷键）。"""
        return not self._get_activation_hotkey()

    def _set_active(self, active, x=None, y=None, source=None):
        """设置滚动激活/关闭状态，更新 origin_pos 并触发 overlay 显示/隐藏。"""
        if active:
            with STATE_LOCK:
                if x is not None and y is not None:
                    runtime.origin_pos = (x, y)
                runtime.active = True
            self.activation_input_source = source
            self.bridge.show_overlay.emit()
            return

        with STATE_LOCK:
            currently_active = runtime.active
            if currently_active:
                runtime.active = False
        if currently_active:
            self.activation_input_source = None
            self.bridge.hide_overlay.emit()

    def _toggle_active(self, x, y, source):
        """切换滚动激活状态：当前激活则关闭，否则激活。"""
        with STATE_LOCK:
            currently_active = runtime.active
        if currently_active:
            self._set_active(False)
        else:
            self._set_active(True, x, y, source)

    def _should_delay_activation(self):
        """判断是否应使用延迟启动模式（compat_mode 且 delay_ms > 0）。"""
        with STATE_LOCK:
            return bool(cfg.activation_compat_mode) and int(cfg.activation_delay_ms) > 0

    def _cancel_pending_activation(self, source=None):
        """取消待执行的延迟激活定时器，可限定仅取消特定来源。"""
        with self._activation_state_lock:
            if source is not None and self._pending_activation_source != source:
                return
            timer = self._pending_activation_timer
            self._pending_activation_timer = None
            self._pending_activation_source = None
        if timer:
            timer.cancel()

    def _activate_now(self, x, y, source):
        """立即执行激活逻辑：长按模式直接激活，点击模式还需防止双击误触。"""
        if not self.is_app_allowed_callback():
            return

        with STATE_LOCK:
            activation_mode = cfg.activation_mode

        if activation_mode == 1:
            self._set_active(True, x, y, source)
            return

        current_time = time.monotonic()
        if current_time - self.last_activation_press_time < DOUBLE_CLICK_THRESHOLD:
            return
        self.last_activation_press_time = current_time
        self._toggle_active(x, y, source)

    def _schedule_activation(self, x, y, source):
        """安排延迟激活：在指定延迟后检查按键仍按住才真正激活。"""
        self._cancel_pending_activation()
        with STATE_LOCK:
            delay_s = max(0, int(cfg.activation_delay_ms)) / 1000.0

        def _fire():
            with self._activation_state_lock:
                if self._pending_activation_source != source:
                    return
                self._pending_activation_timer = None
                self._pending_activation_source = None
                pressed = self._pressed_activation_sources.get(source, False)
            if not pressed:
                return
            current_x, current_y = self._mouse_controller.position
            self._activate_now(current_x, current_y, source)

        timer = Timer(delay_s, _fire)
        timer.daemon = True
        with self._activation_state_lock:
            self._pending_activation_source = source
            self._pending_activation_timer = timer
        timer.start()

    def _handle_activation_press(self, x, y, source):
        """处理激活键按下事件：惯性中只打断不激活；点击模式下再次按下则关闭；支持延迟启动。"""
        # 惯性运行中只负责打断，不应再次激活滚动。
        if self.scroll_engine and self.scroll_engine.inertia_active:
            self.scroll_engine.interrupt_inertia()
            return

        # 单击启用模式下，如果当前已经处于激活状态，
        # 再次按下触发键应立即关闭，不受延迟启动影响。
        with STATE_LOCK:
            click_mode_and_active = cfg.activation_mode == 0 and runtime.active
        if click_mode_and_active:
            self._cancel_pending_activation()
            self._set_active(False)
            return

        with self._activation_state_lock:
            self._pressed_activation_sources[source] = True
        if self._should_delay_activation():
            self._schedule_activation(x, y, source)
            return

        self._activate_now(x, y, source)

    def _handle_activation_release(self, source):
        """处理激活键释放事件：长按模式下松开即关闭滚动；取消待执行的延迟激活。"""
        with self._activation_state_lock:
            self._pressed_activation_sources[source] = False
        self._cancel_pending_activation(source)

        with STATE_LOCK:
            activation_mode = cfg.activation_mode
        if activation_mode == 1 and self.activation_input_source == source:
            self._set_active(False)

    def _on_key_press(self, key_name, current_keys):
        """键盘按下事件：检查横向热键和激活热键状态，打断惯性。"""
        # 惯性运行中，按下非修饰键时直接打断惯性。
        if self.scroll_engine and self.scroll_engine.inertia_active:
            modifier_only = {"ctrl", "alt", "shift", "meta"}
            if key_name not in modifier_only:
                self.scroll_engine.interrupt_inertia()

        with STATE_LOCK:
            horizontal_hotkey = cfg.horizontal_hotkey
        if self._is_keyboard_hotkey_active(horizontal_hotkey, current_keys):
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
            x, y = self._mouse_controller.position
            self._handle_activation_press(x, y, "keyboard")
        else:
            with self._activation_state_lock:
                self._pressed_activation_sources["keyboard"] = False
            self._cancel_pending_activation("keyboard")
            self.activation_hotkey_active = False

    def _on_key_release(self, _key_name, current_keys):
        """键盘释放事件：更新热键激活状态，处理激活键释放。"""
        with STATE_LOCK:
            horizontal_hotkey = cfg.horizontal_hotkey
        if not self._is_keyboard_hotkey_active(horizontal_hotkey, current_keys):
            self.horizontal_hotkey_active = False

        activation_hotkey = self._get_activation_hotkey()
        if not self._is_keyboard_hotkey_active(activation_hotkey, current_keys):
            with self._activation_state_lock:
                self._pressed_activation_sources["keyboard"] = False
            if self.activation_hotkey_active:
                self._handle_activation_release("keyboard")
            self.activation_hotkey_active = False

    def start(self):
        """启动键盘和鼠标监听器，Windows 下额外注册 win32 事件过滤器。"""
        try:
            self.key_manager = KeyboardManager(self._on_key_press, self._on_key_release)
            self.key_manager.start()
        except Exception as e:
            self.keyboard_hook_available = False
            logger.error(f"键盘钩子失败: {e}")

        kwargs = {"on_click": self.on_click}

        if platform.system() == "Windows":
            kwargs["win32_event_filter"] = self.win32_event_filter

        try:
            self.mouse_listener = mouse.Listener(**kwargs)
            self.mouse_listener.start()
        except Exception as e:
            self.mouse_hook_available = False
            logger.error(f"鼠标钩子失败: {e}")

    def win32_event_filter(self, msg, _data):
        """Windows 低级鼠标钩子过滤器：拦截中键事件以实现自定义激活行为。"""
        # WM_MBUTTONDOWN = 0x0207，WM_MBUTTONUP = 0x0208，WM_MBUTTONDBLCLK = 0x0209
        if msg in (0x0207, 0x0208, 0x0209):
            # 惯性运行中，中键只用于打断惯性。
            if self.scroll_engine and self.scroll_engine.inertia_active:
                if msg == 0x0207:  # 中键按下
                    self.scroll_engine.interrupt_inertia()
                if self.mouse_listener and hasattr(
                    self.mouse_listener, "suppress_event"
                ):
                    self.mouse_listener.suppress_event()
                return False

            if (
                self.is_app_allowed_callback()
                and self._uses_default_middle_activation()
            ):
                x, y = self._mouse_controller.position
                pressed = msg in (0x0207, 0x0209)
                self.on_click(x, y, mouse.Button.middle, pressed)

                if self.mouse_listener and hasattr(
                    self.mouse_listener, "suppress_event"
                ):
                    self.mouse_listener.suppress_event()
                return False
        return True

    def on_click(self, x, y, button, pressed):
        """鼠标点击回调：惯性中任意点击打断；检查横向按钮和激活按钮。"""
        # 惯性运行中，任意鼠标点击都会打断惯性。
        if pressed and self.scroll_engine and self.scroll_engine.inertia_active:
            self.scroll_engine.interrupt_inertia()
            return

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
