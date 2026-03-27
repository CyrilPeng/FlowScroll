import urllib.request
import json
import re
from FlowScroll.services.logging_service import logger

try:
    from PySide6.QtCore import QThread, Signal
except ModuleNotFoundError:  # pragma: no cover - test fallback for non-GUI environments
    class QThread:
        def __init__(self, *_args, **_kwargs):
            pass

    class Signal:
        def __init__(self, *_args, **_kwargs):
            pass


GITHUB_FALLBACK_URL = "https://github.com/CyrilPeng/FlowScroll/releases"
GITEE_FALLBACK_URL = "https://gitee.com/Cyril_P/FlowScroll/releases"


def parse_version_components(version: str) -> tuple[int, ...]:
    if not version:
        return ()
    return tuple(int(part) for part in re.findall(r"\d+", version))


def is_prerelease_version(version: str) -> bool:
    normalized = version.lower()
    return any(marker in normalized for marker in ("alpha", "beta", "rc", "pre", "dev"))


def is_newer_version(latest_version: str, current_version: str) -> bool:
    if is_prerelease_version(latest_version):
        return False

    latest = parse_version_components(latest_version)
    current = parse_version_components(current_version)
    if not latest or not current:
        return False

    max_len = max(len(latest), len(current))
    latest += (0,) * (max_len - len(latest))
    current += (0,) * (max_len - len(current))
    return latest > current


def _fetch_github():
    url = "https://api.github.com/repos/CyrilPeng/FlowScroll/releases/latest"
    req = urllib.request.Request(
        url, headers={"User-Agent": "FlowScroll-Update-Checker"}
    )
    with urllib.request.urlopen(req, timeout=5) as response:
        data = json.loads(response.read().decode("utf-8"))
        version = data.get("tag_name", "").lstrip("v")
        html_url = data.get("html_url", "") or GITHUB_FALLBACK_URL
        return version, html_url


def _fetch_gitee():
    url = "https://gitee.com/api/v5/repos/Cyril_P/FlowScroll/releases/latest"
    req = urllib.request.Request(
        url, headers={"User-Agent": "FlowScroll-Update-Checker"}
    )
    with urllib.request.urlopen(req, timeout=5) as response:
        data = json.loads(response.read().decode("utf-8"))
        version = data.get("tag_name", "").lstrip("v")
        html_url = data.get("html_url", "") or GITEE_FALLBACK_URL
        return version, html_url


class UpdateCheckerThread(QThread):
    update_available = Signal(str, str)  # version, url

    def run(self):
        # 优先 GitHub，失败则回退 Gitee
        for name, fetcher in [("GitHub", _fetch_github), ("Gitee", _fetch_gitee)]:
            try:
                version, html_url = fetcher()
                if version:
                    logger.info(f"更新检查成功 ({name}): v{version}")
                    self.update_available.emit(version, html_url)
                    return
            except Exception as e:
                logger.warning(f"{name} 更新检查失败: {e}")
        logger.warning("所有更新检查源均失败，未检测到可用版本")
