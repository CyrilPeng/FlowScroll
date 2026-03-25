import os

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
        "filter_mode": 0,
        "filter_list": [],
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
        "filter_mode": 0,
        "filter_list": [],
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
        "filter_mode": 0,
        "filter_list": [],
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
        "filter_mode": 0,
        "filter_list": [],
        "disable_fullscreen": True,
        "disable_desktop": True,
    },
}

DEFAULT_PRESET_NAME = "长文档/表格"


class GlobalConfig:
    """
    全局配置与状态管理
    按照重构计划拆分为：持久化用户配置、运行时状态。
    """

    def __init__(self):
        # ==========================================
        # 1. 持久化用户配置 (默认值 = 长文档/表格 预设)
        # ==========================================
        self.config_version = 2

        defaults = BUILTIN_PRESETS[DEFAULT_PRESET_NAME]
        self.dead_zone = defaults["dead_zone"]
        self.sensitivity = defaults["sensitivity"]
        self.speed_factor = defaults["speed_factor"]
        self.overlay_size = defaults["overlay_size"]
        self.enable_horizontal = defaults["enable_horizontal"]
        self.minimize_to_tray = defaults["minimize_to_tray"]

        self.horizontal_hotkey = ""

        self.reverse_y = False
        self.reverse_x = False

        self.filter_mode = 0
        self.filter_list = []
        self.disable_fullscreen = True
        self.disable_desktop = True

        # ==========================================
        # WebDAV Sync Config
        # ==========================================
        self.webdav_url = ""
        self.webdav_username = ""
        self.webdav_password = ""

        # ==========================================
        # 2. 运行时状态 (不持久化)
        # ==========================================
        self.active = False
        self.origin_pos = (0, 0)
        self.current_window_name = ""
        self.current_window_class = ""
        self.is_fullscreen = False

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
            "reverse_y": self.reverse_y,
            "reverse_x": self.reverse_x,
            "filter_mode": self.filter_mode,
            "filter_list": self.filter_list,
            "disable_fullscreen": self.disable_fullscreen,
            "disable_desktop": self.disable_desktop,
            "webdav_url": self.webdav_url,
            "webdav_username": self.webdav_username,
            "webdav_password": self.webdav_password,
        }

    def from_dict(self, data):
        # 兼容旧版本配置
        _version = data.get("config_version", 1)

        self.sensitivity = data.get("sensitivity", 2.0)
        self.speed_factor = data.get("speed_factor", 2.0)
        self.dead_zone = data.get("dead_zone", 20.0)
        self.overlay_size = data.get("overlay_size", 60.0)
        self.enable_horizontal = data.get("enable_horizontal", True)
        self.minimize_to_tray = data.get("minimize_to_tray", True)
        self.horizontal_hotkey = data.get("horizontal_hotkey", "")
        self.reverse_y = data.get("reverse_y", False)
        self.reverse_x = data.get("reverse_x", False)
        self.filter_mode = data.get("filter_mode", 0)
        self.filter_list = data.get("filter_list", [])
        self.disable_fullscreen = data.get("disable_fullscreen", True)
        self.disable_desktop = data.get("disable_desktop", True)
        self.webdav_url = data.get("webdav_url", "")
        self.webdav_username = data.get("webdav_username", "")
        self.webdav_password = data.get("webdav_password", "")


cfg = GlobalConfig()
