import re

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence


MODIFIER_ORDER = ("ctrl", "alt", "shift", "meta")
MODIFIER_DISPLAY = {
    "ctrl": "Ctrl",
    "alt": "Alt",
    "shift": "Shift",
    "meta": "Meta",
}
LEGACY_ALIASES = {
    "control": "ctrl",
    "command": "meta",
    "cmd": "meta",
    "win": "meta",
    "super": "meta",
    "pgup": "page_up",
    "pageup": "page_up",
    "page_up": "page_up",
    "pgdown": "page_down",
    "pagedown": "page_down",
    "page_down": "page_down",
    "ins": "insert",
    "del": "delete",
    "return": "enter",
    "escape": "esc",
    "mouse_x1": "mouse_x1",
    "mouse_x2": "mouse_x2",
    "mouse_middle": "mouse_middle",
    "middle_mouse": "mouse_middle",
    "middle_button": "mouse_middle",
    "mouse_x_1": "mouse_x1",
    "mouse_x_2": "mouse_x2",
    "mouse_xbutton1": "mouse_x1",
    "mouse_xbutton2": "mouse_x2",
    "mouse_x_button_1": "mouse_x1",
    "mouse_x_button_2": "mouse_x2",
    "volume_down": "media_volume_down",
    "volume_up": "media_volume_up",
    "volume_mute": "media_volume_mute",
    "media_previous": "media_previous",
    "media_next": "media_next",
    "media_stop": "media_stop",
    "media_play": "media_play_pause",
    "media_pause": "media_play_pause",
    "media_toggle_play_pause": "media_play_pause",
    "toggle_media_play_pause": "media_play_pause",
    "play_pause_media": "media_play_pause",
}
DISPLAY_ALIASES = {
    "page_up": "PgUp",
    "page_down": "PgDown",
    "insert": "Ins",
    "delete": "Del",
    "esc": "Esc",
    "enter": "Enter",
    "mouse_x1": "Mouse X1",
    "mouse_x2": "Mouse X2",
    "mouse_middle": "Mouse Middle",
    "media_volume_down": "Volume Down",
    "media_volume_up": "Volume Up",
    "media_volume_mute": "Volume Mute",
    "media_previous": "Media Previous",
    "media_next": "Media Next",
    "media_stop": "Media Stop",
    "media_play_pause": "Toggle Media Play/Pause",
}
MODIFIER_KEYS = {
    Qt.Key.Key_Control,
    Qt.Key.Key_Shift,
    Qt.Key.Key_Alt,
    Qt.Key.Key_Meta,
}


def normalize_hotkey_part(value):
    token = value.strip().lower()
    if not token:
        return ""
    token = re.sub(r"[^a-z0-9]+", "_", token).strip("_")
    return LEGACY_ALIASES.get(token, token)


def normalize_hotkey_string(value):
    if not value:
        return ""
    normalized_parts = []
    for raw_part in value.split("+"):
        part = normalize_hotkey_part(raw_part)
        if part and part not in normalized_parts:
            normalized_parts.append(part)

    modifiers = [part for part in MODIFIER_ORDER if part in normalized_parts]
    others = [part for part in normalized_parts if part not in MODIFIER_ORDER]
    return "+".join(modifiers + others)


def hotkey_to_display(value):
    normalized = normalize_hotkey_string(value)
    if not normalized:
        return ""

    display_parts = []
    for part in normalized.split("+"):
        if part in MODIFIER_DISPLAY:
            display_parts.append(MODIFIER_DISPLAY[part])
        elif part in DISPLAY_ALIASES:
            display_parts.append(DISPLAY_ALIASES[part])
        elif len(part) == 1:
            display_parts.append(part.upper())
        else:
            display_parts.append(part.replace("_", " ").title())
    return "+".join(display_parts)


def hotkey_from_key_event(event):
    modifiers = []
    keyboard_modifiers = event.modifiers()
    if keyboard_modifiers & Qt.ControlModifier:
        modifiers.append("ctrl")
    if keyboard_modifiers & Qt.AltModifier:
        modifiers.append("alt")
    if keyboard_modifiers & Qt.ShiftModifier:
        modifiers.append("shift")
    if keyboard_modifiers & Qt.MetaModifier:
        modifiers.append("meta")

    if event.key() in MODIFIER_KEYS:
        return "+".join(modifiers)

    key_text = QKeySequence(event.key()).toString()
    if not key_text:
        key_text = event.text()

    main_key = normalize_hotkey_part(key_text)
    if not main_key:
        return "+".join(modifiers)

    return normalize_hotkey_string("+".join(modifiers + [main_key]))
