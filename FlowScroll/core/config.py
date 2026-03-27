import os
from dataclasses import dataclass
from typing import Tuple

from FlowScroll.constants import (
    CONFIG_VERSION,
    DEFAULT_INERTIA_FRICTION_MS,
    DEFAULT_INERTIA_THRESHOLD,
)

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".FlowScroll_config.json")

BUILTIN_PRESETS = {
    "网页阅读": {
        "sensitivity": 1.5,
        "speed_factor": 3.0,
        "dead_zone": 25.0,
        "overlay_size": 60.0,
        "enable_horizontal": False,
        "minimize_to_tray": True,
        "horizontal_hotkey": "",
        "activation_hotkey_click": "",
        "activation_hotkey_hold": "",
        "activation_mode": 0,
        "filter_mode": 0,
        "filter_blacklist": [],
        "filter_whitelist": [],
        "disable_fullscreen": True,
        "disable_desktop": True,
    },
    "代码办公": {
        "sensitivity": 2.5,
        "speed_factor": 2.5,
        "dead_zone": 15.0,
        "overlay_size": 60.0,
        "enable_horizontal": False,
        "minimize_to_tray": True,
        "horizontal_hotkey": "",
        "activation_hotkey_click": "",
        "activation_hotkey_hold": "",
        "activation_mode": 0,
        "filter_mode": 0,
        "filter_blacklist": [],
        "filter_whitelist": [],
        "disable_fullscreen": True,
        "disable_desktop": True,
    },
    "长文档/表格": {
        "sensitivity": 2.0,
        "speed_factor": 2.0,
        "dead_zone": 20.0,
        "overlay_size": 60.0,
        "enable_horizontal": True,
        "minimize_to_tray": True,
        "horizontal_hotkey": "",
        "activation_hotkey_click": "",
        "activation_hotkey_hold": "",
        "activation_mode": 0,
        "filter_mode": 0,
        "filter_blacklist": [],
        "filter_whitelist": [],
        "disable_fullscreen": True,
        "disable_desktop": True,
    },
    "轻柔/接近触控板": {
        "sensitivity": 1.2,
        "speed_factor": 1.5,
        "dead_zone": 10.0,
        "overlay_size": 60.0,
        "enable_horizontal": False,
        "minimize_to_tray": True,
        "horizontal_hotkey": "",
        "activation_hotkey_click": "",
        "activation_hotkey_hold": "",
        "activation_mode": 0,
        "filter_mode": 0,
        "filter_blacklist": [],
        "filter_whitelist": [],
        "disable_fullscreen": True,
        "disable_desktop": True,
    },
}

DEFAULT_PRESET_NAME = "长文档/表格"


@dataclass
class RuntimeState:
    """运行时状态，不持久化，进程生命周期内有效。"""

    active: bool = False
    origin_pos: Tuple[int, int] = (0, 0)
    current_window_name: str = ""
    current_window_class: str = ""
    is_fullscreen: bool = False


class GlobalConfig:
    """
    持久化用户配置。
    运行时状态已拆分到 RuntimeState。
    """

    def __init__(self):
        # ==========================================
        # 持久化用户配置 (默认值 = 长文档/表格 预设)
        # ==========================================
        self.config_version = CONFIG_VERSION

        defaults = BUILTIN_PRESETS[DEFAULT_PRESET_NAME]
        self.dead_zone = defaults["dead_zone"]
        self.sensitivity = defaults["sensitivity"]
        self.speed_factor = defaults["speed_factor"]
        self.overlay_size = defaults["overlay_size"]
        self.enable_horizontal = defaults["enable_horizontal"]
        self.minimize_to_tray = defaults["minimize_to_tray"]

        self.horizontal_hotkey = ""
        self.activation_hotkey_click = ""
        self.activation_hotkey_hold = ""

        self.reverse_y = False
        self.reverse_x = False

        self.activation_mode = 0  # 0=点击中键启用/关闭, 1=长按中键时启用
        self.filter_mode = 0
        self.filter_blacklist = []
        self.filter_whitelist = []
        self.disable_fullscreen = True
        self.disable_desktop = True

        # ==========================================
        # 惯性滚动配置
        # ==========================================
        self.enable_inertia = False
        self.inertia_friction_ms = DEFAULT_INERTIA_FRICTION_MS
        self.inertia_threshold = DEFAULT_INERTIA_THRESHOLD

        # ==========================================
        # WebDAV 连接信息 (非敏感)
        # ==========================================
        self.webdav_url = ""
        self.webdav_username = ""

    def to_dict(self):
        return {
            "config_version": self.config_version,
            "sensitivity": self.sensitivity,
            "speed_factor": self.speed_factor,
            "dead_zone": self.dead_zone,
            "overlay_size": self.overlay_size,
            "enable_horizontal": self.enable_horizontal,
            "minimize_to_tray": self.minimize_to_tray,
            "horizontal_hotkey": self.horizontal_hotkey,
            "activation_hotkey_click": self.activation_hotkey_click,
            "activation_hotkey_hold": self.activation_hotkey_hold,
            "reverse_y": self.reverse_y,
            "reverse_x": self.reverse_x,
            "filter_mode": self.filter_mode,
            "filter_blacklist": self.filter_blacklist,
            "filter_whitelist": self.filter_whitelist,
            "filter_list": self._get_active_filter_list(),
            "disable_fullscreen": self.disable_fullscreen,
            "disable_desktop": self.disable_desktop,
            "activation_mode": self.activation_mode,
            "webdav_url": self.webdav_url,
            "webdav_username": self.webdav_username,
            "enable_inertia": self.enable_inertia,
            "inertia_friction_ms": self.inertia_friction_ms,
            "inertia_threshold": self.inertia_threshold,
        }

    def to_dict_for_sync(self) -> dict:
        """生成用于 WebDAV 同步的配置字典，不包含 WebDAV 凭据"""
        return {
            "config_version": self.config_version,
            "sensitivity": self.sensitivity,
            "speed_factor": self.speed_factor,
            "dead_zone": self.dead_zone,
            "overlay_size": self.overlay_size,
            "enable_horizontal": self.enable_horizontal,
            "minimize_to_tray": self.minimize_to_tray,
            "horizontal_hotkey": self.horizontal_hotkey,
            "activation_hotkey_click": self.activation_hotkey_click,
            "activation_hotkey_hold": self.activation_hotkey_hold,
            "reverse_y": self.reverse_y,
            "reverse_x": self.reverse_x,
            "filter_mode": self.filter_mode,
            "filter_blacklist": self.filter_blacklist,
            "filter_whitelist": self.filter_whitelist,
            "filter_list": self._get_active_filter_list(),
            "disable_fullscreen": self.disable_fullscreen,
            "disable_desktop": self.disable_desktop,
            "activation_mode": self.activation_mode,
            "enable_inertia": self.enable_inertia,
            "inertia_friction_ms": self.inertia_friction_ms,
            "inertia_threshold": self.inertia_threshold,
        }

    def from_dict(self, data):
        self.sensitivity = data.get("sensitivity", 2.0)
        self.speed_factor = data.get("speed_factor", 2.0)
        self.dead_zone = data.get("dead_zone", 20.0)
        self.overlay_size = data.get("overlay_size", 60.0)
        self.enable_horizontal = data.get("enable_horizontal", True)
        self.minimize_to_tray = data.get("minimize_to_tray", True)
        self.horizontal_hotkey = data.get("horizontal_hotkey", "")
        self.activation_hotkey_click = data.get("activation_hotkey_click", "")
        self.activation_hotkey_hold = data.get("activation_hotkey_hold", "")
        self.reverse_y = data.get("reverse_y", False)
        self.reverse_x = data.get("reverse_x", False)
        self.filter_mode = data.get("filter_mode", 0)
        legacy_list = data.get("filter_list", [])
        self.filter_blacklist = data.get("filter_blacklist")
        self.filter_whitelist = data.get("filter_whitelist")

        if self.filter_blacklist is None:
            if self.filter_mode in (0, 1):
                self.filter_blacklist = legacy_list
            else:
                self.filter_blacklist = []
        if self.filter_whitelist is None:
            if self.filter_mode in (0, 2):
                self.filter_whitelist = legacy_list
            else:
                self.filter_whitelist = []

        self.filter_blacklist = [
            str(v).strip() for v in self.filter_blacklist if str(v).strip()
        ]
        self.filter_whitelist = [
            str(v).strip() for v in self.filter_whitelist if str(v).strip()
        ]
        self.disable_fullscreen = data.get("disable_fullscreen", True)
        self.disable_desktop = data.get("disable_desktop", True)
        self.activation_mode = data.get("activation_mode", 0)
        self.webdav_url = data.get("webdav_url", "")
        self.webdav_username = data.get("webdav_username", "")
        self.enable_inertia = data.get("enable_inertia", False)
        self.inertia_friction_ms = data.get("inertia_friction_ms", 500)
        self.inertia_threshold = data.get("inertia_threshold", 80.0)


    def _get_active_filter_list(self):
        if self.filter_mode == 1:
            return list(self.filter_blacklist)
        if self.filter_mode == 2:
            return list(self.filter_whitelist)
        return []

cfg = GlobalConfig()
runtime = RuntimeState()
