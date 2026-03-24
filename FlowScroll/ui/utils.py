import sys
import os

def resource_path(relative_path):
    """
    获取资源的绝对路径，兼容 PyInstaller 打包后的路径。
    """
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        # 为了兼容，依然使用当前工作目录
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
