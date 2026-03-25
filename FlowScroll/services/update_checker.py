import urllib.request
import json
from PySide6.QtCore import QThread, Signal
from FlowScroll.services.logging_service import logger


def _fetch_github():
    url = "https://api.github.com/repos/CyrilPeng/FlowScroll/releases/latest"
    req = urllib.request.Request(
        url, headers={"User-Agent": "FlowScroll-Update-Checker"}
    )
    with urllib.request.urlopen(req, timeout=5) as response:
        data = json.loads(response.read().decode("utf-8"))
        version = data.get("tag_name", "").lstrip("v")
        html_url = data.get("html_url", "")
        return version, html_url


def _fetch_gitee():
    url = "https://gitee.com/api/v5/repos/Cyril_P/FlowScroll/releases/latest"
    req = urllib.request.Request(
        url, headers={"User-Agent": "FlowScroll-Update-Checker"}
    )
    with urllib.request.urlopen(req, timeout=5) as response:
        data = json.loads(response.read().decode("utf-8"))
        version = data.get("tag_name", "").lstrip("v")
        html_url = data.get("html_url", "")
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
                logger.debug(f"{name} 更新检查失败: {e}")
