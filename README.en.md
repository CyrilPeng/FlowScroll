<div align="center">

# <img src="FlowScroll/resources/FlowScroll.svg" width="40" align="center" alt="Logo" /> FlowScroll

**Global infinite scrolling with your mouse middle button**

Bring browser-style auto-scroll to your whole desktop.

`English` | [中文](README.md)

[![License](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()
[![Release](https://img.shields.io/github/v/release/CyrilPeng/FlowScroll?color=success&label=Release)](https://github.com/CyrilPeng/FlowScroll/releases) ![Channel](https://img.shields.io/badge/Channel-dev-f59e0b) 

[Website](https://flowscroll.pages.dev/) | [Releases](https://github.com/CyrilPeng/FlowScroll/releases)

</div>

---

## Overview

FlowScroll extends browser middle-button auto-scroll to desktop apps.

It is designed for long pages, documents, code, timelines, and wide content where frequent wheel scrolling or dragging scrollbars is inefficient.

Typical use cases:

- Reading long web pages, docs, and PDFs
- Browsing code/log/config files
- Navigating wide sheets, canvases, and timelines
- Reducing repetitive wheel and scrollbar operations

---

## Screenshots

### Main UI

<div align="center">
  <img src="https://git-pictures.cyrilworkshop.dpdns.org/flowscroll/1.jpg" alt="Main UI" width="30%" style="margin-right: 2%;">
  <img src="https://git-pictures.cyrilworkshop.dpdns.org/flowscroll/2.jpg" alt="Settings UI" width="30%" style="margin-right: 2%;">
  <img src="https://git-pictures.cyrilworkshop.dpdns.org/flowscroll/3.jpg" alt="Work Mode" width="30%">
</div>

### Demo

<div align="center">
<img src="https://git-pictures.cyrilworkshop.dpdns.org/flowscroll/demo1.gif" alt="FlowScroll Demo 1" width="80%" style="border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
<br>
<br>
<img src="https://git-pictures.cyrilworkshop.dpdns.org/flowscroll/demo2.gif" alt="FlowScroll Demo 2" width="80%" style="border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
</div>

---

## Download and Install

Get the latest build from [Releases](https://github.com/CyrilPeng/FlowScroll/releases).

Official release builds are packaged with `Nuitka`. Compared with common packagers such as `PyInstaller`, this generally gives this project better startup/runtime efficiency and lower packaging overhead.

| Platform | File | Installation |
| :--- | :--- | :--- |
| **Windows** | `FlowScroll_Win_v*.exe` | Double-click to run |
| **macOS** | `FlowScroll_Mac_v*.dmg` | Drag into `Applications`; grant Accessibility permission |
| **Linux (Preview)** | `FlowScroll_Linux_x86_v*.AppImage` | `chmod +x` then run |

Platform status:

- **Windows**: fully supported (recommended)
- **macOS**: supported, requires Accessibility permission
- **Linux**: preview; works on X11/Xorg, not available on Wayland due to global-input restrictions

---

## Quick Start

FlowScroll supports two activation modes. Each mode has its own activation hotkey/button. If empty, middle mouse button is used by default.

### Click to toggle (default)

1. Press the activation key/button once.
2. Crosshair appears, indicating scrolling mode is active.
3. Move mouse away from center to scroll (farther means faster).
4. Press activation key/button again to exit.

### Hold to activate

1. Hold the activation key/button.
2. Crosshair appears and scrolling mode activates.
3. Keep holding while moving mouse to scroll.
4. Release to exit automatically.

### Delayed Activation

If you want to preserve the native behavior of a middle-button click, enable **Delayed activation** in Work Mode.

- A short middle-button click will not start FlowScroll immediately
- FlowScroll activates only after the button is held for the configured delay
- This helps avoid conflicts between native middle-click actions and FlowScroll activation

Typical cases include:

- Browser native middle-button features
- Middle-click to close a tab
- Other app-specific middle-click actions

`150~250ms` is usually a practical range for balancing responsiveness and conflict avoidance.

---

## Features

- Global scrolling interaction in common scrollable apps
- Direction indicator overlay and clear activation state
- Tunable motion curve, base speed, and dead zone
- Optional 360-degree scrolling for horizontal content
- Fullscreen disable and app filter rules (blacklist/whitelist)
- Optional WebDAV sync for presets/config
- Optional inertia scroll after release
- Independent X/Y reverse direction settings

---

## Configuration

### Built-in Presets

Includes 4 built-in presets for common scenarios:

- Web Reading
- Coding/Office
- Long Docs/Sheets (default)
- Gentle/Trackpad-like

You can save custom presets in the app. By default, the config is stored in an app data directory: Windows `%AppData%\FlowScroll\FlowScroll_config.json`, macOS `~/Library/Application Support/FlowScroll/FlowScroll_config.json`, Linux `~/.config/FlowScroll/FlowScroll_config.json`. You can also override the location with `FLOWSCROLL_CONFIG_FILE` or `FLOWSCROLL_CONFIG_DIR`.

### Core Parameters

- **Sensitivity curve**: controls acceleration growth
- **Speed factor**: global speed multiplier
- **Dead zone**: center area without scroll output
- **Horizontal mode**: allow X-axis scrolling
- **Inertia**: friction and trigger threshold

---

## Permissions

### macOS

FlowScroll needs Accessibility permission to listen to global input events.

### Windows

Usually no admin privilege is required.

### Linux

Global hooks are available on X11/Xorg. Wayland does not allow this class of global interception.

---

## Privacy

- Default mode is local-only
- WebDAV sync is opt-in
- Password is stored in system keychain when available
- Password is not included in preset export/sync payload

---

## Known Compatibility Notes

- macOS fullscreen detection has limitations in some apps
- Wayland is not supported for global input hooks
- Some special/UWP apps may have input hook limitations on Windows

---

## FAQ

### Will it conflict with browser middle-button auto-scroll?

No. FlowScroll targets global interaction outside browser-native behavior and supports app-level filtering.

### Blacklist vs whitelist?

- **Blacklist**: disable FlowScroll in matched apps
- **Whitelist**: enable FlowScroll only in matched apps

### How are app keywords matched?

Case-insensitive substring match against the foreground process name.
If the current environment cannot identify a process name, FlowScroll falls back to the foreground window title for that app only.

### Why does it sometimes look inactive?

Check activation mode/hotkey, app filter rules, fullscreen disable setting, and required permissions.

### Is WebDAV password uploaded?

No. Password is kept in local secure storage and excluded from sync payload.

---

## Build from Source

If you run directly from `main`, you may be using an in-progress development build rather than the latest stable release.

Stable release artifacts are packaged separately with `Nuitka`; running from source is mainly intended for development, debugging, and testing.

```bash
git clone https://github.com/CyrilPeng/FlowScroll.git
cd FlowScroll
uv sync
uv run python main.py
```

Run tests:

```bash
uv run python -m pytest tests/ -v
```

---

## Contributors

Thanks to everyone who has contributed pull requests, bug reports, discussion, and concrete improvements to FlowScroll.

This contributor graph updates automatically with the repository:

<div align="center">
  <a href="https://github.com/CyrilPeng/FlowScroll/graphs/contributors">
    <img src="https://contrib.rocks/image?repo=CyrilPeng/FlowScroll" alt="FlowScroll contributors" />
  </a>
</div>

If you want to help improve it too, issues and pull requests are welcome.

---

## Community Links

- [Linux.do](https://linux.do/): A general tech community focused on open source, productivity tools, development, and AI discussions.

---

## About The Code

FlowScroll is built with a pragmatic mindset: solve real user problems first, then keep improving the implementation over time.

In this project, the author's role is closer to product design and feature direction. Some parts of the implementation came from rapid iteration, exploratory validation, and AI-assisted generation, so the engineering structure and fine details may not always be ideal.

If you notice weaknesses in the implementation or see room for improvement, issues and pull requests are welcome.

- Feedback with context, reproduction steps, and actionable suggestions is especially useful
- Constructive discussion about interaction design, compatibility, and code quality is welcome
- Dismissive criticism without concrete substance does not help the project move forward

FlowScroll is, first of all, a small tool built for real usage scenarios.
It may not be perfect, but it will keep evolving.

---

## License

GPL-3.0. See [LICENSE](LICENSE).
