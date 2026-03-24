import sys
import os

def resource_path(relative_path):
    """
    获取资源的绝对路径，兼容 Nuitka (Standalone / Onefile) 和 PyInstaller 打包后的路径。
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller
        base_path = sys._MEIPASS
    elif "__compiled__" in globals() or hasattr(sys, 'frozen'):
        # Nuitka 模式下
        # 对于 Nuitka standalone 和 onefile，打包的 data-dir 或 data-files 
        # 会被放置在可执行文件（在 onefile 模式下是解压后的临时可执行文件）所在的同级目录中。
        base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    else:
        # 开发源码环境
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
