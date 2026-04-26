import os
import re
import subprocess
from pathlib import Path

from FlowScroll.constants import DEFAULT_SCROLL_MULTIPLIER
from FlowScroll.platform.base import PlatformInterface
from FlowScroll.services.logging_service import logger


class LinuxPlatform(PlatformInterface):
    def __init__(self):
        self.autostart_dir = Path.home() / ".config" / "autostart"
        self.desktop_file = self.autostart_dir / "FlowScroll.desktop"

    def get_frontmost_window_info(self):
        session_type = os.environ.get("XDG_SESSION_TYPE", "").strip().lower()
        if session_type == "wayland" and not os.environ.get("DISPLAY"):
            return ("", "", "", False)

        window_ref = self._run_command(["xprop", "-root", "_NET_ACTIVE_WINDOW"])
        match = re.search(r"window id # (0x[0-9a-fA-F]+)", window_ref or "")
        if not match:
            return ("", "", "", False)

        wid = match.group(1)
        props = self._run_command([
            "xprop", "-id", wid,
            "_NET_WM_NAME", "WM_NAME", "WM_CLASS",
            "_NET_WM_PID", "_NET_WM_STATE",
        ])
        if not props:
            return ("", "", "", False)

        title = self._parse_xprop_value_from_block(props, "_NET_WM_NAME")
        if not title:
            title = self._parse_xprop_value_from_block(props, "WM_NAME")
        window_class = self._parse_wm_class_from_block(props)
        pid_match = re.search(r"_NET_WM_PID.*?=\s*(\d+)", props)
        process_name = self._read_process_name(pid_match.group(1)) if pid_match else ""
        is_fullscreen = "_NET_WM_STATE_FULLSCREEN" in props
        return (title, process_name, window_class, is_fullscreen)

    def set_autostart(self, app_name: str, app_path: str, enable: bool) -> bool:
        try:
            self.autostart_dir.mkdir(parents=True, exist_ok=True)
            if enable:
                if not app_path:
                    return False
                self.desktop_file.write_text(
                    self._build_desktop_entry(app_name, app_path),
                    encoding="utf-8",
                )
            elif self.desktop_file.exists():
                self.desktop_file.unlink()
            return True
        except Exception as e:
            logger.error(f"设置 Linux 开机自启失败: {e}")
            return False

    def is_autostart_enabled(self, app_name: str, app_path: str) -> bool:
        if not self.desktop_file.exists():
            return False

        try:
            content = self.desktop_file.read_text(encoding="utf-8")
        except Exception as e:
            logger.debug(f"读取 Linux 自启动文件失败: {e}")
            return False

        name_value = ""
        exec_value = ""
        for line in content.splitlines():
            if line.startswith("Name="):
                name_value = line[len("Name=") :].strip()
            elif line.startswith("Exec="):
                exec_value = line[len("Exec=") :].strip()
        return name_value == app_name and exec_value == app_path

    def get_scroll_multiplier(self) -> float:
        return DEFAULT_SCROLL_MULTIPLIER

    def get_font_name(self) -> str:
        return "Noto Sans"

    def get_icon_name(self) -> str:
        return os.path.join("FlowScroll", "resources", "FlowScroll.svg")

    @staticmethod
    def _run_command(command: list[str]) -> str:
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=1,
                check=False,
            )
        except FileNotFoundError:
            return ""
        except Exception as e:
            logger.debug(f"Linux command failed {command}: {e}")
            return ""

        if result.returncode != 0:
            return ""
        return result.stdout.strip()

    @staticmethod
    def _parse_xprop_value(output: str) -> str:
        if not output or "=" not in output:
            return ""
        value = output.split("=", 1)[1].strip()
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]
        return value

    @staticmethod
    def _parse_xprop_value_from_block(block: str, prop_name: str) -> str:
        for line in block.splitlines():
            if line.startswith(prop_name) and "=" in line:
                value = line.split("=", 1)[1].strip()
                if value.startswith('"') and value.endswith('"'):
                    return value[1:-1]
                return value
        return ""

    @staticmethod
    def _parse_wm_class(output: str) -> str:
        if not output or "=" not in output:
            return ""
        values = [item.strip().strip('"') for item in output.split("=", 1)[1].split(",")]
        for item in reversed(values):
            if item:
                return item
        return ""

    @staticmethod
    def _parse_wm_class_from_block(block: str) -> str:
        for line in block.splitlines():
            if line.startswith("WM_CLASS") and "=" in line:
                values = [item.strip().strip('"') for item in line.split("=", 1)[1].split(",")]
                for item in reversed(values):
                    if item:
                        return item
        return ""

    @staticmethod
    def _read_process_name(pid: str) -> str:
        try:
            with open(f"/proc/{pid}/comm", "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            return ""

    @staticmethod
    def _build_desktop_entry(app_name: str, app_path: str) -> str:
        return "\n".join(
            [
                "[Desktop Entry]",
                "Type=Application",
                f"Name={app_name}",
                f"Exec={app_path}",
                "X-GNOME-Autostart-enabled=true",
                "",
            ]
        )
