import logging
import os
import sys
import time
import tempfile
import traceback


def get_log_dir():
    # 将日志统一写入系统临时目录下的 flowscroll 子目录。
    temp_dir = tempfile.gettempdir()
    log_dir = os.path.join(temp_dir, "flowscroll")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


LOG_FILE = os.path.join(get_log_dir(), "app.log")


def setup_logging():
    logger = logging.getLogger("FlowScroll")
    logger.setLevel(logging.DEBUG)

    # 避免重复添加处理器。
    if logger.handlers:
        return logger

    # 文件处理器。
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)

    # 控制台处理器。
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # 统一日志格式。
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


logger = setup_logging()


def log_crash(exception):
    crash_log_path = os.path.join(get_log_dir(), "FlowScroll_Crash_Log.txt")
    try:
        from FlowScroll import __version__

        with open(crash_log_path, "w", encoding="utf-8") as f:
            f.write(f"FlowScroll v{__version__}\n")
            f.write(f"Crash Time: {time.ctime()}\n")
            f.write(f"Error: {str(exception)}\n")
            f.write(traceback.format_exc())
        return crash_log_path
    except Exception:
        return None
