"""hotkeys.py 归一化与显示转换的回归测试。

覆盖 normalize_hotkey_part / normalize_hotkey_string / hotkey_to_display
三个公共函数，不涉及 Qt 事件解析（hotkey_from_key_event 需要 QEvent 实例，
在监听器层单独 mock，本文件不负责）。
"""

import pytest

from FlowScroll.core.hotkeys import (
    DISPLAY_ALIASES,
    LEGACY_ALIASES,
    MODIFIER_DISPLAY,
    MODIFIER_ORDER,
    hotkey_to_display,
    normalize_hotkey_part,
    normalize_hotkey_string,
)


# ---- normalize_hotkey_part ----

class TestNormalizeHotkeyPart:
    """normalize_hotkey_part 行为验证。"""

    @pytest.mark.parametrize(
        "raw, expected",
        [
            # 空与空白
            ("", ""),
            ("   ", ""),
            # 大小写归一
            ("CTRL", "ctrl"),
            ("aLt", "alt"),
            ("shift", "shift"),
            ("Meta", "meta"),
            # 修饰键别名
            ("control", "ctrl"),
            ("cmd", "meta"),
            ("command", "meta"),
            ("win", "meta"),
            ("super", "meta"),
            # 导航键别名
            ("pgup", "page_up"),
            ("pageup", "page_up"),
            ("page_up", "page_up"),
            ("pgdown", "page_down"),
            ("pagedown", "page_down"),
            ("ins", "insert"),
            ("del", "delete"),
            ("return", "enter"),
            ("escape", "esc"),
            # 锁定键别名
            ("capslock", "caps_lock"),
            ("caps_lock", "caps_lock"),
            ("numlock", "num_lock"),
            ("scrolllock", "scroll_lock"),
            # 鼠标键多种写法统一
            ("mouse_x1", "mouse_x1"),
            ("mouse_x2", "mouse_x2"),
            ("middle_mouse", "mouse_middle"),
            ("middle_button", "mouse_middle"),
            ("mouse_x_1", "mouse_x1"),
            ("mouse_x_2", "mouse_x2"),
            ("mouse_xbutton1", "mouse_x1"),
            ("mouse_xbutton2", "mouse_x2"),
            ("mouse_x_button_1", "mouse_x1"),
            ("mouse_x_button_2", "mouse_x2"),
            # 媒体键统一
            ("volume_down", "media_volume_down"),
            ("volume_up", "media_volume_up"),
            ("volume_mute", "media_volume_mute"),
            ("media_play", "media_play_pause"),
            ("media_pause", "media_play_pause"),
            ("media_toggle_play_pause", "media_play_pause"),
            ("toggle_media_play_pause", "media_play_pause"),
            ("play_pause_media", "media_play_pause"),
            # 单字符按键
            ("k", "k"),
            ("K", "k"),
            ("1", "1"),
        ],
    )
    def test_alias_and_case_variants(self, raw, expected):
        assert normalize_hotkey_part(raw) == expected

    def test_non_alphanumeric_characters_collapsed_to_underscore(self):
        """连续的非字母数字字符（含空格、下划线、减号）被折叠为单个 _ 并剥首尾。"""
        assert normalize_hotkey_part("foo--bar") == "foo_bar"
        assert normalize_hotkey_part("foo  bar") == "foo_bar"
        assert normalize_hotkey_part("__foo__") == "foo"

    def test_all_keys_in_legacy_aliases_map_to_canonical(self):
        """所有 LEGACY_ALIASES 中的键在归一化后应能再次稳定为同一值。"""
        for alias, canonical in LEGACY_ALIASES.items():
            # 输入 alias 应得到 canonical
            result = normalize_hotkey_part(alias)
            assert result == canonical, f"alias {alias!r} → {result!r} (expected {canonical!r})"
            # 再归一化一次应保持不变（幂等）
            assert normalize_hotkey_part(canonical) == canonical


# ---- normalize_hotkey_string ----

class TestNormalizeHotkeyString:
    """normalize_hotkey_string 行为验证。"""

    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("", ""),
            (None, ""),
            # 单个修饰
            ("ctrl", "ctrl"),
            # 修饰键排序
            ("shift+ctrl+k", "ctrl+shift+k"),
            ("meta+alt+shift+ctrl+k", "ctrl+alt+shift+meta+k"),
            # 普通字符按键
            ("ctrl+a", "ctrl+a"),
            ("ctrl+k", "ctrl+k"),
            # 去重
            ("ctrl+ctrl+k", "ctrl+k"),
            ("alt+shift+alt+a", "alt+shift+a"),
            # 空白容忍
            ("ctrl + alt + k", "ctrl+alt+k"),
            (" ctrl + alt +k ", "ctrl+alt+k"),
            # 多修饰 + 多普通键保留顺序
            ("ctrl+alt+k+m", "ctrl+alt+k+m"),
            # 别名展开与排序同时生效
            ("control + meta + k", "ctrl+meta+k"),
            ("cmd + ctrl + k", "ctrl+meta+k"),
            # 数字/符号按键
            ("ctrl+f4", "ctrl+f4"),
            # 多个普通键时，保留首次出现的插入顺序
            ("ctrl+k +v", "ctrl+k+v"),
        ],
    )
    def test_ordering_and_normalization(self, raw, expected):
        assert normalize_hotkey_string(raw) == expected

    def test_mouse_button_standalone(self):
        assert normalize_hotkey_string("mouse_middle") == "mouse_middle"
        assert normalize_hotkey_string("ctrl + mouse_x1") == "ctrl+mouse_x1"

    def test_unknown_keys_pass_through_lowercased(self):
        """未登记的键名保留小写形式，不崩溃。"""
        assert normalize_hotkey_string("Ctrl+Numpad5") == "ctrl+numpad5"
        assert normalize_hotkey_string("ctrl+f13") == "ctrl+f13"

    def test_modifier_always_precedes_non_modifier(self):
        """无论原始书写顺序，所有修饰键必须排在非修饰键之前。"""
        import itertools

        for perm in itertools.permutations(["ctrl", "alt", "k", "shift", "meta"]):
            joined = "+".join(perm)
            result = normalize_hotkey_string(joined)
            parts = result.split("+")
            # 检查前 4 个必须是 MODIFIER_ORDER 中的键（按固定顺序）
            assert parts[:4] == list(MODIFIER_ORDER), f"permutation {perm} → {parts}"
            assert parts[4:] == ["k"]


# ---- hotkey_to_display ----

class TestHotkeyToDisplay:
    """hotkey_to_display 输出验证。"""

    def test_empty_input(self):
        assert hotkey_to_display("") == ""
        assert hotkey_to_display(None) == ""

    def test_modifiers_show_with_standard_labels(self):
        assert hotkey_to_display("ctrl") == "Ctrl"
        # MODIFIER_ORDER = ("ctrl", "alt", "shift", "meta") 决定显示顺序
        assert hotkey_to_display("shift+alt") == "Alt+Shift"
        assert hotkey_to_display("ctrl+shift+alt+meta") == "Ctrl+Alt+Shift+Meta"

    def test_display_aliases_applied(self):
        for internal, display in DISPLAY_ALIASES.items():
            assert display in hotkey_to_display("ctrl+" + internal), (
                f"key {internal!r} should display as {display!r}"
            )

    def test_single_char_is_uppercased(self):
        assert hotkey_to_display("ctrl+a") == "Ctrl+A"
        assert hotkey_to_display("ctrl+k") == "Ctrl+K"
        assert hotkey_to_display("alt+1") == "Alt+1"

    def test_title_case_fallback_for_unregistered_keys(self):
        """未登记的键名下划线转空格，使用 Title Case。"""
        # mouse_middle 在 DISPLAY_ALIASES 中有定义（不是这条路径）
        # 这里测试一个真正未登记的键，例如 "custom_action"
        result = hotkey_to_display("ctrl+custom_action")
        # 期望：Ctrl + Custom Action（Title Case，下划线被替换为空格）
        assert result == "Ctrl+Custom Action"

    def test_complex_combination(self):
        assert hotkey_to_display("ctrl+alt+delete") == "Ctrl+Alt+Del"
        assert hotkey_to_display("shift+pgup") == "Shift+PgUp"
        assert hotkey_to_display("ctrl+caps_lock") == "Ctrl+Caps Lock"

    def test_round_trip_via_normalize_preserves_semantics(self):
        """display 字符串应该反映 normalized 的语义，即使用户输入混乱。"""
        ugly = "control + cmd + del + pgup"
        display = hotkey_to_display(ugly)
        assert display == "Ctrl+Meta+Del+PgUp"

    def test_modifier_order_in_display_is_fixed(self):
        """display 字符串中修饰键顺序必须固定为 Ctrl+Alt+Shift+Meta。"""
        result = hotkey_to_display("meta+shift+alt+ctrl+k")
        assert result == "Ctrl+Alt+Shift+Meta+K"
