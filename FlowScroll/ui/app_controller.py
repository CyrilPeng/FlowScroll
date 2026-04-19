"""应用控制器：从 MainWindow 中抽离的业务逻辑，负责线程生命周期、配置持久化与状态协调。"""

import os

from pynput import mouse

from FlowScroll.core.config import (
    STATE_LOCK,
    cfg,
    runtime,
    BUILTIN_PRESETS,
    DEFAULT_PRESET_NAME,
    get_config_file,
    get_config_override_source,
    set_config_attr,
)
from FlowScroll.core.engine import ScrollEngine
from FlowScroll.core.rules import is_current_app_allowed
from FlowScroll.input.listeners import GlobalInputListener
from FlowScroll.services.autostart import AutoStartManager
from FlowScroll.services.logging_service import logger
from FlowScroll.services.window_monitor import WindowMonitor
from FlowScroll.services.update_checker import (
    UpdateCheckerThread,
    is_newer_version,
    is_prerelease_version,
)
from FlowScroll.ui.bridge import LogicBridge
from FlowScroll.ui.preset_manager import PresetManager
from FlowScroll.platform import OS_NAME, system_platform

mouse_controller = mouse.Controller()


class ApplicationController:
    """管理应用的业务逻辑：后台线程、预设、更新检测与配置持久化。"""

    def __init__(self):
        """初始化应用控制器，创建桥接器、自启动管理器、预设管理器等核心组件。"""
        self.bridge = LogicBridge()
        self.autostart = AutoStartManager()
        self.preset_manager = PresetManager()
        self.mouse_controller = mouse_controller

        # 后台线程引用。
        self.window_monitor = None
        self.scroller = None
        self.input_listener = None
        self.keyboard_hook_available = True
        self.mouse_hook_available = True

        # 更新检测状态。
        self.current_version = ""
        self.github_url = "https://github.com/CyrilPeng/FlowScroll"
        self.latest_release_version = None
        self.update_badge_mode = "hidden"

        self.preset_manager.load_from_file()

        from FlowScroll import __version__

        self.current_version = __version__
        self.version_label = (
            f"{self.current_version} (Dev)"
            if is_prerelease_version(self.current_version)
            else self.current_version
        )

    @property
    def presets(self):
        """返回当前预设字典。"""
        return self.preset_manager.presets

    @property
    def current_preset_name(self):
        """返回当前使用的预设名称。"""
        return self.preset_manager.current_preset_name

    @current_preset_name.setter
    def current_preset_name(self, value) -> None:
        """设置当前预设名称并持久化。"""
        self.preset_manager.current_preset_name = value

    def save_presets_to_file(self) -> None:
        """将当前预设和配置持久化到磁盘。"""
        self.preset_manager.save_to_file()

    def start_threads(self, overlay) -> None:
        """启动所有后台线程（窗口监控、滚动引擎、输入监听）。"""
        self.window_monitor = None
        self.scroller = None
        self.input_listener = None
        self.keyboard_hook_available = True
        self.mouse_hook_available = True

        try:
            self.window_monitor = WindowMonitor()
            self.window_monitor.start()
        except Exception as e:
            logger.error(f"Failed to start WindowMonitor: {e}")

        try:
            self.scroller = ScrollEngine(self.bridge, self.mouse_controller)
            self.scroller.start()
        except Exception as e:
            logger.error(f"Failed to start ScrollEngine: {e}")
            from FlowScroll.i18n import tr

            return [
                (
                    "critical",
                    tr("main.scroll_engine_failed.title"),
                    tr("main.scroll_engine_failed.body"),
                )
            ]

        try:
            self.input_listener = GlobalInputListener(
                self.bridge, is_current_app_allowed, self.scroller
            )
            self.input_listener.start()
            self.keyboard_hook_available = self.input_listener.keyboard_hook_available
            self.mouse_hook_available = self.input_listener.mouse_hook_available
        except Exception as e:
            logger.error(f"Failed to start GlobalInputListener: {e}")
            self.keyboard_hook_available = False
            self.mouse_hook_available = False

        # 返回需要 UI 层显示的消息列表，格式: [(level, title, body), ...]
        messages = []
        from FlowScroll.i18n import tr

        detail = self._get_input_hook_failure_detail()
        if self.scroller is None:
            messages.append(
                (
                    "critical",
                    tr("main.scroll_engine_failed.title"),
                    tr("main.scroll_engine_failed.body"),
                )
            )
        if not self.keyboard_hook_available:
            messages.append(
                (
                    "warning",
                    tr("main.keyboard_hook_failed.title"),
                    tr("main.keyboard_hook_failed.body", detail=detail),
                )
            )
        if not self.mouse_hook_available:
            messages.append(
                (
                    "warning",
                    tr("main.mouse_hook_failed.title"),
                    tr("main.mouse_hook_failed.body", detail=detail),
                )
            )
        if self.keyboard_hook_available is False and self.mouse_hook_available is False:
            try:
                from FlowScroll.services.credential_service import credential_service
            except ImportError:
                pass
            messages.append(
                (
                    "critical",
                    tr("main.permission_denied.title"),
                    tr("main.permission_denied.body"),
                )
            )
        return messages

    def check_for_updates(self, on_update_available) -> None:
        """启动更新检测线程，发现更新时回调 on_update_available。"""
        self._update_callback = on_update_available
        self.update_checker = UpdateCheckerThread(None)
        self.update_checker.update_available.connect(self._on_update_available)
        self.update_checker.start()

    def _on_update_available(self, latest_version, html_url) -> None:
        """更新检测结果处理。"""
        self.latest_release_version = latest_version
        self.github_url = html_url
        if is_prerelease_version(self.current_version):
            self.update_badge_mode = "dev"
        elif is_newer_version(latest_version, self.current_version):
            self.update_badge_mode = "update"
        else:
            self.update_badge_mode = "hidden"
        if self._update_callback:
            self._update_callback()

    def _get_input_hook_failure_detail(self) -> str:
        """按平台返回输入钩子失败的排查说明。"""
        from FlowScroll.i18n import tr

        if OS_NAME == "Darwin":
            return tr("main.input_hook_failure_detail.macos")
        if OS_NAME == "Windows":
            return tr("main.input_hook_failure_detail.windows")

        session_type = os.environ.get("XDG_SESSION_TYPE", "").strip().lower()
        has_wayland = bool(os.environ.get("WAYLAND_DISPLAY"))
        has_x11 = bool(os.environ.get("DISPLAY"))

        if session_type == "wayland" or has_wayland:
            return tr("main.input_hook_failure_detail.linux_wayland")
        if session_type == "x11" or has_x11:
            return tr("main.input_hook_failure_detail.linux_x11")
        if OS_NAME == "Linux":
            return tr("main.input_hook_failure_detail.linux_generic")

        return tr("main.input_hook_failure_detail.generic")

    def get_config_storage_summary(self) -> str:
        """返回配置存储位置的摘要文本。"""
        from FlowScroll.i18n import tr

        current_path = get_config_file()
        source = get_config_override_source()
        source_key = {
            "default": "tab.advanced.config_path_source_default",
            "custom": "tab.advanced.config_path_source_custom",
            "env_file": "tab.advanced.config_path_source_env_file",
            "env_dir": "tab.advanced.config_path_source_env_dir",
        }.get(source, "tab.advanced.config_path_source_default")
        return tr(
            "tab.advanced.config_path_summary", source=tr(source_key), path=current_path
        )

    def load_selected_preset(self, name) -> None:
        """切换到指定预设，同步 scroller 摩擦系数并持久化。"""
        if not self.preset_manager.load_preset(name):
            return
        if self.scroller:
            self.scroller.update_friction()
        self.save_presets_to_file()

    def save_new_preset(self, name) -> bool:
        """保存新预设，返回是否成功。"""
        if name in BUILTIN_PRESETS:
            return False
        self.preset_manager.save_preset(name)
        self.save_presets_to_file()
        return True

    def delete_preset(self, name) -> bool:
        """删除自定义预设，返回是否成功。"""
        if name in BUILTIN_PRESETS or name not in self.presets:
            return False
        self.preset_manager.delete_preset(name)
        self.save_presets_to_file()
        return True

    def on_inertia_settings_accepted(self) -> None:
        """惯性设置对话框确认后，更新引擎摩擦系数并持久化。"""
        if self.scroller:
            self.scroller.update_friction()
        self.save_presets_to_file()
