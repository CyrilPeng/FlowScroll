import logging
import os
import sys
import time
import tempfile
import traceback
from logging.handlers import RotatingFileHandler


def get_log_dir():
    # 将日志统一写入系统临时目录下的 flowscroll 子目录。
    temp_dir = tempfile.gettempdir()
    log_dir = os.path.join(temp_dir, "flowscroll")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


LOG_FILE = os.path.join(get_log_dir(), "app.log")
CRASH_LOG_FILE = os.path.join(get_log_dir(), "FlowScroll_Crash_Log.txt")

# 单文件最大 512KB，保留 2 个备份，总计约 1.5MB
LOG_MAX_BYTES = 512 * 1024
LOG_BACKUP_COUNT = 2
# 崩溃日志保留最近 10 次记录
CRASH_LOG_MAX_ENTRIES = 10


def is_frozen_binary():
    return bool(getattr(sys, "frozen", False))


def get_logger_level():
    return logging.ERROR if is_frozen_binary() else logging.DEBUG


def get_console_log_level():
    return logging.ERROR if is_frozen_binary() else logging.DEBUG


def setup_logging():
    logger = logging.getLogger("FlowScroll")
    logger.setLevel(get_logger_level())
    logger.propagate = False

    # 避免重复添加处理器。
    if logger.handlers:
        return logger

    # 文件处理器（带轮转：最多 3 个文件 × 512KB）
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.ERROR)

    # 控制台处理器。
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(get_console_log_level())

    # 统一日志格式。
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


logger = setup_logging()


def log_crash(exception):
    """将崩溃信息追加到崩溃日志文件（保留最近 N 条记录），返回日志路径。"""
    try:
        from FlowScroll import __version__

        # 追加模式：保留历史崩溃记录
        with open(CRASH_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n{'=' * 60}\n")
            f.write(f"FlowScroll v{__version__}\n")
            f.write(f"Crash Time: {time.ctime()}\n")
            f.write(f"Error: {str(exception)}\n")
            f.write(traceback.format_exc())
            f.write(f"{'=' * 60}\n")

        # 限制崩溃日志文件大小：保留最近 N 条记录
        _trim_crash_log()

        return CRASH_LOG_FILE
    except Exception:
        return None


def _trim_crash_log():
    """保留崩溃日志中最近 N 条记录，避免文件无限增长。"""
    try:
        if not os.path.exists(CRASH_LOG_FILE):
            return

        with open(CRASH_LOG_FILE, "r", encoding="utf-8") as f:
            content = f.read()

        # 按分隔符切分为独立崩溃记录
        separator = f"\n{'=' * 60}\n"
        # 过滤空段
        records = [r for r in content.split(separator) if r.strip()]

        if len(records) <= CRASH_LOG_MAX_ENTRIES:
            return

        # 保留最近的 N 条
        trimmed = records[-CRASH_LOG_MAX_ENTRIES:]
        with open(CRASH_LOG_FILE, "w", encoding="utf-8") as f:
            f.write(separator.join(trimmed))
    except Exception:
        pass
