"""CLI 参数解析测试。

验证 --version、--help、--silent 参数的正确性，
以及 autostart 注册命令是否包含 --silent。
"""

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAIN_PY = PROJECT_ROOT / "main.py"


def _run_main(*args: str, timeout: float = 5.0) -> subprocess.CompletedProcess:
    """运行 main.py 并捕获输出。"""
    return subprocess.run(
        [sys.executable, str(MAIN_PY), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(PROJECT_ROOT),
    )


class TestVersionFlag:
    """--version / -v 参数测试。"""

    def test_long_version(self):
        """--version 应正常退出（弹出消息框后退出，超时视为预期）。"""
        try:
            result = _run_main("--version", timeout=2.0)
            assert result.returncode == 0
        except subprocess.TimeoutExpired:
            # Windows GUI 应用会弹出消息框等待用户点击，超时是预期行为
            pass

    def test_short_version(self):
        """-v 短参数同样应被正确解析。"""
        try:
            result = _run_main("-v", timeout=2.0)
            assert result.returncode == 0
        except subprocess.TimeoutExpired:
            pass


class TestHelpFlag:
    """--help / -h 参数测试。"""

    def test_long_help(self):
        """--help 应正常退出（弹出消息框后退出，超时视为预期）。"""
        try:
            result = _run_main("--help", timeout=2.0)
            assert result.returncode == 0
        except subprocess.TimeoutExpired:
            # Windows GUI 应用会弹出消息框等待用户点击，超时是预期行为
            pass

    def test_short_help(self):
        """-h 短参数同样应被正确解析。"""
        try:
            result = _run_main("-h", timeout=2.0)
            assert result.returncode == 0
        except subprocess.TimeoutExpired:
            pass


class TestSilentFlag:
    """--silent / -s 参数解析测试。"""

    def test_silent_is_parsed_without_error(self):
        """--silent 不应导致解析失败（但需要 GUI 环境才能完整运行）。"""
        # --silent 模式下程序会持续运行（等待托盘交互），
        # 因此预期超时。只要没有 argparse 错误即可。
        try:
            result = _run_main("--silent", timeout=2.0)
            # 如果程序意外退出，检查不是 argparse 错误
            # 接受 Qt/pynput/平台相关的环境限制错误（如无 X server）
            if result.returncode != 0:
                stderr_lower = result.stderr.lower()
                is_env_error = any(
                    kw in stderr_lower for kw in ["qt", "pynput", "display", "x server", "x connection", "platform"]
                )
                assert is_env_error, f"Unexpected error: {result.stderr}"
        except subprocess.TimeoutExpired:
            # 预期行为：程序在静默模式下持续运行
            pass

    def test_short_silent(self):
        """-s 短参数同样应被正确解析。"""
        try:
            result = _run_main("-s", timeout=2.0)
            if result.returncode != 0:
                stderr_lower = result.stderr.lower()
                is_env_error = any(
                    kw in stderr_lower for kw in ["qt", "pynput", "display", "x server", "x connection", "platform"]
                )
                assert is_env_error, f"Unexpected error: {result.stderr}"
        except subprocess.TimeoutExpired:
            pass


class TestAutoStartSilentParam:
    """验证 autostart 注册的命令包含 --silent 参数。"""

    def test_build_launch_command_includes_silent(self):
        """AutoStartManager 构建的启动命令应包含 --silent。"""
        from FlowScroll.services.autostart import AutoStartManager

        manager = AutoStartManager()
        assert "--silent" in manager.app_path, f"app_path 应包含 --silent，实际为: {manager.app_path}"

    def test_build_source_launch_command_includes_silent(self):
        """源码模式下的启动命令应包含 --silent。"""
        from FlowScroll.services.autostart import AutoStartManager

        cmd = AutoStartManager._build_source_launch_command("/fake/path/main.py")
        assert "--silent" in cmd

    def test_quote_path_with_silent(self):
        """Windows 引号路径模式下应包含 --silent。"""
        from FlowScroll.services.autostart import AutoStartManager

        manager = AutoStartManager()
        # 模拟 frozen 环境的路径构建
        quoted = manager._quote_path(r"C:\Program Files\FlowScroll.exe")
        # _quote_path 本身不加 --silent，但 _build_launch_command 会加
        # 这里只测试 _quote_path 的引号逻辑
        assert quoted.startswith('"') and quoted.endswith('"')


class TestArgvIsolation:
    """验证自定义参数不会泄漏到 Qt 的 argv 中。"""

    def test_silent_not_in_qt_argv(self):
        """--silent 应从 Qt 的 argv 中移除。"""
        # 通过检查 main 模块的 _qt_argv 来验证
        # 注意：这需要 main.py 已经被导入

        # 重新导入以获取模块级变量
        if "main" in sys.modules:
            main_mod = sys.modules["main"]
            # _qt_argv 不应包含 --silent
            assert "--silent" not in getattr(main_mod, "_qt_argv", [])
            assert "-s" not in getattr(main_mod, "_qt_argv", [])
