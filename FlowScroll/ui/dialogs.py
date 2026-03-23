from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QCheckBox,
    QComboBox,
    QTextEdit,
    QPushButton,
)
from PySide6.QtCore import Qt
from FlowScroll.core.config import cfg


class AdvancedSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("高级规则 (防误触/过滤)")
        self.setFixedSize(400, 500)

        self.setStyleSheet("""
            QDialog { background-color: #0F172A; font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif; }
            QLabel { font-size: 14px; color: #F8FAFC; }
            QCheckBox { color: #CBD5E1; font-size: 14px; font-weight: 500; spacing: 10px; }
            QTextEdit { border: 1px solid #334155; border-radius: 8px; padding: 10px; background: #1E293B; font-size: 14px; color: #F8FAFC; }
            QTextEdit:focus { border: 1px solid #3B82F6; }
            QComboBox { border: 1px solid #334155; border-radius: 8px; padding: 8px 12px; background: #1E293B; font-size: 14px; color: #F8FAFC; }
            QComboBox::drop-down { border: none; width: 30px; }
            QPushButton#BtnPrimary { background-color: #3B82F6; color: #FFFFFF; border: none; border-radius: 8px; padding: 12px 0; font-weight: 600; font-size: 14px; }
            QPushButton#BtnPrimary:hover { background-color: #2563EB; }
            QPushButton#BtnPrimary:pressed { background-color: #1D4ED8; }
            QFrame#Line { background-color: #334155; max-height: 1px; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        self.chk_fullscreen = QCheckBox("智能防误触：在所有全屏程序中自动禁用")
        self.chk_fullscreen.setChecked(cfg.disable_fullscreen)
        self.chk_fullscreen.setStyleSheet("color: #FCA5A5;")  # Red accent
        layout.addWidget(self.chk_fullscreen)

        self.chk_desktop = QCheckBox("屏蔽系统桌面：在桌面上自动禁用滚动")
        self.chk_desktop.setChecked(cfg.disable_desktop)
        self.chk_desktop.setStyleSheet("color: #93C5FD;")  # Blue accent
        layout.addWidget(self.chk_desktop)

        line = QFrame()
        line.setObjectName("Line")
        layout.addWidget(line)

        layout.addWidget(QLabel("<span style='font-weight: 600;'>应用过滤模式</span>"))
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(
            [
                "全局生效 (不进行过滤)",
                "黑名单模式 (在以下程序中禁用)",
                "白名单模式 (仅在以下程序中启用)",
            ]
        )
        self.combo_mode.setCurrentIndex(cfg.filter_mode)
        layout.addWidget(self.combo_mode)

        layout.addWidget(
            QLabel(
                "<span style='font-weight: 600;'>输入应用名称关键词 (每行一个)</span><br><span style='color: #94A3B8; font-size: 12px;'>例如输入 'League' 或 'AutoCAD'</span>"
            )
        )
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText("\\n".join(cfg.filter_list))
        layout.addWidget(self.text_edit)

        btn_layout = QHBoxLayout()
        btn_save = QPushButton("保存规则")
        btn_save.setObjectName("BtnPrimary")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.clicked.connect(self.save_and_close)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def save_and_close(self):
        cfg.disable_fullscreen = self.chk_fullscreen.isChecked()
        cfg.disable_desktop = self.chk_desktop.isChecked()
        cfg.filter_mode = self.combo_mode.currentIndex()
        lines = self.text_edit.toPlainText().split("\\n")
        cfg.filter_list = [line.strip() for line in lines if line.strip()]
        self.accept()
