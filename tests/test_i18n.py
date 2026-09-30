import json
from pathlib import Path
import sys

import pytest


@pytest.fixture
def clean_locale_env(monkeypatch):
    for env_name in ("LC_ALL", "LC_MESSAGES", "LANG"):
        monkeypatch.delenv(env_name, raising=False)


def test_locale_keysets_match():
    base = Path(__file__).resolve().parents[1] / "FlowScroll" / "locales"
    zh = json.loads((base / "zh-CN.json").read_text(encoding="utf-8"))
    en = json.loads((base / "en-US.json").read_text(encoding="utf-8"))

    zh_keys = set(zh.keys())
    en_keys = set(en.keys())
    assert zh_keys == en_keys, (
        f"locale key mismatch: only_zh={sorted(zh_keys - en_keys)} " f"only_en={sorted(en_keys - zh_keys)}"
    )


def test_language_normalization_and_fallback():
    from FlowScroll.i18n import normalize_language

    assert normalize_language("auto") == "auto"
    assert normalize_language("zh") == "zh-CN"
    assert normalize_language("zh-Hans") == "zh-CN"
    assert normalize_language("en") == "en-US"
    assert normalize_language("EN_us") == "en-US"
    assert normalize_language("unknown") == "auto"


def test_get_system_language_falls_back_to_env(monkeypatch, clean_locale_env):
    import FlowScroll.i18n as i18n

    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setattr(i18n, "_get_windows_ui_language", lambda: "")
    monkeypatch.setattr(i18n, "_get_qt_system_language", lambda: "")
    monkeypatch.setattr(i18n.locale, "getlocale", lambda *args, **kwargs: (None, None))
    monkeypatch.setenv("LANG", "zh_CN.UTF-8")

    assert i18n.get_system_language() == "zh-CN"


@pytest.mark.parametrize(
    ("environment", "expected"),
    [
        ({"LANG": "zh_CN.UTF-8"}, "zh-CN"),
        ({"LANG": "en_US.UTF-8"}, "en-US"),
        ({"LANG": "de_DE.UTF-8"}, "en-US"),
        ({"LANG": "C"}, "en-US"),
        ({"LANG": "POSIX"}, "en-US"),
        ({"LC_ALL": "C", "LC_MESSAGES": "zh_CN.UTF-8", "LANG": "zh_CN.UTF-8"}, "en-US"),
        ({"LC_ALL": "fr_FR.UTF-8", "LC_MESSAGES": "zh_CN.UTF-8", "LANG": "zh_CN.UTF-8"}, "en-US"),
        ({"LC_ALL": "en_US.UTF-8", "LC_MESSAGES": "zh_CN.UTF-8", "LANG": "zh_CN.UTF-8"}, "en-US"),
        ({"LC_ALL": "zh_CN.UTF-8", "LC_MESSAGES": "en_US.UTF-8", "LANG": "en_US.UTF-8"}, "zh-CN"),
        ({"LC_MESSAGES": "en_US.UTF-8", "LANG": "zh_CN.UTF-8"}, "en-US"),
        ({"LC_MESSAGES": "de_DE.UTF-8", "LANG": "zh_CN.UTF-8"}, "en-US"),
        ({"LC_MESSAGES": "zh_CN.UTF-8", "LANG": "en_US.UTF-8"}, "zh-CN"),
        ({"LC_ALL": " ", "LC_MESSAGES": "", "LANG": "zh_CN.UTF-8"}, "zh-CN"),
    ],
)
def test_linux_language_uses_first_nonempty_locale(environment, expected, monkeypatch, clean_locale_env):
    import FlowScroll.i18n as i18n

    monkeypatch.setattr(sys, "platform", "linux")
    for env_name, value in environment.items():
        monkeypatch.setenv(env_name, value)

    def unexpected_fallback(*args, **kwargs):
        pytest.fail("Explicit Linux message locale must take precedence over platform detection")

    monkeypatch.setattr(i18n, "_get_windows_ui_language", unexpected_fallback)
    monkeypatch.setattr(i18n, "_get_qt_system_language", unexpected_fallback)
    monkeypatch.setattr(i18n.locale, "getlocale", unexpected_fallback)

    assert i18n.get_system_language() == expected


@pytest.mark.parametrize(
    ("qt_language", "python_locale", "expected"),
    [
        ("zh-CN", None, "zh-CN"),
        ("en-US", "zh_CN", "en-US"),
        ("", "zh_CN", "zh-CN"),
        ("", "de_DE", "en-US"),
        ("", None, "en-US"),
    ],
)
def test_linux_language_without_environment_keeps_platform_fallback(
    qt_language, python_locale, expected, monkeypatch, clean_locale_env
):
    import FlowScroll.i18n as i18n

    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(i18n, "_get_windows_ui_language", lambda: "")
    monkeypatch.setattr(i18n, "_get_qt_system_language", lambda: qt_language)
    monkeypatch.setattr(i18n.locale, "getlocale", lambda *args, **kwargs: (python_locale, None))

    assert i18n.get_system_language() == expected


@pytest.mark.parametrize(
    ("configured", "environment_locale", "expected"),
    [
        ("auto", "zh_CN.UTF-8", "zh-CN"),
        ("auto", "de_DE.UTF-8", "en-US"),
        ("zh-CN", "en_US.UTF-8", "zh-CN"),
        ("en-US", "zh_CN.UTF-8", "en-US"),
    ],
)
def test_active_language_preserves_explicit_choice(
    configured, environment_locale, expected, monkeypatch, clean_locale_env
):
    import FlowScroll.i18n as i18n
    from FlowScroll.core.config import cfg

    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("LC_ALL", environment_locale)
    monkeypatch.setattr(cfg, "ui_language", configured)

    assert i18n.get_active_language() == expected


def test_get_system_language_prefers_windows_ui_language(monkeypatch, clean_locale_env):
    import FlowScroll.i18n as i18n

    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(i18n, "_get_qt_system_language", lambda: "")
    monkeypatch.setattr(i18n.locale, "windows_locale", {2052: "zh_CN"})

    class DummyKernel32:
        @staticmethod
        def GetUserDefaultUILanguage():
            return 2052

        @staticmethod
        def GetUserDefaultLocaleName(buffer, size):
            buffer.value = "en-US"
            return 1

    class DummyCtypes:
        windll = type("Windll", (), {"kernel32": DummyKernel32()})()

        @staticmethod
        def create_unicode_buffer(size):
            return type("Buf", (), {"value": ""})()

    monkeypatch.setitem(sys.modules, "ctypes", DummyCtypes)
    monkeypatch.setattr(i18n.locale, "getlocale", lambda *args, **kwargs: ("en_US", None))
    monkeypatch.setenv("LC_ALL", "en_US.UTF-8")
    monkeypatch.setenv("LC_MESSAGES", "en_US.UTF-8")
    monkeypatch.setenv("LANG", "en_US.UTF-8")

    assert i18n.get_system_language() == "zh-CN"
