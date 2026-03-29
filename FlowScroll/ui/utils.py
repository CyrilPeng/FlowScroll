import sys
import os


def resource_path(relative_path):
    """
    获取资源的绝对路径，兼容 Nuitka 和 PyInstaller 打包后的目录结构。
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 模式下使用其临时解包目录。
        base_path = sys._MEIPASS
    elif "__compiled__" in globals() or hasattr(sys, 'frozen'):
        # Nuitka 模式下，sys.argv[0] 指向外层 exe，
        # 这里改为从当前 utils.py 所在路径向上回溯到数据根目录。
        # FlowScroll/ui/utils.py -> 上退 2 层到 FlowScroll -> 再上退 1 层到根目录。
        try:
            base_path = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
        except NameError:
            base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    else:
        # 开发源码环境直接使用当前工作目录。
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
