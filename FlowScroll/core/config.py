import os

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".FlowScroll_config.json")


class GlobalConfig:
    """
    全局配置与状态管理
    按照重构计划拆分为：持久化用户配置、运行时状态。
    """

    def __init__(self):
        # ==========================================
        # 1. 持久化用户配置
        # ==========================================
        self.config_version = 2

        self.dead_zone = 20.0
        self.sensitivity = 2.0
        self.speed_factor = 2.0
        self.overlay_size = 60.0
        self.enable_horizontal = True
        self.minimize_to_tray = True  # Default: on

        self.horizontal_hotkey = ""

        self.filter_mode = 0
        self.filter_list = []
        self.disable_fullscreen = (
            True  # Merged from disable_fullscreen and disable_desktop
        )

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
            "filter_mode": self.filter_mode,
            "filter_list": self.filter_list,
            "disable_fullscreen": self.disable_fullscreen,
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
        self.filter_mode = data.get("filter_mode", 0)
        self.filter_list = data.get("filter_list", [])
        self.disable_fullscreen = data.get("disable_fullscreen", True)
        self.webdav_url = data.get("webdav_url", "")
        self.webdav_username = data.get("webdav_username", "")
        self.webdav_password = data.get("webdav_password", "")


cfg = GlobalConfig()
