import json
from typing import Dict, List

from FlowScroll.core.config import (
    cfg,
    CONFIG_FILE,
    BUILTIN_PRESETS,
    DEFAULT_PRESET_NAME,
)
from FlowScroll.services.logging_service import logger


class PresetManager:
    """预设管理器，负责预设的加载、保存和切换"""

    def __init__(self):
        self.presets: Dict[str, dict] = {}
        self.current_preset_name: str = DEFAULT_PRESET_NAME

    def load_from_file(self) -> None:
        """从配置文件加载预设"""
        import os

        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.presets = data.get("presets", {})
                    last_used = data.get("last_used", DEFAULT_PRESET_NAME)

                    if last_used in BUILTIN_PRESETS:
                        self.current_preset_name = last_used
                        cfg.from_dict(BUILTIN_PRESETS[last_used])
                    elif last_used in self.presets:
                        self.current_preset_name = last_used
                        cfg.from_dict(self.presets[last_used])
                    else:
                        self.current_preset_name = DEFAULT_PRESET_NAME
                        cfg.from_dict(BUILTIN_PRESETS[DEFAULT_PRESET_NAME])
            except Exception as e:
                logger.warning(f"Failed to load presets from file: {e}")
                self.current_preset_name = DEFAULT_PRESET_NAME
                cfg.from_dict(BUILTIN_PRESETS[DEFAULT_PRESET_NAME])
        else:
            self.current_preset_name = DEFAULT_PRESET_NAME
            cfg.from_dict(BUILTIN_PRESETS[DEFAULT_PRESET_NAME])

    def save_to_file(self) -> None:
        """保存预设到配置文件"""
        data = {"presets": self.presets, "last_used": self.current_preset_name}
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"Failed to save presets to file: {e}")

    def get_all_names(self) -> List[str]:
        """获取所有预设名称"""
        return list(BUILTIN_PRESETS.keys()) + list(self.presets.keys())

    def save_preset(self, name: str) -> bool:
        """保存当前配置为预设"""
        if name in BUILTIN_PRESETS:
            return False
        self.presets[name] = cfg.to_dict()
        self.current_preset_name = name
        self.save_to_file()
        return True

    def delete_preset(self, name: str) -> bool:
        """删除预设"""
        if name in BUILTIN_PRESETS or name not in self.presets:
            return False
        del self.presets[name]
        self.current_preset_name = DEFAULT_PRESET_NAME
        self.save_to_file()
        return True

    def load_preset(self, name: str) -> bool:
        """加载预设"""
        if name in BUILTIN_PRESETS:
            cfg.from_dict(BUILTIN_PRESETS[name])
            self.current_preset_name = name
            return True
        elif name in self.presets:
            cfg.from_dict(self.presets[name])
            self.current_preset_name = name
            return True
        return False
