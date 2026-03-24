import urllib.request
import json
from PySide6.QtCore import QThread, Signal

class UpdateCheckerThread(QThread):
    update_available = Signal(str, str)  # version, url

    def run(self):
        try:
            url = "https://api.github.com/repos/CyrilPeng/FlowScroll/releases/latest"
            req = urllib.request.Request(url, headers={'User-Agent': 'FlowScroll-Update-Checker'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                latest_version = data.get("tag_name", "").lstrip("v")
                html_url = data.get("html_url", "")
                if latest_version:
                    self.update_available.emit(latest_version, html_url)
        except Exception:
            pass
