# FlowScroll - 适用于全平台的平滑滚动工具
# 版权所有 (C) 2026 某不科学的高数
#
# 本程序是自由软件：您可以根据自由软件基金会发布的 GNU 通用公共许可证的条款（许可证的第 3 版，或（由您选择）任何更高版本）重新分发和/或修改它。

import sys
import ctypes
import os
import argparse

from FlowScroll import __version__


def _show_message_box(title: str, message: str) -> None:
    """在 Windows 上用 MessageBox 显示信息（无需控制台），其他平台用 print。"""
    if sys.platform == "win32":
        try:
            # MB_OK | MB_ICONINFORMATION = 0x40
            ctypes.windll.user32.MessageBoxW(0, message, title, 0x40)
        except Exception:
            pass
    else:
        print(f"{title}\n\n{message}")


class _MessageBoxHelpAction(argparse.Action):
    """自定义 help action：用消息框显示帮助信息（兼容无控制台的 Windows GUI 应用）。"""

    def __call__(self, parser, namespace, values, option_string=None):
        help_text = parser.format_help()
        _show_message_box("FlowScroll", help_text)
        parser.exit()


# ---- CLI 参数解析 ----
# 在 QApplication 实例化之前完成，避免 Qt 干扰自定义参数。
_parser = argparse.ArgumentParser(
    prog="FlowScroll",
    description="全局无级滚动工具——把浏览器里的中键自动滚动，带到整个系统。",
    add_help=False,  # 禁用默认 help，使用自定义消息框实现
)
_parser.add_argument(
    "-h", "--help",
    action=_MessageBoxHelpAction,
    nargs=0,
    default=argparse.SUPPRESS,
    help="显示此帮助信息。",
)
_parser.add_argument(
    "-v", "--version",
    action="store_true",
    default=False,
    help="显示版本号。",
)
_parser.add_argument(
    "-s", "--silent",
    action="store_true",
    default=False,
    help="静默启动：不显示主窗口，仅在系统托盘运行。",
)

# 仅解析 FlowScroll 自有的参数，将其从 argv 中移除，
# 剩余参数留给 QApplication（Qt 会消费 --style 等内置参数）。
_known_args, _qt_argv = _parser.parse_known_args()

# --version / --help 使用消息框显示（Windows GUI 应用无控制台）
if _known_args.version:
    _show_message_box("FlowScroll", f"FlowScroll v{__version__}")
    sys.exit(0)

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon

from FlowScroll.i18n import tr
from FlowScroll.platform import system_platform, OS_NAME
from FlowScroll.services.logging_service import logger, log_crash
from FlowScroll.services.single_instance import SingleInstanceManager
from FlowScroll.ui.utils import resource_path
from FlowScroll.ui.settings_window import MainWindow


def _show_already_running_message():
    """检测到已有实例运行时，弹窗提示用户。"""
    QMessageBox.information(
        None,
        tr("main.single_instance.title"),
        tr("main.single_instance.body"),
    )


def main() -> None:
    """应用入口：初始化 QApplication、单实例检查、主窗口与事件循环。"""
    try:
        # 必须在 QApplication 实例化之前设置高分屏缩放策略
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        # 使用移除自定义参数后的 argv，避免 Qt 报未知参数 warning。
        app = QApplication([sys.argv[0]] + _qt_argv)

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

        # --silent 模式下不显示主窗口，仅通过托盘图标运行。
        if not _known_args.silent:
            window.show()

        sys.exit(app.exec())
    except Exception as e:
        # 发生致命崩溃时，记录日志并弹窗提示。
        logger.critical(f"Fatal error: {e}", exc_info=True)
        log_path = log_crash(e)
        if log_path:
            try:
                crash_title = "FlowScroll Crash"
                crash_body = f"A fatal error occurred. Log saved to:\n{log_path}"
                try:
                    crash_title = tr("main.crash.title")
                    crash_body = tr("main.crash.body", path=log_path)
                except Exception:
                    pass
                if OS_NAME == "Windows":
                    ctypes.windll.user32.MessageBoxW(
                        0, crash_body, crash_title, 16,
                    )
                else:
                    import traceback

                    traceback.print_exc()
            except Exception:
                pass
        sys.exit(1)


if __name__ == "__main__":
    main()
