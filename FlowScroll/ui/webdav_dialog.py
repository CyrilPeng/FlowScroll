import base64
import json
import urllib.request
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
)
from PySide6.QtCore import Qt

from FlowScroll.core.config import cfg, CONFIG_FILE
from FlowScroll.ui.styles import get_webdav_dialog_style
from FlowScroll.constants import WEBDAV_DIALOG_WIDTH, WEBDAV_DIALOG_HEIGHT


class WebDAVSyncDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("WebDAV 云同步配置")
        self.setFixedSize(WEBDAV_DIALOG_WIDTH, WEBDAV_DIALOG_HEIGHT)

        self.setStyleSheet(get_webdav_dialog_style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # URL
        layout.addWidget(QLabel("WebDAV 链接 (例如: https://dav.jianguoyun.com/dav/)"))
        self.edit_url = QLineEdit(cfg.webdav_url)
        self.edit_url.setPlaceholderText("https://...")
        layout.addWidget(self.edit_url)

        # Username
        layout.addWidget(QLabel("用户名 / 账号"))
        self.edit_user = QLineEdit(cfg.webdav_username)
        layout.addWidget(self.edit_user)

        # Password
        layout.addWidget(QLabel("密码 / 应用授权码"))
        self.edit_pwd = QLineEdit(cfg.webdav_password)
        self.edit_pwd.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.edit_pwd)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        btn_save = QPushButton("保存配置")
        btn_save.clicked.connect(self.save_config)

        btn_upload = QPushButton("上传配置")
        btn_upload.setObjectName("BtnPrimary")
        btn_upload.setCursor(Qt.PointingHandCursor)
        btn_upload.clicked.connect(self.upload_config)

        btn_download = QPushButton("下载配置")
        btn_download.setObjectName("BtnSuccess")
        btn_download.setCursor(Qt.PointingHandCursor)
        btn_download.clicked.connect(self.download_config)

        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_upload)
        btn_layout.addWidget(btn_download)

        layout.addStretch()
        layout.addLayout(btn_layout)

    def get_full_url(self):
        url = self.edit_url.text().strip()
        if not url.endswith("/"):
            url += "/"
        return url + "FlowScroll_config.json"

    def get_auth_header(self):
        user = self.edit_user.text().strip()
        pwd = self.edit_pwd.text().strip()
        auth_str = f"{user}:{pwd}"
        return f"Basic {base64.b64encode(auth_str.encode('utf-8')).decode('utf-8')}"

    def save_config(self):
        cfg.webdav_url = self.edit_url.text().strip()
        cfg.webdav_username = self.edit_user.text().strip()
        cfg.webdav_password = self.edit_pwd.text().strip()
        QMessageBox.information(
            self, "提示", "WebDAV 配置已暂存，请记得在主界面保存预设以持久化。"
        )
        self.accept()

    def upload_config(self):
        url = self.get_full_url()
        auth = self.get_auth_header()

        try:
            # 只上传参数配置，不上传 WebDAV 凭据
            sync_data = cfg.to_dict_for_sync()
            data = json.dumps(sync_data, ensure_ascii=False, indent=4).encode("utf-8")

            req = urllib.request.Request(url, data=data, method="PUT")
            req.add_header("Authorization", auth)
            req.add_header("Content-Type", "application/json")

            with urllib.request.urlopen(req) as response:
                if response.status in (200, 201, 204):
                    QMessageBox.information(
                        self, "成功", "配置已成功上传至 WebDAV 云端！"
                    )
                else:
                    QMessageBox.warning(
                        self, "失败", f"上传失败，状态码: {response.status}"
                    )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"连接 WebDAV 失败:\\n{str(e)}")

    def download_config(self):
        url = self.get_full_url()
        auth = self.get_auth_header()

        try:
            req = urllib.request.Request(url, method="GET")
            req.add_header("Authorization", auth)

            with urllib.request.urlopen(req) as response:
                remote_data = json.loads(response.read().decode("utf-8"))

            # 保留本地的 WebDAV 凭据
            local_webdav_url = cfg.webdav_url
            local_webdav_username = cfg.webdav_username
            local_webdav_password = cfg.webdav_password

            # 从云端加载参数配置
            cfg.from_dict(remote_data)

            # 恢复本地 WebDAV 凭据
            cfg.webdav_url = local_webdav_url
            cfg.webdav_username = local_webdav_username
            cfg.webdav_password = local_webdav_password

            # 保存到本地文件
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg.to_dict(), f, ensure_ascii=False, indent=4)

            QMessageBox.information(
                self, "成功", "配置已从云端下载成功！重启程序或重新加载预设生效。"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "错误", f"下载配置失败，可能云端尚无配置文件:\\n{str(e)}"
            )
