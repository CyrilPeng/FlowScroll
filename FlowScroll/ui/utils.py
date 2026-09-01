import os
import sys


def resource_path(relative_path):
    """
    获取资源的绝对路径，兼容开发环境、PyInstaller 和 Nuitka。
    """
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        except NameError:
            base_path = os.path.dirname(os.path.abspath(sys.argv[0]))

    return os.path.join(base_path, relative_path)
