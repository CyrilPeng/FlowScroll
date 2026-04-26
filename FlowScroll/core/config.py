import json
import ntpath
import os
import posixpath
import re
import tempfile
import threading
from dataclasses import dataclass
from typing import Tuple

from FlowScroll.constants import (
    CONFIG_VERSION,
    DEFAULT_INERTIA_FRICTION_MS,
    DEFAULT_INERTIA_THRESHOLD,
    WINDOW_INFO_FAILURE_STALE_THRESHOLD,
)

CONFIG_FILENAME = "FlowScroll_config.json"
APP_DIR_NAME = "FlowScroll"
CONFIG_POINTER_FILENAME = "config_path.json"
CONFIG_FILE_ENV_VAR = "FLOWSCROLL_CONFIG_FILE"
CONFIG_DIR_ENV_VAR = "FLOWSCROLL_CONFIG_DIR"
LEGACY_CONFIG_FILE = os.path.join(os.path.expanduser("~"), f".{CONFIG_FILENAME}")


def _is_windows_target() -> bool:
    """判断当前目标平台是否为 Windows。"""
    return os.name == "nt" or os.sys.platform == "win32"


def _path_module_for(path: str | None = None):
    """根据路径特征或当前平台选择 ntpath / posixpath 模块。"""
    if path and re.match(r"^[A-Za-z]:[\\/]", path):
        return ntpath
    if path and path.startswith("\\\\"):
        return ntpath
    return ntpath if _is_windows_target() else posixpath


def _join_path(*parts: str) -> str:
    """使用目标平台对应的路径模块拼接路径。"""
    return _path_module_for().join(*parts)


def _dirname_path(path: str) -> str:
    """使用目标平台对应的路径模块获取目录名。"""
    return _path_module_for(path).dirname(path)


def _normalize_path(path: str) -> str:
    """展开环境变量和用户主目录，返回绝对路径。"""
    path_module = _path_module_for(path)
    expanded = path_module.expandvars(path_module.expanduser(path))
    return path_module.abspath(expanded)


def _paths_equal(path_a: str, path_b: str) -> bool:
    """比较两条路径在归一化后是否相等，兼容跨平台路径格式。"""
    module_a = _path_module_for(path_a)
    module_b = _path_module_for(path_b)
    normalized_a = module_a.normcase(module_a.normpath(_normalize_path(path_a)))
    normalized_b = module_b.normcase(module_b.normpath(_normalize_path(path_b)))
    return normalized_a == normalized_b


def get_default_config_dir() -> str:
    """按平台返回 FlowScroll 默认配置目录路径。"""
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return _join_path(appdata, APP_DIR_NAME)
        return _join_path(
            os.path.expanduser("~"),
            "AppData",
            "Roaming",
            APP_DIR_NAME,
        )

    if os.sys.platform == "darwin":
        return _join_path(
            os.path.expanduser("~"),
            "Library",
            "Application Support",
            APP_DIR_NAME,
        )

    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        return _join_path(xdg_config_home, APP_DIR_NAME)
    return _join_path(os.path.expanduser("~"), ".config", APP_DIR_NAME)


CONFIG_FILE = _join_path(get_default_config_dir(), CONFIG_FILENAME)


def get_config_pointer_file() -> str:
    """返回配置指针文件路径（用于存储自定义配置文件位置）。"""
    return _join_path(get_default_config_dir(), CONFIG_POINTER_FILENAME)


def get_config_override_source() -> str:
    """判断配置路径来源：env_file / env_dir / custom / default。"""
    if os.environ.get(CONFIG_FILE_ENV_VAR, "").strip():
        return "env_file"
    if os.environ.get(CONFIG_DIR_ENV_VAR, "").strip():
        return "env_dir"
    if get_persisted_config_file():
        return "custom"
    return "default"


def get_persisted_config_file() -> str:
    """从指针文件中读取已持久化的自定义配置文件路径，未设置时返回空字符串。"""
    pointer_file = get_config_pointer_file()
    try:
        with open(pointer_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return ""

    if not isinstance(data, dict):
        return ""

    persisted_path = str(data.get("config_file", "")).strip()
    if not persisted_path:
        return ""

    normalized_path = _normalize_path(persisted_path)
    if _paths_equal(normalized_path, CONFIG_FILE):
        return ""
    return normalized_path


def set_persisted_config_file(path: str | None) -> None:
    """将自定义配置文件路径写入指针文件，或清除指针（路径为空/默认时删除文件）。"""
    normalized_default = _normalize_path(CONFIG_FILE)
    normalized_path = _normalize_path(path) if path else ""
    pointer_file = get_config_pointer_file()

    if not normalized_path or _paths_equal(normalized_path, normalized_default):
        try:
            os.remove(pointer_file)
        except FileNotFoundError:
            pass
        return

    os.makedirs(_dirname_path(pointer_file), exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=_dirname_path(pointer_file), suffix=".tmp"
    )
    try:
        if os.name != "nt":
            os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"config_file": normalized_path}, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, pointer_file)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def get_config_file() -> str:
    """解析当前生效的配置文件路径，优先级：环境变量 > 指针文件 > 默认。"""
    explicit_file = os.environ.get(CONFIG_FILE_ENV_VAR, "").strip()
    if explicit_file:
        return _normalize_path(explicit_file)

    explicit_dir = os.environ.get(CONFIG_DIR_ENV_VAR, "").strip()
    if explicit_dir:
        return _path_module_for(explicit_dir).join(
            _normalize_path(explicit_dir),
            CONFIG_FILENAME,
        )

    persisted_file = get_persisted_config_file()
    if persisted_file:
        return persisted_file

    return _normalize_path(CONFIG_FILE)


def get_config_load_candidates() -> list[str]:
    """返回按优先级排列的配置文件候选列表（主路径 + 默认路径 + 旧版路径）。"""
    primary_path = get_config_file()
    candidates = [primary_path]

    if get_config_override_source().startswith("env_"):
        return candidates

    default_path = _normalize_path(CONFIG_FILE)
    if default_path not in candidates:
        candidates.append(default_path)

    legacy_path = _normalize_path(LEGACY_CONFIG_FILE)
    if legacy_path not in candidates:
        candidates.append(legacy_path)

    return candidates


def ensure_config_dir(path: str | None = None) -> str:
    """确保配置目录存在，返回配置文件路径。"""
    config_path = path or get_config_file()
    config_dir = _dirname_path(config_path)
    if config_dir:
        os.makedirs(config_dir, exist_ok=True)
    return config_path


BUILTIN_PRESETS = {
    "网页阅读": {
        "sensitivity": 1.5,
        "speed_factor": 3.0,
        "dead_zone": 25.0,
    },
    "代码办公": {
        "sensitivity": 2.5,
        "speed_factor": 2.5,
        "dead_zone": 15.0,
    },
    "长文档/表格": {
        "sensitivity": 2.0,
        "speed_factor": 2.0,
        "dead_zone": 20.0,
        "enable_horizontal": True,
    },
    "轻柔/接近触控板": {
        "sensitivity": 1.2,
        "speed_factor": 1.5,
        "dead_zone": 10.0,
    },
}

# 预设共享的默认值，每个预设只需覆盖差异字段。
_PRESET_DEFAULTS = {
    "overlay_size": 60.0,
    "enable_horizontal": False,
    "minimize_to_tray": True,
    "horizontal_hotkey": "",
    "activation_hotkey_click": "",
    "activation_hotkey_hold": "",
    "activation_mode": 0,
    "activation_compat_mode": False,
    "activation_delay_ms": 0,
    "filter_mode": 0,
    "filter_blacklist": [],
    "filter_whitelist": [],
    "filter_use_regex": False,
    "disable_fullscreen": True,
    "disable_desktop": True,
}

# 将共享默认值合并到各预设中，避免重复定义。
for _name, _preset in BUILTIN_PRESETS.items():
    for _key, _value in _PRESET_DEFAULTS.items():
        _preset.setdefault(_key, _value)

DEFAULT_PRESET_NAME = "长文档/表格"

PRESET_DISPLAY_KEYS = {
    "网页阅读": "preset.web_reading",
    "代码办公": "preset.code_office",
    "长文档/表格": "preset.long_doc_table",
    "轻柔/接近触控板": "preset.gentle_touchpad",
}


def get_preset_display_name(name: str) -> str:
    """返回预设的本地化显示名称，非内置预设原样返回。"""
    i18n_key = PRESET_DISPLAY_KEYS.get(name)
    if not i18n_key:
        return name
    from FlowScroll.i18n import tr
    return tr(i18n_key)


def get_preset_internal_name(display_name: str) -> str:
    """将本地化显示名称反查为内部预设键名，非内置预设原样返回。"""
    from FlowScroll.i18n import tr
    for internal_name, i18n_key in PRESET_DISPLAY_KEYS.items():
        if tr(i18n_key) == display_name:
            return internal_name
    return display_name


@dataclass
class RuntimeState:
    """运行时状态，不持久化，仅在当前进程生命周期内有效。"""

    active: bool = False
    origin_pos: Tuple[int, int] = (0, 0)
    current_window_name: str = ""
    current_process_name: str = ""
    process_name_status: str = "unknown"
    last_match_target: str = ""
    current_window_class: str = ""
    is_fullscreen: bool = False
    window_info_failure_count: int = 0

    @property
    def window_info_is_stale(self) -> bool:
        return self.window_info_failure_count >= WINDOW_INFO_FAILURE_STALE_THRESHOLD


class GlobalConfig:
    """
    持久化用户配置。
    运行时状态已拆分到 RuntimeState。
    """

    def __init__(self):
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

        self.hide_overlay = False  # 是否隐藏准星

        self.activation_mode = 0  # 0=点击中键启用/关闭, 1=长按中键时启用
        self.activation_compat_mode = False
        self.activation_delay_ms = 0
        self.ui_language = "auto"
        self.filter_mode = 0
        self.filter_blacklist = []
        self.filter_whitelist = []
        self.filter_use_regex = False
        self.disable_fullscreen = True
        self.disable_desktop = True

        self.enable_inertia = False
        self.inertia_friction_ms = DEFAULT_INERTIA_FRICTION_MS
        self.inertia_threshold = DEFAULT_INERTIA_THRESHOLD

        self.webdav_url = ""
        self.webdav_username = ""

    def _to_dict_common(self) -> dict:
        """生成配置字典的公共部分，供 to_dict 和 to_dict_for_sync 复用。"""
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
            "hide_overlay": self.hide_overlay,
            "filter_mode": self.filter_mode,
            "filter_blacklist": list(self.filter_blacklist),
            "filter_whitelist": list(self.filter_whitelist),
            "filter_use_regex": self.filter_use_regex,
            "filter_list": self._get_active_filter_list(),
            "disable_fullscreen": self.disable_fullscreen,
            "disable_desktop": self.disable_desktop,
            "activation_mode": self.activation_mode,
            "activation_compat_mode": self.activation_compat_mode,
            "activation_delay_ms": self.activation_delay_ms,
            "ui_language": self.ui_language,
            "enable_inertia": self.enable_inertia,
            "inertia_friction_ms": self.inertia_friction_ms,
            "inertia_threshold": self.inertia_threshold,
        }

    def to_dict(self):
        """返回配置字典（运行时 + 持久化字段的合集）。"""
        return self._to_dict_common()

    def to_webdav_dict(self) -> dict:
        """返回 WebDAV 相关配置字典（仅 URL 和用户名，不含密码）。"""
        return {
            "url": self.webdav_url,
            "username": self.webdav_username,
        }

    def to_dict_for_sync(self) -> dict:
        """生成用于 WebDAV 同步的配置字典，不包含 WebDAV 凭据。"""
        return self._to_dict_common()

    def from_dict(self, data) -> None:
        """从字典中恢复配置值，处理旧版 filter_list 到 blacklist/whitelist 的迁移。"""
        with STATE_LOCK:
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
            self.hide_overlay = data.get("hide_overlay", False)
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
                if self.filter_mode == 2:
                    self.filter_whitelist = legacy_list
                else:
                    self.filter_whitelist = []

            self.filter_blacklist = [
                str(v).strip() for v in self.filter_blacklist if str(v).strip()
            ]
            self.filter_whitelist = [
                str(v).strip() for v in self.filter_whitelist if str(v).strip()
            ]
            self.filter_use_regex = data.get("filter_use_regex", False)
            self.disable_fullscreen = data.get("disable_fullscreen", True)
            self.disable_desktop = data.get("disable_desktop", True)
            self.activation_mode = data.get("activation_mode", 0)
            self.activation_compat_mode = data.get("activation_compat_mode", False)
            self.activation_delay_ms = int(data.get("activation_delay_ms", 0))
            self.ui_language = data.get("ui_language", "auto")
            self.enable_inertia = data.get("enable_inertia", False)
            self.inertia_friction_ms = data.get("inertia_friction_ms", 500)
            self.inertia_threshold = data.get("inertia_threshold", 80.0)

    def from_webdav_dict(self, data) -> None:
        """从字典中恢复 WebDAV URL 和用户名。"""
        with STATE_LOCK:
            if not isinstance(data, dict):
                self.webdav_url = ""
                self.webdav_username = ""
                return
            self.webdav_url = str(data.get("url", "")).strip()
            self.webdav_username = str(data.get("username", "")).strip()

    def _get_active_filter_list(self):
        """根据 filter_mode 返回当前生效的过滤列表（黑名单或白名单）。"""
        if self.filter_mode == 1:
            return list(self.filter_blacklist)
        if self.filter_mode == 2:
            return list(self.filter_whitelist)
        return []


cfg = GlobalConfig()
runtime = RuntimeState()
STATE_LOCK = threading.RLock()


def set_config_attr(name: str, value) -> None:
    """线程安全地设置 cfg 属性，所有 UI 侧对 cfg 的写操作应通过此函数。"""
    with STATE_LOCK:
        setattr(cfg, name, value)
