from __future__ import annotations

import re
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


def is_hotkey_valid(value: str) -> bool:
    normalized = normalize_hotkey(value)
    if not normalized:
        return False
    try:
        normalized.encode("ascii")
    except UnicodeEncodeError:
        return False
    kb = get_keyboard()
    if kb is not None and hasattr(kb, "parse_hotkey"):
        try:
            kb.parse_hotkey(normalized)
            return True
        except Exception:
            return False
    return bool(re.match(r"^[a-z0-9+\-]+$", normalized))


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
