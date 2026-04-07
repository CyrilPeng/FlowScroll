import json
import urllib.request

from packaging.version import InvalidVersion, Version

from FlowScroll.constants import UPDATE_CHECK_TIMEOUT
from FlowScroll.services.logging_service import logger

try:
    from PySide6.QtCore import QThread, Signal
except ModuleNotFoundError:  # pragma: no cover - 用于无 GUI 测试环境下的降级替身
    class QThread:
        def __init__(self, *_args, **_kwargs):
            pass

    class Signal:
        def __init__(self, *_args, **_kwargs):
            pass


GITHUB_FALLBACK_URL = "https://github.com/CyrilPeng/FlowScroll/releases"
GITEE_FALLBACK_URL = "https://gitee.com/Cyril_P/FlowScroll/releases"


def parse_version(version: str) -> Version | None:
    token = (version or "").strip()
    if not token:
        return None
    if token.startswith(("v", "V")):
        token = token[1:]
    try:
        return Version(token)
    except InvalidVersion:
        return None


def is_prerelease_version(version: str) -> bool:
    parsed = parse_version(version)
    if parsed is None:
        return False
    return parsed.is_prerelease or parsed.is_devrelease


def is_newer_version(latest_version: str, current_version: str) -> bool:
    latest = parse_version(latest_version)
    current = parse_version(current_version)
    if latest is None or current is None:
        return False

    if latest.is_prerelease or latest.is_devrelease:
        return False

    return latest > current


def _fetch_github():
    url = "https://api.github.com/repos/CyrilPeng/FlowScroll/releases/latest"
    req = urllib.request.Request(
        url, headers={"User-Agent": "FlowScroll-Update-Checker"}
    )
    with urllib.request.urlopen(req, timeout=UPDATE_CHECK_TIMEOUT) as response:
        data = json.loads(response.read().decode("utf-8"))
        version = data.get("tag_name", "").lstrip("v")
        html_url = data.get("html_url", "") or GITHUB_FALLBACK_URL
        return version, html_url


def _fetch_gitee():
    url = "https://gitee.com/api/v5/repos/Cyril_P/FlowScroll/releases/latest"
    req = urllib.request.Request(
        url, headers={"User-Agent": "FlowScroll-Update-Checker"}
    )
    with urllib.request.urlopen(req, timeout=UPDATE_CHECK_TIMEOUT) as response:
        data = json.loads(response.read().decode("utf-8"))
        version = data.get("tag_name", "").lstrip("v")
        html_url = data.get("html_url", "") or GITEE_FALLBACK_URL
        return version, html_url


class UpdateCheckerThread(QThread):
    update_available = Signal(str, str)  # 版本号、发布地址

    def run(self) -> None:
        # 优先检查 GitHub，失败后再回退到 Gitee。
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
