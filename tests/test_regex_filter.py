"""正则匹配过滤功能测试。"""

import re

import pytest


class TestRegexValidationHelpers:
    def test_collect_invalid_regex_lines_preserves_original_line_numbers(self):
        from FlowScroll.core.filter_validation import collect_invalid_regex_lines

        raw_text = "\n[invalid\n\n  ^chrome$  \n*bad\n"
        assert collect_invalid_regex_lines(raw_text) == [(2, "[invalid"), (5, "*bad")]

    def test_collect_invalid_regex_lines_handles_windows_newlines(self):
        from FlowScroll.core.filter_validation import collect_invalid_regex_lines

        raw_text = "\r\n[bad\r\n\r\n  (?P<name\r\n"
        assert collect_invalid_regex_lines(raw_text) == [(2, "[bad"), (4, "(?P<name")]


class TestMatchKeyword:
    """测试 _match_keyword 辅助函数的模糊/正则匹配逻辑。"""

    def test_fuzzy_mode_substring_match(self):
        from FlowScroll.core.rules import _match_keyword

        # target 已经由 is_current_app_allowed 预处理为小写
        assert _match_keyword("chrome", "google chrome", use_regex=False) is True
        assert _match_keyword("chrome", "chrome.exe", use_regex=False) is True
        assert _match_keyword("chrome", "chromium-browser", use_regex=False) is False
        assert _match_keyword("chrome", "firefox", use_regex=False) is False

    def test_fuzzy_mode_case_insensitive(self):
        from FlowScroll.core.rules import _match_keyword

        # keyword 在函数内 lowercase，target 在调用前已 lowercase
        assert _match_keyword("Chrome", "google chrome", use_regex=False) is True
        assert _match_keyword("CHROME", "chrome", use_regex=False) is True

    def test_regex_mode_basic_match(self):
        from FlowScroll.core.rules import _match_keyword

        assert _match_keyword("^chrome$", "chrome", use_regex=True) is True
        assert _match_keyword("^chrome$", "google chrome", use_regex=True) is False

    def test_regex_mode_case_insensitive(self):
        from FlowScroll.core.rules import _match_keyword

        assert _match_keyword("chrome", "Google Chrome", use_regex=True) is True
        assert _match_keyword("^chrome$", "CHROME", use_regex=True) is True

    def test_regex_mode_alternation(self):
        from FlowScroll.core.rules import _match_keyword

        assert _match_keyword("chrome|firefox", "firefox", use_regex=True) is True
        assert _match_keyword("chrome|firefox", "chrome", use_regex=True) is True
        assert _match_keyword("chrome|firefox", "safari", use_regex=True) is False

    def test_regex_mode_character_class(self):
        from FlowScroll.core.rules import _match_keyword

        assert _match_keyword(r"code\d+", "code123", use_regex=True) is True
        assert _match_keyword(r"code\d+", "code-insiders", use_regex=True) is False

    def test_regex_mode_dot_star(self):
        from FlowScroll.core.rules import _match_keyword

        assert _match_keyword(r"note.*\.exe", "notepad.exe", use_regex=True) is True
        assert _match_keyword(r"note.*\.exe", "notepad", use_regex=True) is False

    def test_invalid_regex_returns_false(self):
        from FlowScroll.core.rules import _match_keyword

        # 未闭合的括号
        assert _match_keyword("[invalid", "test", use_regex=True) is False
        # 量词无前置
        assert _match_keyword("*invalid", "test", use_regex=True) is False
        # 未闭合的命名组
        assert _match_keyword("(?P<name", "test", use_regex=True) is False

    def test_invalid_regex_does_not_affect_other_keywords(self):
        """无效正则只跳过自身，不影响同组其他规则。"""
        from FlowScroll.core.rules import _match_keyword

        results = [
            _match_keyword("[bad", "anything", use_regex=True),
            _match_keyword("^chrome$", "chrome", use_regex=True),
            _match_keyword("*also_bad", "anything", use_regex=True),
            _match_keyword("firefox", "firefox", use_regex=True),
        ]
        assert results == [False, True, False, True]

    def test_empty_keyword(self):
        from FlowScroll.core.rules import _match_keyword

        # 空字符串在模糊模式下匹配任何目标
        assert _match_keyword("", "chrome", use_regex=False) is True
        # 空正则在 re.search 中匹配任何字符串
        assert _match_keyword("", "chrome", use_regex=True) is True


class TestRegexBlacklist:
    """测试正则模式下的黑名单过滤。"""

    def test_regex_blacklist_blocks_matching_process(self):
        from FlowScroll.core.config import cfg, runtime
        from FlowScroll.core.rules import is_current_app_allowed

        cfg.filter_mode = 1
        cfg.filter_blacklist = [r"^chrome(\.exe)?$", r"firefox.*"]
        cfg.filter_whitelist = []
        cfg.filter_use_regex = True
        cfg.disable_fullscreen = False
        runtime.is_fullscreen = False
        runtime.process_name_status = "available"

        runtime.current_process_name = "chrome"
        assert is_current_app_allowed() is False

        runtime.current_process_name = "chrome.exe"
        assert is_current_app_allowed() is False

        runtime.current_process_name = "firefox-nightly"
        assert is_current_app_allowed() is False

        runtime.current_process_name = "msedge"
        assert is_current_app_allowed() is True

    def test_regex_blacklist_with_character_class(self):
        from FlowScroll.core.config import cfg, runtime
        from FlowScroll.core.rules import is_current_app_allowed

        cfg.filter_mode = 1
        cfg.filter_blacklist = [r"player\d+"]
        cfg.filter_whitelist = []
        cfg.filter_use_regex = True
        cfg.disable_fullscreen = False
        runtime.is_fullscreen = False
        runtime.process_name_status = "available"

        runtime.current_process_name = "potplayer64"
        assert is_current_app_allowed() is False

        runtime.current_process_name = "potplayer"
        assert is_current_app_allowed() is True


class TestRegexWhitelist:
    """测试正则模式下的白名单过滤。"""

    def test_regex_whitelist_allows_only_matching(self):
        from FlowScroll.core.config import cfg, runtime
        from FlowScroll.core.rules import is_current_app_allowed

        cfg.filter_mode = 2
        cfg.filter_blacklist = []
        cfg.filter_whitelist = [r"^chrome$", r"^code$", r"notepad\+\+"]
        cfg.filter_use_regex = True
        cfg.disable_fullscreen = False
        runtime.is_fullscreen = False
        runtime.process_name_status = "available"

        runtime.current_process_name = "chrome"
        assert is_current_app_allowed() is True

        runtime.current_process_name = "code"
        assert is_current_app_allowed() is True

        runtime.current_process_name = "notepad++"
        assert is_current_app_allowed() is True

        runtime.current_process_name = "firefox"
        assert is_current_app_allowed() is False

    def test_regex_whitelist_alternation(self):
        from FlowScroll.core.config import cfg, runtime
        from FlowScroll.core.rules import is_current_app_allowed

        cfg.filter_mode = 2
        cfg.filter_blacklist = []
        cfg.filter_whitelist = [r"(chrome|firefox|edge)"]
        cfg.filter_use_regex = True
        cfg.disable_fullscreen = False
        runtime.is_fullscreen = False
        runtime.process_name_status = "available"

        runtime.current_process_name = "firefox"
        assert is_current_app_allowed() is True

        runtime.current_process_name = "msedge"
        assert is_current_app_allowed() is True

        runtime.current_process_name = "safari"
        assert is_current_app_allowed() is False


class TestRegexFallbackBehavior:
    """测试异常与边界场景。"""

    def test_invalid_regex_in_blacklist_is_skipped(self):
        from FlowScroll.core.config import cfg, runtime
        from FlowScroll.core.rules import is_current_app_allowed

        cfg.filter_mode = 1
        cfg.filter_blacklist = ["[invalid", "chrome"]
        cfg.filter_whitelist = []
        cfg.filter_use_regex = True
        cfg.disable_fullscreen = False
        runtime.is_fullscreen = False
        runtime.process_name_status = "available"

        # 无效规则被跳过，chrome 仍然可以被正常匹配阻止
        runtime.current_process_name = "chrome"
        assert is_current_app_allowed() is False

    def test_all_invalid_regex_in_blacklist_blocks_nothing(self):
        from FlowScroll.core.config import cfg, runtime
        from FlowScroll.core.rules import is_current_app_allowed

        cfg.filter_mode = 1
        cfg.filter_blacklist = ["[invalid", "*also_bad"]
        cfg.filter_whitelist = []
        cfg.filter_use_regex = True
        cfg.disable_fullscreen = False
        runtime.is_fullscreen = False
        runtime.process_name_status = "available"

        runtime.current_process_name = "chrome"
        assert is_current_app_allowed() is True

    def test_all_invalid_regex_in_whitelist_blocks_everything(self):
        from FlowScroll.core.config import cfg, runtime
        from FlowScroll.core.rules import is_current_app_allowed

        cfg.filter_mode = 2
        cfg.filter_blacklist = []
        cfg.filter_whitelist = ["[invalid", "*also_bad"]
        cfg.filter_use_regex = True
        cfg.disable_fullscreen = False
        runtime.is_fullscreen = False
        runtime.process_name_status = "available"

        runtime.current_process_name = "chrome"
        assert is_current_app_allowed() is False

    def test_fuzzy_mode_still_works_when_regex_off(self):
        """开启过正则后关闭，模糊匹配应完全恢复正常。"""
        from FlowScroll.core.config import cfg, runtime
        from FlowScroll.core.rules import is_current_app_allowed

        cfg.filter_mode = 1
        cfg.filter_blacklist = ["chrome"]
        cfg.filter_whitelist = []
        cfg.filter_use_regex = False
        cfg.disable_fullscreen = False
        runtime.is_fullscreen = False
        runtime.process_name_status = "available"

        runtime.current_process_name = "google chrome"
        assert is_current_app_allowed() is False

        runtime.current_process_name = "msedge"
        assert is_current_app_allowed() is True

        runtime.current_process_name = "firefox"
        assert is_current_app_allowed() is True

    def test_regex_with_window_name_fallback(self):
        """进程名不可用时回退到窗口标题，正则同样生效。"""
        from FlowScroll.core.config import cfg, runtime
        from FlowScroll.core.rules import is_current_app_allowed

        cfg.filter_mode = 1
        cfg.filter_blacklist = [r".*Chrome.*"]
        cfg.filter_whitelist = []
        cfg.filter_use_regex = True
        cfg.disable_fullscreen = False
        runtime.is_fullscreen = False
        runtime.process_name_status = "unavailable"
        runtime.current_process_name = ""
        runtime.current_window_name = "Google Chrome - New Tab"

        assert is_current_app_allowed() is False

    def test_global_mode_ignores_regex_setting(self):
        from FlowScroll.core.config import cfg, runtime
        from FlowScroll.core.rules import is_current_app_allowed

        cfg.filter_mode = 0
        cfg.filter_use_regex = True
        cfg.disable_fullscreen = False
        runtime.is_fullscreen = False

        assert is_current_app_allowed() is True


class TestRegexCompilationCache:
    def test_compiles_each_regex_pattern_only_once(self, monkeypatch):
        import FlowScroll.core.rules as rules

        original_compile = re.compile
        compile_calls = []

        def tracking_compile(pattern, flags=0):
            compile_calls.append((pattern, flags))
            return original_compile(pattern, flags)

        rules._compile_regex.cache_clear()
        monkeypatch.setattr(rules.re, "compile", tracking_compile)

        assert rules._match_keyword(r"^chrome$", "chrome", use_regex=True) is True
        assert rules._match_keyword(r"^chrome$", "chrome.exe", use_regex=True) is False
        assert compile_calls == [(r"^chrome$", re.IGNORECASE)]

    def test_invalid_regex_is_cached_after_first_failure(self, monkeypatch):
        import FlowScroll.core.rules as rules

        original_compile = re.compile
        compile_calls = []

        def tracking_compile(pattern, flags=0):
            compile_calls.append((pattern, flags))
            return original_compile(pattern, flags)

        rules._compile_regex.cache_clear()
        monkeypatch.setattr(rules.re, "compile", tracking_compile)

        assert rules._match_keyword("[invalid", "chrome", use_regex=True) is False
        assert rules._match_keyword("[invalid", "firefox", use_regex=True) is False
        assert compile_calls == [("[invalid", re.IGNORECASE)]


class TestAppFilterDialogRegexValidation:
    def test_invalid_regex_blocks_save_and_shows_warning(self, monkeypatch):
        qtwidgets = pytest.importorskip("PySide6.QtWidgets", exc_type=ImportError)
        QApplication = qtwidgets.QApplication
        app = QApplication.instance() or QApplication([])
        assert app is not None

        from FlowScroll.core.config import cfg
        from FlowScroll.ui.dialogs import AppFilterDialog

        warnings = []

        def fake_warning(_parent, title, body):
            warnings.append((title, body))
            return qtwidgets.QMessageBox.Ok

        monkeypatch.setattr(qtwidgets.QMessageBox, "warning", fake_warning)

        cfg.filter_mode = 0
        cfg.filter_blacklist = ["existing-blacklist"]
        cfg.filter_whitelist = ["existing-whitelist"]
        cfg.filter_use_regex = False

        dialog = AppFilterDialog()
        dialog.radio_blacklist.setChecked(True)
        dialog.chk_use_regex.setChecked(True)
        dialog.text_edit_blacklist.setPlainText("[invalid\nchrome")
        dialog.text_edit_whitelist.setPlainText("")

        dialog.save_and_close()

        assert len(warnings) == 1
        assert "invalid" in warnings[0][0].lower() or "无效" in warnings[0][0]
        assert "[invalid" in warnings[0][1]
        assert cfg.filter_mode == 0
        assert cfg.filter_blacklist == ["existing-blacklist"]
        assert cfg.filter_whitelist == ["existing-whitelist"]
        assert cfg.filter_use_regex is False
        dialog.close()

    def test_valid_regex_saves_successfully(self):
        qtwidgets = pytest.importorskip("PySide6.QtWidgets", exc_type=ImportError)
        QApplication = qtwidgets.QApplication
        app = QApplication.instance() or QApplication([])
        assert app is not None

        from FlowScroll.core.config import cfg
        from FlowScroll.ui.dialogs import AppFilterDialog

        cfg.filter_mode = 0
        cfg.filter_blacklist = []
        cfg.filter_whitelist = []
        cfg.filter_use_regex = False

        dialog = AppFilterDialog()
        dialog.radio_blacklist.setChecked(True)
        dialog.chk_use_regex.setChecked(True)
        dialog.text_edit_blacklist.setPlainText(r"^chrome$")
        dialog.text_edit_whitelist.setPlainText(r"^code$")

        dialog.save_and_close()

        assert cfg.filter_mode == 1
        assert cfg.filter_blacklist == [r"^chrome$"]
        assert cfg.filter_whitelist == [r"^code$"]
        assert cfg.filter_use_regex is True
        dialog.close()


class TestRegexConfigPersistence:
    """测试 filter_use_regex 的配置序列化与反序列化。"""

    def test_default_is_false(self):
        from FlowScroll.core.config import GlobalConfig

        c = GlobalConfig()
        assert c.filter_use_regex is False

    def test_to_dict_includes_filter_use_regex(self):
        from FlowScroll.core.config import GlobalConfig

        c = GlobalConfig()
        c.filter_use_regex = True
        d = c.to_dict()
        assert "filter_use_regex" in d
        assert d["filter_use_regex"] is True

    def test_to_dict_includes_filter_use_regex(self):
        from FlowScroll.core.config import GlobalConfig

        c = GlobalConfig()
        c.filter_use_regex = True
        d = c.to_dict()
        assert "filter_use_regex" in d
        assert d["filter_use_regex"] is True

    def test_from_dict_restores_filter_use_regex(self):
        from FlowScroll.core.config import GlobalConfig

        c = GlobalConfig()
        c.from_dict({"filter_use_regex": True})
        assert c.filter_use_regex is True

    def test_from_dict_missing_key_defaults_to_false(self):
        from FlowScroll.core.config import GlobalConfig

        c = GlobalConfig()
        c.from_dict({"sensitivity": 3.0})
        assert c.filter_use_regex is False

    def test_roundtrip(self):
        from FlowScroll.core.config import GlobalConfig

        c1 = GlobalConfig()
        c1.filter_use_regex = True
        c1.filter_blacklist = [r"^chrome$"]
        c1.filter_mode = 1

        d = c1.to_dict()
        c2 = GlobalConfig()
        c2.from_dict(d)

        assert c2.filter_use_regex is True
        assert c2.filter_blacklist == [r"^chrome$"]
        assert c2.filter_mode == 1

    def test_builtin_presets_have_filter_use_regex(self):
        from FlowScroll.core.config import BUILTIN_PRESETS

        for name, preset in BUILTIN_PRESETS.items():
            assert "filter_use_regex" in preset, f"预设 '{name}' 缺少 filter_use_regex"
            assert preset["filter_use_regex"] is False
