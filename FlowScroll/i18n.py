import json
import locale
import os
import sys
from pathlib import Path

SUPPORTED_LANGUAGES = ("zh-CN", "en-US")
DEFAULT_LANGUAGE = "en-US"
AUTO_LANGUAGE = "auto"

_ALIASES = {
    "zh": "zh-CN",
    "zh_cn": "zh-CN",
    "zh-cn": "zh-CN",
    "zh_hans": "zh-CN",
    "zh-hans": "zh-CN",
    "en": "en-US",
    "en_us": "en-US",
    "en-us": "en-US",
}

_cache = {}


def _normalize_tag(tag: str) -> str:
    """将语言标签归一化为支持的标准格式（zh-CN / en-US），无法识别时返回空字符串。"""
    token = (tag or "").strip().lower().replace("-", "_")
    if not token:
        return ""
    if token in _ALIASES:
        return _ALIASES[token]
    if token.startswith("zh"):
        return "zh-CN"
    if token.startswith("en"):
        return "en-US"
    return ""


def normalize_language(value: str) -> str:
    """将用户配置的语言值归一化：auto / zh-CN / en-US，无效值回退为 auto。"""
    token = (value or "").strip()
    if not token or token.lower() == AUTO_LANGUAGE:
        return AUTO_LANGUAGE
    normalized = _normalize_tag(token)
    if normalized in SUPPORTED_LANGUAGES:
        return normalized
    return AUTO_LANGUAGE


def _get_windows_ui_language() -> str:
    """通过 Win32 API 检测 Windows 系统界面语言。"""
    if sys.platform != "win32":
        return ""

    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        lang_id = kernel32.GetUserDefaultUILanguage()
        tag = locale.windows_locale.get(lang_id, "")
        normalized = _normalize_tag(tag)
        if normalized in SUPPORTED_LANGUAGES:
            return normalized

        buffer = ctypes.create_unicode_buffer(85)
        if kernel32.GetUserDefaultLocaleName(buffer, len(buffer)):
            normalized = _normalize_tag(buffer.value)
            if normalized in SUPPORTED_LANGUAGES:
                return normalized
    except Exception:
        pass

    return ""


def _get_qt_system_language() -> str:
    """通过 QLocale 检测系统语言。"""
    try:
        from PySide6.QtCore import QLocale

        for tag in (QLocale.system().name(), QLocale.system().bcp47Name()):
            normalized = _normalize_tag(tag)
            if normalized in SUPPORTED_LANGUAGES:
                return normalized
    except Exception:
        pass

    return ""


def get_system_language() -> str:
    """按优先级检测系统语言：Win32 API → QLocale → locale 模块 → 环境变量，最终回退为 en-US。"""
    for detector in (_get_windows_ui_language, _get_qt_system_language):
        detected = detector()
        if detected:
            return detected

    candidates = []
    try:
        current_locale = locale.getlocale()[0]
        if current_locale:
            candidates.append(current_locale)
    except Exception:
        pass

    locale_messages = getattr(locale, "LC_MESSAGES", None)
    if locale_messages is not None:
        try:
            message_locale = locale.getlocale(locale_messages)[0]
            if message_locale:
                candidates.append(message_locale)
        except Exception:
            pass

    for env_name in ("LC_ALL", "LC_MESSAGES", "LANG"):
        raw = os.environ.get(env_name, "").strip()
        if raw:
            candidates.append(raw.split(".", 1)[0])

    for item in candidates:
        normalized = _normalize_tag(item)
        if normalized in SUPPORTED_LANGUAGES:
            return normalized

    return DEFAULT_LANGUAGE


def get_active_language() -> str:
    """获取当前生效的语言：若配置为 auto 则返回系统语言，否则返回配置值。"""
    from FlowScroll.core.config import STATE_LOCK, cfg

    with STATE_LOCK:
        config_language = normalize_language(getattr(cfg, "ui_language", AUTO_LANGUAGE))
    if config_language == AUTO_LANGUAGE:
        return get_system_language()
    return config_language


def set_ui_language(value: str) -> str:
    """设置 UI 语言并持久化到配置，返回归一化后的语言代码。"""
    from FlowScroll.core.config import STATE_LOCK, cfg

    normalized = normalize_language(value)
    with STATE_LOCK:
        cfg.ui_language = normalized
    return normalized


def _load_locale(lang: str) -> dict:
    """从 locales 目录加载指定语言的 JSON 翻译文件。"""
    locale_path = Path(__file__).resolve().parent / "locales" / f"{lang}.json"
    if not locale_path.exists():
        return {}
    try:
        return json.loads(locale_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _get_dict(lang: str) -> dict:
    """获取指定语言的翻译字典，带缓存。"""
    if lang not in _cache:
        _cache[lang] = _load_locale(lang)
    return _cache.get(lang, {})


def tr(key: str, **kwargs) -> str:
    """翻译指定 key 到当前语言，支持 kwargs 格式化参数，缺失时回退到英文再回退到 key 本身。"""
    active = get_active_language()
    active_dict = _get_dict(active)
    fallback_dict = _get_dict(DEFAULT_LANGUAGE)
    value = active_dict.get(key)
    if value is None:
        value = fallback_dict.get(key, key)
    if kwargs:
        try:
            return str(value).format(**kwargs)
        except Exception:
            return str(value)
    return str(value)
