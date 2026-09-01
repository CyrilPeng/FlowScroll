import json
import os
import tempfile
import time
from typing import Dict, List

from FlowScroll.core.config import (
    _paths_equal,
    BUILTIN_PRESETS,
    DEFAULT_PRESET_NAME,
    cfg,
    ensure_config_dir,
    get_config_file,
    get_config_load_candidates,
    get_preset_display_name,
)
from FlowScroll.services.logging_service import logger


class PresetManager:
    """负责预设的加载、保存与切换。"""

    def __init__(self):
        self.presets: Dict[str, dict] = {}
        self.current_preset_name: str = DEFAULT_PRESET_NAME
        self.last_recovery_backup_path: str | None = None

    def _serialize_state(self) -> dict:
        return {
            "presets": self.presets,
            "last_used": self.current_preset_name,
            "current_config": cfg.to_dict(),
            "webdav": cfg.to_webdav_dict(),
        }

    def _load_webdav_settings(self, data, current_config, last_used):
        webdav_settings = data.get("webdav")
        if isinstance(webdav_settings, dict):
            cfg.from_webdav_dict(webdav_settings)
            return

        legacy_sources = []
        if isinstance(current_config, dict):
            legacy_sources.append(current_config)
        if last_used in self.presets:
            legacy_sources.append(self.presets[last_used])

        for source in legacy_sources:
            url = source.get("webdav_url", "")
            username = source.get("webdav_username", "")
            if url or username:
                cfg.from_webdav_dict({"url": url, "username": username})
                return

        cfg.from_webdav_dict({})

    def _backup_invalid_config(self, config_path: str) -> str | None:
        """将无效配置移到同目录备份，避免后续保存覆盖用户原始数据。"""
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        base_path = f"{config_path}.invalid-{timestamp}.bak"
        backup_path = base_path
        suffix = 1
        while os.path.exists(backup_path):
            backup_path = f"{base_path}.{suffix}"
            suffix += 1

        try:
            os.replace(config_path, backup_path)
        except OSError as error:
            logger.error(f"Failed to back up invalid config '{config_path}': {error}")
            return None

        self.last_recovery_backup_path = backup_path
        logger.warning(f"Invalid config backed up to: {backup_path}")
        return backup_path

    def load_from_file(self) -> None:
        """从配置文件中加载预设和当前配置。"""
        self.last_recovery_backup_path = None
        loaded_from = None
        for candidate in get_config_load_candidates():
            if os.path.exists(candidate):
                loaded_from = candidate
                break

        if loaded_from:
            try:
                with open(loaded_from, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if not isinstance(data, dict):
                    raise ValueError("Preset config root must be a JSON object")

                presets = data.get("presets", {})
                if not isinstance(presets, dict):
                    raise ValueError("Preset config 'presets' must be an object")

                last_used = data.get("last_used", DEFAULT_PRESET_NAME)
                if not isinstance(last_used, str):
                    raise ValueError("Preset config 'last_used' must be a string")

                current_config = data.get("current_config")
                if current_config is not None and not isinstance(current_config, dict):
                    raise ValueError("Preset config 'current_config' must be an object")

                self.presets = {
                    str(name): value
                    for name, value in presets.items()
                    if isinstance(name, str) and isinstance(value, dict)
                }

                if current_config is not None:
                    self.current_preset_name = (
                        last_used if last_used in BUILTIN_PRESETS or last_used in self.presets else DEFAULT_PRESET_NAME
                    )
                    cfg.from_dict(current_config)
                elif last_used in BUILTIN_PRESETS:
                    self.current_preset_name = last_used
                    cfg.from_dict(BUILTIN_PRESETS[last_used])
                elif last_used in self.presets:
                    self.current_preset_name = last_used
                    cfg.from_dict(self.presets[last_used])
                else:
                    self.presets = {}
                    self.current_preset_name = DEFAULT_PRESET_NAME
                    cfg.from_dict(BUILTIN_PRESETS[DEFAULT_PRESET_NAME])
                self._load_webdav_settings(data, current_config, last_used)
                target_path = get_config_file()
                if not _paths_equal(loaded_from, target_path):
                    self.save_to_file()
                return
            except (KeyError, TypeError, ValueError) as e:
                logger.warning(f"Failed to load presets from file: {e}")
                if self._backup_invalid_config(loaded_from):
                    self.presets = {}
                    self.current_preset_name = DEFAULT_PRESET_NAME
                    cfg.from_dict(BUILTIN_PRESETS[DEFAULT_PRESET_NAME])
                    cfg.from_webdav_dict({})
                    self.save_to_file()
                    return
            except OSError as e:
                logger.warning(f"Failed to read presets from file: {e}")
            except Exception as e:
                logger.warning(f"Unexpected preset loading error: {e}", exc_info=True)

        self.presets = {}
        self.current_preset_name = DEFAULT_PRESET_NAME
        cfg.from_dict(BUILTIN_PRESETS[DEFAULT_PRESET_NAME])
        cfg.from_webdav_dict({})

    def save_to_file(self, target_path: str | None = None) -> bool:
        """将预设与当前配置写回配置文件（原子写入，非 Windows 下限制文件权限）。"""
        data = self._serialize_state()
        config_path = ensure_config_dir(target_path) if target_path else ensure_config_dir()
        config_dir = os.path.dirname(config_path)
        try:
            fd, tmp_path = tempfile.mkstemp(dir=config_dir, suffix=".tmp")
            try:
                if os.name != "nt":
                    os.fchmod(fd, 0o600)
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                os.replace(tmp_path, config_path)
            except BaseException:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                raise
            return True
        except Exception as e:
            logger.error(f"Failed to save presets to file: {e}")
            return False

    def get_all_names(self) -> List[str]:
        """返回所有可选预设名称（内部键名）。"""
        return list(BUILTIN_PRESETS.keys()) + list(self.presets.keys())

    def get_all_display_names(self) -> List[str]:
        """返回所有可选预设的本地化显示名称。"""
        return [get_preset_display_name(n) for n in self.get_all_names()]

    def save_preset(self, name: str) -> bool:
        """将当前配置保存为一个自定义预设。"""
        if name in BUILTIN_PRESETS:
            return False
        self.presets[name] = cfg.to_dict()
        self.current_preset_name = name
        self.save_to_file()
        return True

    def delete_preset(self, name: str) -> bool:
        """删除一个自定义预设。"""
        if name in BUILTIN_PRESETS or name not in self.presets:
            return False
        del self.presets[name]
        self.current_preset_name = DEFAULT_PRESET_NAME
        self.save_to_file()
        return True

    def load_preset(self, name: str) -> bool:
        """切换到指定预设。"""
        if name in BUILTIN_PRESETS:
            cfg.from_dict(BUILTIN_PRESETS[name])
            self.current_preset_name = name
            return True
        if name in self.presets:
            cfg.from_dict(self.presets[name])
            self.current_preset_name = name
            return True
        return False
