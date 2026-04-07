import base64
import json
import socket
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

from FlowScroll.constants import (
    WEBDAV_DIALOG_DEFAULT_HEIGHT,
    WEBDAV_DIALOG_DEFAULT_WIDTH,
    WEBDAV_DIALOG_MIN_HEIGHT,
    WEBDAV_DIALOG_MIN_WIDTH,
)
from FlowScroll.core.config import cfg, ensure_config_dir, get_config_file
from FlowScroll.i18n import tr
from FlowScroll.services.credential_service import credential_service
from FlowScroll.services.logging_service import logger

try:
    from PySide6.QtCore import Qt, QThread, Signal
    from PySide6.QtWidgets import (
        QDialog,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMessageBox,
        QPushButton,
        QVBoxLayout,
    )
except ImportError:
    Qt = None

    class _BoundSignal:
        def __init__(self):
            self._callbacks = []

        def connect(self, callback) -> None:
            self._callbacks.append(callback)

        def emit(self, *args, **kwargs) -> None:
            for callback in list(self._callbacks):
                callback(*args, **kwargs)

    class Signal:
        def __init__(self, *_args, **_kwargs):
            self._name = None

        def __set_name__(self, _owner, name):
            self._name = name

        def __get__(self, instance, _owner):
            if instance is None:
                return self
            signal = instance.__dict__.get(self._name)
            if signal is None:
                signal = _BoundSignal()
                instance.__dict__[self._name] = signal
            return signal

    class QThread:
        finished = Signal()

        def __init__(self, *_args, **_kwargs):
            pass

        def start(self) -> None:
            try:
                self.run()
            finally:
                self.finished.emit()

        def deleteLater(self) -> None:
            pass

    QDialog = None
    QHBoxLayout = None
    QLabel = None
    QLineEdit = None
    QMessageBox = None
    QPushButton = None
    QVBoxLayout = None

if QDialog is not None:
    from FlowScroll.ui.styles import get_webdav_dialog_style


WEBDAV_LOG_FIELD_ORDER = (
    "event",
    "mode",
    "url",
    "username",
    "status",
    "reason",
    "error",
    "duration_ms",
)

WEBDAV_CONFIG_FILENAME = "FlowScroll_config.json"
WEBDAV_APP_DIRNAME = "FlowScroll"


def mask_webdav_username(username: str) -> str:
    value = (username or "").strip()
    if not value:
        return "<empty>"
    if len(value) <= 2:
        return value[0] + "*"
    if len(value) == 3:
        return value[0] + "*" + value[-1]
    return value[:2] + "*" * (len(value) - 3) + value[-1]


def log_webdav_event(level: str, event: str, **fields) -> None:
    normalized_fields = {"event": event, **fields}
    parts = []
    for key in WEBDAV_LOG_FIELD_ORDER:
        value = normalized_fields.pop(key, None)
        if value is None:
            continue
        text = str(value).replace("\n", "\\n")
        parts.append(f"{key}={text}")
    for key, value in normalized_fields.items():
        if value is None:
            continue
        text = str(value).replace("\n", "\\n")
        parts.append(f"{key}={text}")
    message = "WebDAV " + " ".join(parts)
    getattr(logger, level)(message)


def validate_webdav_url(url: str) -> str | None:
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return tr("webdav.invalid_url")
    return None


def normalize_webdav_base_url(url: str) -> str:
    value = (url or "").strip()
    if not value:
        return value
    return value if value.endswith("/") else value + "/"


def build_legacy_webdav_file_url(base_url: str) -> str:
    return normalize_webdav_base_url(base_url) + WEBDAV_CONFIG_FILENAME


def build_preferred_webdav_file_url(base_url: str) -> str:
    return (
        normalize_webdav_base_url(base_url)
        + WEBDAV_APP_DIRNAME
        + "/"
        + WEBDAV_CONFIG_FILENAME
    )


def build_webdav_collection_url(base_url: str) -> str:
    return normalize_webdav_base_url(base_url) + WEBDAV_APP_DIRNAME + "/"


def format_webdav_error(error: Exception) -> str:
    if isinstance(error, urllib.error.HTTPError):
        return tr(
            "webdav.http_error",
            status=error.code,
            reason=error.reason or error.__class__.__name__,
        )

    if isinstance(error, urllib.error.URLError):
        reason = error.reason
        if isinstance(reason, TimeoutError | socket.timeout):
            return tr("webdav.timeout_hint")

        winerror = getattr(reason, "winerror", None)
        if winerror == 10061:
            return tr("webdav.connection_refused_hint")

        if isinstance(reason, OSError):
            if reason.errno in (-2, 11001):
                return tr("webdav.name_resolution_hint")
            return tr("webdav.os_error_hint", error=str(reason))

        return tr("webdav.url_error_hint", error=str(reason))

    if isinstance(error, TimeoutError | socket.timeout):
        return tr("webdav.timeout_hint")

    return str(error)


class WebDAVJobThread(QThread):
    upload_finished = Signal(int)
    download_finished = Signal(dict)
    failed = Signal(str)

    def __init__(
        self,
        mode: str,
        url: str,
        auth: str,
        username: str,
        payload: dict | None = None,
    ):
        super().__init__()
        self.mode = mode
        self.url = url
        self.auth = auth
        self.username = username
        self.payload = payload or {}

    def _open(self, request: urllib.request.Request):
        return urllib.request.urlopen(request, timeout=10)

    def _upload_to_url(self, target_url: str, data: bytes):
        req = urllib.request.Request(target_url, data=data, method="PUT")
        req.add_header("Authorization", self.auth)
        req.add_header("Content-Type", "application/json")
        with self._open(req) as response:
            return int(response.status)

    def _ensure_app_collection(self):
        collection_url = build_webdav_collection_url(self.url)
        req = urllib.request.Request(collection_url, method="MKCOL")
        req.add_header("Authorization", self.auth)
        try:
            with self._open(req) as response:
                return int(getattr(response, "status", 201))
        except urllib.error.HTTPError as e:
            # 405/301/302 通常表示目录已存在或服务端自行处理为现有目录。
            if e.code in (301, 302, 405):
                return e.code
            raise

    def _upload(self):
        data = json.dumps(self.payload, ensure_ascii=False, indent=4).encode("utf-8")

        legacy_url = build_legacy_webdav_file_url(self.url)
        try:
            return self._upload_to_url(legacy_url, data)
        except urllib.error.HTTPError as e:
            # 某些 WebDAV 服务在根目录下直接 PUT 文件会返回 404，
            # 回退到应用专用子目录以提升兼容性。
            if e.code != 404:
                raise

        self._ensure_app_collection()
        preferred_url = build_preferred_webdav_file_url(self.url)
        return self._upload_to_url(preferred_url, data)

    def _download(self):
        candidate_urls = (
            build_legacy_webdav_file_url(self.url),
            build_preferred_webdav_file_url(self.url),
        )
        last_error = None
        for candidate_url in candidate_urls:
            try:
                req = urllib.request.Request(candidate_url, method="GET")
                req.add_header("Authorization", self.auth)
                with self._open(req) as response:
                    remote_data = json.loads(response.read().decode("utf-8"))
                return remote_data
            except urllib.error.HTTPError as e:
                last_error = e
                if e.code == 404:
                    continue
                raise

        if last_error is not None:
            raise last_error
        raise FileNotFoundError("No WebDAV config candidate URL resolved")

    def run(self) -> None:
        started_at = time.monotonic()
        try:
            if self.mode == "upload":
                self.upload_finished.emit(self._upload())
                return

            self.download_finished.emit(self._download())
        except Exception as e:
            duration_ms = int((time.monotonic() - started_at) * 1000)
            if isinstance(e, urllib.error.HTTPError):
                log_webdav_event(
                    "error",
                    "failed",
                    mode=self.mode,
                    url=self.url,
                    username=mask_webdav_username(self.username),
                    status=e.code,
                    reason=e.reason,
                    duration_ms=duration_ms,
                )
            else:
                log_webdav_event(
                    "error",
                    "failed",
                    mode=self.mode,
                    url=self.url,
                    username=mask_webdav_username(self.username),
                    error=repr(e),
                    duration_ms=duration_ms,
                )
            self.failed.emit(format_webdav_error(e))


if QDialog is not None:
    class WebDAVSyncDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle(tr("webdav.title"))
            self.setMinimumSize(WEBDAV_DIALOG_MIN_WIDTH, WEBDAV_DIALOG_MIN_HEIGHT)
            self.setSizeGripEnabled(True)

            self.setStyleSheet(get_webdav_dialog_style())

            layout = QVBoxLayout(self)
            layout.setContentsMargins(24, 24, 24, 24)
            layout.setSpacing(16)

            layout.addWidget(QLabel(tr("webdav.url_label")))
            self.edit_url = QLineEdit(cfg.webdav_url)
            self.edit_url.setPlaceholderText("https://...")
            layout.addWidget(self.edit_url)

            layout.addWidget(QLabel(tr("webdav.username_label")))
            self.edit_user = QLineEdit(cfg.webdav_username)
            layout.addWidget(self.edit_user)

            layout.addWidget(QLabel(tr("webdav.password_label")))
            saved_password = credential_service.load_password()
            self.edit_pwd = QLineEdit(saved_password)
            self.edit_pwd.setEchoMode(QLineEdit.Password)
            layout.addWidget(self.edit_pwd)

            if not credential_service.is_keyring_available:
                hint = QLabel(tr("webdav.keyring_unavailable_hint"))
                hint.setStyleSheet("color: #F59E0B; font-size: 11px;")
                hint.setWordWrap(True)
                layout.addWidget(hint)

            btn_layout = QHBoxLayout()
            btn_layout.setSpacing(12)

            btn_save = QPushButton(tr("webdav.save"))
            btn_save.clicked.connect(self.save_config)
            self.btn_save = btn_save

            btn_upload = QPushButton(tr("webdav.upload"))
            btn_upload.setObjectName("BtnPrimary")
            btn_upload.setCursor(Qt.PointingHandCursor)
            btn_upload.clicked.connect(self.upload_config)
            self.btn_upload = btn_upload

            btn_download = QPushButton(tr("webdav.download"))
            btn_download.setObjectName("BtnSuccess")
            btn_download.setCursor(Qt.PointingHandCursor)
            btn_download.clicked.connect(self.download_config)
            self.btn_download = btn_download

            btn_layout.addWidget(btn_save)
            btn_layout.addWidget(btn_upload)
            btn_layout.addWidget(btn_download)

            layout.addStretch()
            layout.addLayout(btn_layout)

            adaptive_height = max(WEBDAV_DIALOG_DEFAULT_HEIGHT, self.sizeHint().height())
            self.resize(WEBDAV_DIALOG_DEFAULT_WIDTH, adaptive_height)
            self._job = None

        def get_full_url(self):
            return normalize_webdav_base_url(self.edit_url.text())

        def get_auth_header(self):
            user = self.edit_user.text().strip()
            pwd = self.edit_pwd.text().strip()
            auth_str = f"{user}:{pwd}"
            encoded = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
            return f"Basic {encoded}"

        def get_username(self):
            return self.edit_user.text().strip()

        def save_config(self) -> None:
            cfg.webdav_url = self.edit_url.text().strip()
            cfg.webdav_username = self.edit_user.text().strip()
            password = self.edit_pwd.text().strip()

            if password:
                saved = credential_service.save_password(password)
                if not saved:
                    QMessageBox.warning(
                        self,
                        tr("webdav.notice_title"),
                        tr("webdav.password_session_only"),
                    )
            else:
                credential_service.delete_password()

            QMessageBox.information(
                self,
                tr("webdav.notice_title"),
                tr("webdav.saved_notice"),
            )
            self.accept()

        def upload_config(self) -> None:
            invalid = validate_webdav_url(self.edit_url.text())
            if invalid:
                log_webdav_event(
                    "error",
                    "invalid_url",
                    mode="upload",
                    url=self.edit_url.text().strip(),
                    username=mask_webdav_username(self.get_username()),
                )
                QMessageBox.warning(self, tr("webdav.failed_title"), invalid)
                return
            self._start_job(
                WebDAVJobThread(
                    "upload",
                    self.get_full_url(),
                    self.get_auth_header(),
                    self.get_username(),
                    cfg.to_dict_for_sync(),
                )
            )

        def download_config(self) -> None:
            invalid = validate_webdav_url(self.edit_url.text())
            if invalid:
                log_webdav_event(
                    "error",
                    "invalid_url",
                    mode="download",
                    url=self.edit_url.text().strip(),
                    username=mask_webdav_username(self.get_username()),
                )
                QMessageBox.warning(self, tr("webdav.failed_title"), invalid)
                return
            self._start_job(
                WebDAVJobThread(
                    "download",
                    self.get_full_url(),
                    self.get_auth_header(),
                    self.get_username(),
                )
            )

        def _set_busy(self, busy: bool):
            self.btn_save.setEnabled(not busy)
            self.btn_upload.setEnabled(not busy)
            self.btn_download.setEnabled(not busy)

        def _start_job(self, job: WebDAVJobThread):
            if self._job is not None:
                return

            self._job = job
            self._set_busy(True)
            job.upload_finished.connect(self._on_upload_finished)
            job.download_finished.connect(self._on_download_finished)
            job.failed.connect(self._on_job_failed)
            job.finished.connect(self._on_job_complete)
            job.start()

        def _on_upload_finished(self, status: int):
            if status in (200, 201, 204):
                QMessageBox.information(
                    self,
                    tr("webdav.success_title"),
                    tr("webdav.upload_success"),
                )
                return

            log_webdav_event(
                "error",
                "unexpected_status",
                mode="upload",
                url=self._job.url if self._job else "<unknown>",
                username=mask_webdav_username(
                    self._job.username if self._job else ""
                ),
                status=status,
            )
            QMessageBox.warning(
                self,
                tr("webdav.failed_title"),
                tr("webdav.upload_failed_status", status=status),
            )

        def _on_download_finished(self, remote_data: dict):
            local_webdav_url = cfg.webdav_url
            local_webdav_username = cfg.webdav_username

            cfg.from_dict(remote_data)
            cfg.webdav_url = local_webdav_url
            cfg.webdav_username = local_webdav_username

            parent = self.parent()
            if parent is not None and hasattr(parent, "save_presets_to_file"):
                parent.save_presets_to_file()
            else:
                with open(ensure_config_dir(get_config_file()), "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "presets": {},
                            "last_used": "",
                            "current_config": cfg.to_dict(),
                            "webdav": cfg.to_webdav_dict(),
                        },
                        f,
                        ensure_ascii=False,
                        indent=4,
                    )

            QMessageBox.information(
                self,
                tr("webdav.success_title"),
                tr("webdav.download_success"),
            )

        def _on_job_failed(self, error: str):
            message_key = (
                "webdav.connect_failed"
                if self._job and self._job.mode == "upload"
                else "webdav.download_failed"
            )
            QMessageBox.critical(
                self,
                tr("webdav.error_title"),
                tr(message_key, error=error),
            )

        def _on_job_complete(self):
            if self._job is not None:
                self._job.deleteLater()
                self._job = None
            self._set_busy(False)
else:
    class WebDAVSyncDialog:
        def __init__(self, *_args, **_kwargs):
            raise RuntimeError("WebDAVSyncDialog requires PySide6 with GUI dependencies")
