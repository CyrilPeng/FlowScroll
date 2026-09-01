"""rules.py 边界条件与 fallback 逻辑的回归测试。

覆盖 test_services.py::TestRules 与 test_regex_filter.py 之外的场景：
- 桌面窗口拦截 (Progman/WorkerW) 与平台差异
- 白名单模式下空 match_target 的回退行为
- filter_mode 未知值回退到 "允许"
- 进程名/窗口名的前后空白剥离
- 黑名单短路与（第一条规则即匹配）
"""

import pytest


@pytest.fixture(autouse=True)
def _reset_rules_state():
    """每个测试前后重置 cfg/runtime 中可能被修改的字段，并清空正则缓存。"""
    from FlowScroll.core.config import cfg, runtime
    from FlowScroll.core import rules as rules_module

    # 保存
    snapshot = dict(
        filter_mode=cfg.filter_mode,
        filter_blacklist=list(cfg.filter_blacklist),
        filter_whitelist=list(cfg.filter_whitelist),
        filter_use_regex=cfg.filter_use_regex,
        disable_fullscreen=cfg.disable_fullscreen,
        disable_desktop=cfg.disable_desktop,
        is_fullscreen=runtime.is_fullscreen,
        current_process_name=runtime.current_process_name,
        current_window_name=runtime.current_window_name,
        process_name_status=runtime.process_name_status,
        current_window_class=runtime.current_window_class,
    )

    rules_module._compile_regex.cache_clear()
    yield
    # 还原
    for k, v in snapshot.items():
        if hasattr(cfg, k):
            setattr(cfg, k, v)
        else:
            setattr(runtime, k, v)
    rules_module._compile_regex.cache_clear()


# ---- 桌面窗口拦截 ----


class TestDisableDesktop:
    """禁用 Windows 桌面滚动增强。"""

    def test_progman_blocked_on_windows(self, monkeypatch):
        monkeypatch.setattr("FlowScroll.core.rules.OS_NAME", "Windows")
        from FlowScroll.core.config import cfg, runtime
        from FlowScroll.core.rules import is_current_app_allowed

        cfg.filter_mode = 0
        cfg.disable_desktop = True
        cfg.disable_fullscreen = False
        runtime.is_fullscreen = False
        runtime.current_window_class = "Progman"
        runtime.process_name_status = "available"

        assert is_current_app_allowed() is False

    def test_workerw_blocked_on_windows(self, monkeypatch):
        monkeypatch.setattr("FlowScroll.core.rules.OS_NAME", "Windows")
        from FlowScroll.core.config import cfg, runtime
        from FlowScroll.core.rules import is_current_app_allowed

        cfg.filter_mode = 0
        cfg.disable_desktop = True
        runtime.is_fullscreen = False
        runtime.current_window_class = "WorkerW"
        runtime.process_name_status = "available"

        assert is_current_app_allowed() is False

    def test_other_windows_class_not_blocked_by_desktop_rule(self, monkeypatch):
        """非桌面窗口 (普通应用) 即使有桌面窗口 class 特征也不受桌面规则影响。"""
        monkeypatch.setattr("FlowScroll.core.rules.OS_NAME", "Windows")
        from FlowScroll.core.config import cfg, runtime
        from FlowScroll.core.rules import is_current_app_allowed

        cfg.filter_mode = 0
        cfg.disable_desktop = True
        runtime.is_fullscreen = False
        runtime.current_window_class = "Chrome_WidgetWin_1"
        runtime.process_name_status = "available"

        assert is_current_app_allowed() is True

    def test_disable_desktop_ignored_on_macos(self, monkeypatch):
        """macOS 下 disable_desktop 不应阻止任何窗口。"""
        monkeypatch.setattr("FlowScroll.core.rules.OS_NAME", "Darwin")
        from FlowScroll.core.config import cfg, runtime
        from FlowScroll.core.rules import is_current_app_allowed

        cfg.filter_mode = 0
        cfg.disable_desktop = True
        runtime.is_fullscreen = False
        runtime.current_window_class = "Progman"  # 即使在 Darwin 也不会触发
        runtime.process_name_status = "available"

        assert is_current_app_allowed() is True

    def test_disable_desktop_ignored_when_off(self, monkeypatch):
        """在 Windows 下若 disable_desktop=False，Progman 也不受限制。"""
        monkeypatch.setattr("FlowScroll.core.rules.OS_NAME", "Windows")
        from FlowScroll.core.config import cfg, runtime
        from FlowScroll.core.rules import is_current_app_allowed

        cfg.filter_mode = 0
        cfg.disable_desktop = False
        runtime.is_fullscreen = False
        runtime.current_window_class = "Progman"
        runtime.process_name_status = "available"

        assert is_current_app_allowed() is True


# ---- 白名单空目标回退 ----


class TestWhitelistEmptyTargetFallback:
    """白名单模式下若无法确定 match_target，应宽容放行（避免错误阻止应用）。"""

    def test_whitelist_allows_when_match_target_is_empty(self):
        from FlowScroll.core.config import cfg, runtime
        from FlowScroll.core.rules import is_current_app_allowed

        cfg.filter_mode = 2
        cfg.filter_whitelist = ["chrome"]
        cfg.filter_blacklist = []
        cfg.filter_use_regex = False
        cfg.disable_fullscreen = False
        runtime.is_fullscreen = False
        runtime.process_name_status = "stale"  # 无法得到任何进程信息
        runtime.current_process_name = ""
        runtime.current_window_name = ""

        assert is_current_app_allowed() is True


# ---- filter_mode 回退 ----


class TestFilterModeFallback:
    """filter_mode 不在 {0, 1, 2} 范围内时默认允许，不崩溃。"""

    def test_unknown_filter_mode_allows_everything(self):
        from FlowScroll.core.config import cfg, runtime
        from FlowScroll.core.rules import is_current_app_allowed

        cfg.filter_mode = 99
        cfg.filter_blacklist = ["chrome"]
        cfg.filter_whitelist = []
        cfg.disable_fullscreen = False
        runtime.is_fullscreen = False
        runtime.current_process_name = "chrome"
        runtime.process_name_status = "available"

        assert is_current_app_allowed() is True


# ---- 前后空白规范化 ----


class TestWhitespaceStripping:
    """进程名和窗口名前导/尾随空白在匹配前会被剥离。"""

    def test_leading_trailing_whitespace_in_process_name_stripped(self):
        from FlowScroll.core.config import cfg, runtime
        from FlowScroll.core.rules import is_current_app_allowed

        cfg.filter_mode = 1
        cfg.filter_blacklist = ["chrome"]
        cfg.filter_whitelist = []
        cfg.filter_use_regex = False
        cfg.disable_fullscreen = False
        runtime.is_fullscreen = False
        runtime.current_process_name = "  google chrome  "
        runtime.process_name_status = "available"

        assert is_current_app_allowed() is False

    def test_whitespace_in_window_name_stripped_in_fallback(self):
        from FlowScroll.core.config import cfg, runtime
        from FlowScroll.core.rules import is_current_app_allowed

        cfg.filter_mode = 1
        cfg.filter_blacklist = ["chrome"]
        cfg.filter_whitelist = []
        cfg.filter_use_regex = False
        cfg.disable_fullscreen = False
        runtime.is_fullscreen = False
        runtime.current_process_name = ""
        runtime.current_window_name = "  Google Chrome  "
        runtime.process_name_status = "unavailable"

        assert is_current_app_allowed() is False


# ---- 黑名单短路与 ----


class TestBlacklistShortCircuit:
    """黑名单模式应尽快返回，且不会因单条规则异常导致后续规则失效。"""

    def test_blacklist_returns_false_on_first_match(self):
        """第一条规则即命中时，后续规则（即便是无效正则）不影响结果。"""
        from FlowScroll.core.config import cfg, runtime
        from FlowScroll.core.rules import is_current_app_allowed

        cfg.filter_mode = 1
        cfg.filter_blacklist = ["chrome", "[invalid_regex_later"]
        cfg.filter_use_regex = True
        cfg.disable_fullscreen = False
        runtime.is_fullscreen = False
        runtime.current_process_name = "chrome"
        runtime.process_name_status = "available"

        # 即便第二条规则是无效正则，chrome 仍应被第一条规则拦截
        # 这同时验证了"短路" 与 "无效正则不会抛异常" 两个不变量
        assert is_current_app_allowed() is False

    def test_blacklist_falls_through_when_no_hit(self):
        """所有规则都不命中时，黑名单模式应放行（而非被某条无效规则意外阻断）。"""
        from FlowScroll.core.config import cfg, runtime
        from FlowScroll.core.rules import is_current_app_allowed

        cfg.filter_mode = 1
        cfg.filter_blacklist = ["[invalid_regex_first", "[invalid_regex_second", "edge"]
        cfg.filter_use_regex = True
        cfg.disable_fullscreen = False
        runtime.is_fullscreen = False
        runtime.current_process_name = "potplayer"
        runtime.process_name_status = "available"

        # 前两条无效正则全部静默跳过，第三条不匹配 → 允许
        assert is_current_app_allowed() is True


# ---- 空列表边界 ----


class TestEmptyFilterLists:
    """空名单在不同 filter_mode 下的表现。"""

    def test_blacklist_empty_allows_all(self):
        from FlowScroll.core.config import cfg, runtime
        from FlowScroll.core.rules import is_current_app_allowed

        cfg.filter_mode = 1
        cfg.filter_blacklist = []
        cfg.filter_whitelist = ["chrome"]
        cfg.filter_use_regex = False
        cfg.disable_fullscreen = False
        runtime.is_fullscreen = False
        runtime.current_process_name = "potplayer"
        runtime.process_name_status = "available"

        assert is_current_app_allowed() is True

    def test_whitelist_empty_blocks_all_when_process_known(self):
        from FlowScroll.core.config import cfg, runtime
        from FlowScroll.core.rules import is_current_app_allowed

        cfg.filter_mode = 2
        cfg.filter_blacklist = []
        cfg.filter_whitelist = []
        cfg.filter_use_regex = False
        cfg.disable_fullscreen = False
        runtime.is_fullscreen = False
        runtime.current_process_name = "chrome"
        runtime.process_name_status = "available"

        assert is_current_app_allowed() is False
