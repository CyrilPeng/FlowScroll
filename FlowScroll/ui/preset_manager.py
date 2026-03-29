import json
import os
from typing import Dict, List

from FlowScroll.core.config import (
    BUILTIN_PRESETS,
    CONFIG_FILE,
    DEFAULT_PRESET_NAME,
    cfg,
)
from FlowScroll.services.logging_service import logger


class PresetManager:
    """负责预设的加载、保存与切换。"""

    def __init__(self):
        self.presets: Dict[str, dict] = {}
        self.current_preset_name: str = DEFAULT_PRESET_NAME

    def _serialize_state(self) -> dict:
        return {
            "presets": self.presets,
            "last_used": self.current_preset_name,
            "current_config": cfg.to_dict(),
        }

    def load_from_file(self) -> None:
        """从配置文件中加载预设和当前配置。"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
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
                        last_used
                        if last_used in BUILTIN_PRESETS or last_used in self.presets
                        else DEFAULT_PRESET_NAME
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
                return
            except Exception as e:
                logger.warning(f"Failed to load presets from file: {e}")

        self.presets = {}
        self.current_preset_name = DEFAULT_PRESET_NAME
        cfg.from_dict(BUILTIN_PRESETS[DEFAULT_PRESET_NAME])

    def save_to_file(self) -> None:
        """将预设与当前配置写回配置文件。"""
        data = self._serialize_state()
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"Failed to save presets to file: {e}")

    def get_all_names(self) -> List[str]:
        """返回所有可选预设名称。"""
        return list(BUILTIN_PRESETS.keys()) + list(self.presets.keys())

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
