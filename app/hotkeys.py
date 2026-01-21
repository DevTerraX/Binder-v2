from __future__ import annotations

import sys
from typing import Iterable

try:
    import keyboard as _keyboard  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    _keyboard = None


DISPLAY_MAP = {
    "ctrl": "Ctrl",
    "alt": "Alt",
    "alt gr": "AltGr",
    "shift": "Shift",
    "cmd": "Cmd",
    "win": "Win",
    "windows": "Win",
    "caps lock": "CapsLock",
    "capslock": "CapsLock",
    "enter": "Enter",
    "space": "Space",
    "tab": "Tab",
    "esc": "Esc",
    "escape": "Esc",
}


def keyboard_available() -> bool:
    return sys.platform == "win32" and _keyboard is not None


def get_keyboard():
    return _keyboard


def normalize_hotkey(value: str) -> str:
    parts = [p.strip().lower() for p in value.split("+") if p.strip()]
    return "+".join(parts)


def format_hotkey(value: str) -> str:
    if not value:
        return ""
    parts = [p.strip().lower() for p in value.split("+") if p.strip()]
    formatted: list[str] = []
    for part in parts:
        formatted.append(DISPLAY_MAP.get(part, part.title()))
    return " + ".join(formatted)


def format_hotkey_parts(parts: Iterable[str]) -> str:
    return format_hotkey("+".join(parts))
