"""Launch the shipped AppImage on isolated X11 displays and capture its real UI.

Requires Linux, Xvfb, xdotool, xprop (x11-utils), and ImageMagick's import.
Screenshots are retained for language review; success requires a visible main
window owned by the launched application, continued liveness, and no dialogs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time


CASES = (
    ("english", {"LANG": "en_US.UTF-8", "LC_ALL": "en_US.UTF-8"}, "en-US"),
    ("chinese", {"LANG": "zh_CN.UTF-8", "LC_ALL": "zh_CN.UTF-8"}, "zh-CN"),
    ("unsupported-german", {"LANG": "de_DE.UTF-8", "LC_ALL": "de_DE.UTF-8"}, "en-US"),
    ("c-overrides-chinese", {"LANG": "zh_CN.UTF-8", "LC_ALL": "C"}, "en-US"),
)
MAIN_TITLE = re.compile(r"^FlowScroll v\d+\.")


def isolated_environment(root: Path, locale_env: dict[str, str]) -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("LC_", "QT_", "FLOWSCROLL_", "XDG_"))
        and key not in {"LANG", "LANGUAGE", "DISPLAY", "WAYLAND_DISPLAY", "PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV"}
    }
    for key, name in {
        "HOME": "home",
        "APPDATA": "appdata",
        "XDG_CONFIG_HOME": "config",
        "XDG_CACHE_HOME": "cache",
        "XDG_DATA_HOME": "data",
        "XDG_RUNTIME_DIR": "runtime",
        "TMPDIR": "tmp",
    }.items():
        directory = root / name
        directory.mkdir(mode=0o700)
        env[key] = str(directory)
    env.update(locale_env)
    env.update({"XDG_SESSION_TYPE": "x11", "QT_QPA_PLATFORM": "xcb", "QT_SCALE_FACTOR": "1"})
    return env


def command(args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess:
    # Keep X11 utility output parseable even for the Chinese application case.
    return subprocess.run(args, env={**env, "LC_ALL": "C"}, capture_output=True, text=True, timeout=5, check=False)


def visible_windows(env: dict[str, str]) -> list[dict]:
    found = command(["xdotool", "search", "--onlyvisible", "--name", "."], env)
    windows = []
    for window_id in found.stdout.split():
        title = command(["xdotool", "getwindowname", window_id], env)
        geometry = command(["xdotool", "getwindowgeometry", "--shell", window_id], env)
        owner = command(["xdotool", "getwindowpid", window_id], env)
        props = command(["xprop", "-id", window_id, "_NET_WM_WINDOW_TYPE", "_NET_WM_STATE", "WM_TRANSIENT_FOR"], env)
        if title.returncode or geometry.returncode:
            continue  # A window may disappear between the X11 queries.
        dimensions = dict(re.findall(r"^(WIDTH|HEIGHT)=(\d+)$", geometry.stdout, re.MULTILINE))
        windows.append(
            {
                "id": window_id,
                "title": title.stdout.strip(),
                "width": int(dimensions.get("WIDTH", 0)),
                "height": int(dimensions.get("HEIGHT", 0)),
                "pid": int(owner.stdout.strip()) if owner.stdout.strip().isdigit() else 0,
                "dialog": "_NET_WM_WINDOW_TYPE_DIALOG" in props.stdout
                or "_NET_WM_STATE_MODAL" in props.stdout
                or bool(re.search(r"WM_TRANSIENT_FOR\(WINDOW\).*# 0x[0-9a-f]*[1-9a-f]", props.stdout)),
            }
        )
    return windows


def main_window(windows: list[dict], app_pid: int) -> dict | None:
    dialogs = [window["title"] for window in windows if window["dialog"]]
    if dialogs:
        raise RuntimeError(f"Unexpected visible dialog(s): {dialogs}")
    for window in windows:
        if MAIN_TITLE.match(window["title"]) and window["width"] >= 420 and window["height"] >= 680:
            try:
                # AppImage may launch a child process; both belong to our new session.
                if window["pid"] > 0 and os.getpgid(window["pid"]) == app_pid:
                    return window
            except ProcessLookupError:
                pass
    return None


def wait_for_window(app: subprocess.Popen, env: dict[str, str], timeout: float, stable_seconds: float = 4) -> dict:
    deadline = time.monotonic() + timeout
    visible_since = None
    while time.monotonic() < deadline:
        if app.poll() is not None:
            raise RuntimeError(f"AppImage exited before validation (exit code {app.returncode})")
        window = main_window(visible_windows(env), app.pid)
        if window:
            if visible_since is None:
                visible_since = time.monotonic()
            if time.monotonic() - visible_since >= stable_seconds:
                return window
        else:
            visible_since = None
        time.sleep(0.25)
    raise RuntimeError("Timed out without a stable, visible FlowScroll main window")


def stop_process_group(process: subprocess.Popen | None) -> None:
    if process is None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        pass
    finally:
        # Also reap helpers left behind when their parent already exited.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=3)


def capture(env: dict[str, str], window_id: str, path: Path) -> None:
    result = command(["import", "-window", window_id, str(path)], env)
    if result.returncode or not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"Could not capture screenshot: {result.stderr.strip()}")


def run_case(appimage: Path, output: Path, case: tuple, timeout: float) -> dict:
    name, locale_env, expected_language = case
    case_output = output / name
    case_output.mkdir(parents=True, exist_ok=True)
    result = {"case": name, "locale": locale_env, "expected_language": expected_language, "passed": False}
    app = None
    xvfb = None
    with tempfile.TemporaryDirectory(prefix=f"flowscroll-smoke-{name}-") as temporary:
        root = Path(temporary)
        env = isolated_environment(root, locale_env)
        try:
            with (case_output / "xvfb.log").open("wb") as xlog, (root / "display").open("w+") as display:
                xvfb = subprocess.Popen(
                    [
                        "Xvfb",
                        "-displayfd",
                        str(display.fileno()),
                        "-screen",
                        "0",
                        "1600x1200x24",
                        "-nolisten",
                        "tcp",
                        "-ac",
                    ],
                    pass_fds=(display.fileno(),),
                    stdout=xlog,
                    stderr=subprocess.STDOUT,
                    env=env,
                    start_new_session=True,
                )
                deadline = time.monotonic() + 10
                while time.monotonic() < deadline:
                    if xvfb.poll() is not None:
                        raise RuntimeError("Xvfb exited before making a display available")
                    display.seek(0)
                    number = display.read().strip()
                    if number.isdigit():
                        env["DISPLAY"] = f":{number}"
                        break
                    time.sleep(0.1)
                else:
                    raise RuntimeError("Xvfb did not make a display available")
            with (case_output / "application.log").open("wb") as log:
                app = subprocess.Popen(
                    [str(appimage), "--appimage-extract-and-run"],
                    cwd=root,
                    env=env,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                window = wait_for_window(app, env, timeout)
                capture(env, window["id"], case_output / "main-window.png")
                # Do not turn a crash during capture, or a startup modal, into a pass.
                if app.poll() is not None or main_window(visible_windows(env), app.pid) is None:
                    raise RuntimeError("Application stopped displaying its main window during capture")
                result.update({"passed": True, "window": window})
        except (OSError, RuntimeError, subprocess.SubprocessError) as error:
            result["error"] = str(error)
            if "DISPLAY" in env:
                try:
                    capture(env, "root", case_output / "failure-screen.png")
                    result["windows"] = visible_windows(env)
                except (OSError, RuntimeError, subprocess.SubprocessError):
                    pass
        finally:
            stop_process_group(app)
            stop_process_group(xvfb)
            (case_output / "result.json").write_text(
                json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return result


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("appimage", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("appimage-smoke"))
    parser.add_argument("--startup-timeout", type=float, default=45)
    args = parser.parse_args(argv)
    if not sys.platform.startswith("linux"):
        parser.error("The AppImage smoke test requires Linux")
    for executable in ("Xvfb", "xdotool", "xprop", "import"):
        if shutil.which(executable) is None:
            parser.error(f"Required command not found: {executable}")
    appimage = args.appimage.resolve(strict=True)
    if not os.access(appimage, os.X_OK):
        parser.error(f"AppImage is not executable: {appimage}")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    def terminate(signum, _frame):
        raise SystemExit(128 + signum)  # Run the case's finally block on CI cancellation.

    signal.signal(signal.SIGTERM, terminate)
    results = [run_case(appimage, args.output_dir.resolve(), case, args.startup_timeout) for case in CASES]
    with appimage.open("rb") as binary:
        hasher = hashlib.sha256()
        for chunk in iter(lambda: binary.read(1024 * 1024), b""):
            hasher.update(chunk)
        digest = hasher.hexdigest()
    report = {"appimage": appimage.name, "sha256": digest, "cases": results}
    (args.output_dir / "summary.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return 0 if all(result["passed"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
