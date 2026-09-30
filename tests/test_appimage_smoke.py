"""Ensure the artifact gate cannot pass on a crash, a dialog, or another app."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


spec = importlib.util.spec_from_file_location(
    "smoke_appimage", Path(__file__).resolve().parents[1] / ".github/scripts/smoke_appimage.py"
)
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)


def window(**overrides):
    return {
        "id": "42",
        "title": "FlowScroll v1.9.2",
        "width": 650,
        "height": 720,
        "pid": 123,
        "dialog": False,
        **overrides,
    }


def test_environment_isolates_config_and_preserves_locale_precedence(tmp_path, monkeypatch):
    monkeypatch.setenv("FLOWSCROLL_CONFIG_FILE", "/real/user/config.json")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("LANGUAGE", "zh_CN")
    monkeypatch.setenv("LC_MESSAGES", "zh_CN.UTF-8")
    env = smoke.isolated_environment(tmp_path, {"LC_ALL": "C", "LANG": "zh_CN.UTF-8"})
    assert "FLOWSCROLL_CONFIG_FILE" not in env
    assert "LC_MESSAGES" not in env
    assert "LANGUAGE" not in env
    assert env["LC_ALL"] == "C"
    assert env["LANG"] == "zh_CN.UTF-8"
    assert env["QT_QPA_PLATFORM"] == "xcb"
    assert Path(env["HOME"]).parent == tmp_path
    assert Path(env["XDG_CONFIG_HOME"]).parent == tmp_path


def test_main_window_accepts_appimage_child_process(monkeypatch):
    monkeypatch.setattr(smoke.os, "getpgid", lambda pid: 100, raising=False)
    assert smoke.main_window([window()], 100)["pid"] == 123


@pytest.mark.parametrize("candidate", [window(pid=0), window(width=100), window(title="FlowScroll Crash")])
def test_main_window_rejects_invalid_windows(candidate, monkeypatch):
    monkeypatch.setattr(smoke.os, "getpgid", lambda pid: 100, raising=False)
    assert smoke.main_window([candidate], 100) is None


def test_main_window_rejects_unrelated_process(monkeypatch):
    monkeypatch.setattr(smoke.os, "getpgid", lambda pid: 999, raising=False)
    assert smoke.main_window([window()], 100) is None


def test_main_window_rejects_modal_even_with_valid_main_window(monkeypatch):
    monkeypatch.setattr(smoke.os, "getpgid", lambda pid: 100, raising=False)
    with pytest.raises(RuntimeError, match="Unexpected visible dialog"):
        smoke.main_window([window(), window(title="Startup error", dialog=True)], 100)


def test_wait_rejects_early_exit():
    app = SimpleNamespace(poll=lambda: 1, returncode=1)
    with pytest.raises(RuntimeError, match="exited before validation"):
        smoke.wait_for_window(app, {}, timeout=1)


def test_wait_requires_continuous_visibility(monkeypatch):
    now = [0.0]
    monkeypatch.setattr(smoke.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(smoke.time, "sleep", lambda seconds: now.__setitem__(0, now[0] + seconds))
    monkeypatch.setattr(smoke.os, "getpgid", lambda pid: 100, raising=False)
    monkeypatch.setattr(smoke, "visible_windows", lambda env: [window()] if now[0] < 0.5 else [])
    app = SimpleNamespace(poll=lambda: None, pid=100)
    with pytest.raises(RuntimeError, match="Timed out"):
        smoke.wait_for_window(app, {}, timeout=2, stable_seconds=1)
