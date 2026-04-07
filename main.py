# FlowScroll - 适用于全平台的平滑滚动工具
# 版权所有 (C) 2026 某不科学的高数
#
# 本程序是自由软件：您可以根据自由软件基金会发布的 GNU 通用公共许可证的条款（许可证的第 3 版，或（由您选择）任何更高版本）重新分发和/或修改它。

import sys
import ctypes
import os
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon

from FlowScroll import __version__
from FlowScroll.i18n import tr
from FlowScroll.platform import system_platform, OS_NAME
from FlowScroll.services.logging_service import logger, log_crash
from FlowScroll.services.single_instance import SingleInstanceManager
from FlowScroll.ui.utils import resource_path
from FlowScroll.ui.settings_window import MainWindow


def _show_already_running_message():
    QMessageBox.information(
        None,
        tr("main.single_instance.title"),
        tr("main.single_instance.body"),
    )


def main() -> None:
    try:
        # 必须在 QApplication 实例化之前设置高分屏缩放策略
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        app = QApplication(sys.argv)

        if OS_NAME == "Windows":
            myappid = f"cyrilpeng.FlowScroll.app.v{__version__}"
            try:
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except Exception:
                pass

        app.setQuitOnLastWindowClosed(False)

        font_name = system_platform.get_font_name()
        app.setFont(QFont(font_name, 11 if OS_NAME == "Windows" else 13))
        icon_path = resource_path(system_platform.get_icon_name())
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))

        single_instance = SingleInstanceManager("cyrilpeng.FlowScroll")
        if not single_instance.acquire():
            _show_already_running_message()
            sys.exit(0)

        window = MainWindow()
        single_instance.activation_requested.connect(window.show_normal_window)
        if single_instance.pending_activation_request:
            window.show_normal_window()
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
