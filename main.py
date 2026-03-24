# FlowScroll - 适用于全平台的平滑滚动工具
# 版本 v1.2.1
# 版权所有 (C) 2026 某不科学的高数
#
# 本程序是自由软件：您可以根据自由软件基金会发布的 GNU 通用公共许可证的条款（许可证的第 3 版，或（由您选择）任何更高版本）重新分发和/或修改它。

import sys
import ctypes
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from FlowScroll.platform import system_platform, OS_NAME
from FlowScroll.core.config import cfg
from FlowScroll.services.logging_service import logger, log_crash
from FlowScroll.ui.settings_window import MainWindow


def main():
    try:
        # 必须在 QApplication 实例化之前设置高分屏缩放策略
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        app = QApplication(sys.argv)

        if OS_NAME == "Windows":
            myappid = "cyrilpeng.FlowScroll.app.v1.2.0"
            try:
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except Exception:
                pass

        app.setQuitOnLastWindowClosed(False)

        font_name = system_platform.get_font_name()
        app.setFont(QFont(font_name, 11 if OS_NAME == "Windows" else 13))

        window = MainWindow()
        window.show()

        sys.exit(app.exec())
    except Exception as e:
        # 发生致命崩溃时，记录日志并弹窗提示
        logger.critical(f"Fatal error: {e}", exc_info=True)
        log_path = log_crash(e)
        if log_path:
            try:
                if OS_NAME == "Windows":
                    ctypes.windll.user32.MessageBoxW(
                        0,
                        f"程序遇到致命错误，日志已保存至:\\n{log_path}",
                        "FlowScroll 崩溃",
                        16,
                    )
            except Exception:
                pass
        sys.exit(1)


if __name__ == "__main__":
    main()
