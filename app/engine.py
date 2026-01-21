import os
import sys
import threading
import time
from ctypes import wintypes
import ctypes
from datetime import datetime
from typing import Any

from app.hotkeys import get_keyboard


class BinderEngine:
    def __init__(self, log_func) -> None:
        self._log = log_func
        self._hook = None
        self._buffer = ""
        self._enabled = True
        self._auto_layout = True
        self._allow_no_prefix = False
        self._prefixes = ["."]
        self._commit_keys = {"space"}
        self._binds: list[dict[str, Any]] = []
        self._hotkeys: list[dict[str, Any]] = []
        self._apps_only: list[str] = []
        self._apps_exclude: list[str] = []
        self._variables: dict[str, str] = {}
        self._active_profile: dict[str, Any] = {}
        self._hotkey_handles: list[int] = []
        self._macro_running = False
        self.available = sys.platform == "win32" and get_keyboard() is not None
        self._kb = get_keyboard()

    def start(self) -> None:
        if not self.available or self._hook is not None:
            return
        self._hook = self._kb.hook(self._on_event)
        self._refresh_hotkeys()

    def stop(self) -> None:
        if self._hook is None or not self.available:
            return
        self._kb.unhook(self._hook)
        self._hook = None
        self._clear_hotkeys()

    def update_config(
        self,
        profile: dict[str, Any],
        settings: dict[str, Any],
        binds: list[dict[str, Any]],
        variables: dict[str, Any],
        hotkeys: list[dict[str, Any]] | None = None,
    ) -> None:
        self._active_profile = profile
        self._enabled = bool(settings.get("binder_enabled", True))
        self._auto_layout = bool(settings.get("auto_layout", True))
        self._allow_no_prefix = bool(settings.get("allow_no_prefix", False))
        self._prefixes = settings.get("trigger_prefixes", ["."]) or ["."]
        self._commit_keys = set(settings.get("commit_keys", ["space"]))
        self._binds = binds
        self._hotkeys = hotkeys or []
        apps_filter = settings.get("apps_filter", {}) or {}
        self._apps_only = self._split_list(apps_filter.get("only", ""))
        self._apps_exclude = self._split_list(apps_filter.get("exclude", ""))
        self._variables = {
            "discord_me": str(variables.get("discord_me", "")),
            "discord_zga": str(variables.get("discord_zga", "")),
            "discord_ga": str(variables.get("discord_ga", "")),
            "me_name": str(variables.get("me_name", "")),
            "gender": str(variables.get("gender", "male")),
        }
        self._refresh_hotkeys()

    def _on_event(self, event) -> None:
        if event.event_type != "down":
            return
        name = event.name
        if name in {"shift", "ctrl", "alt", "alt gr", "cmd"}:
            return
        if name == "backspace":
            self._buffer = self._buffer[:-1]
            return
        if name in {"space", "enter", "tab"}:
            self._handle_commit(name)
            return
        if isinstance(name, str) and len(name) == 1:
            self._buffer += name

    def _handle_commit(self, key_name: str) -> None:
        if key_name not in self._commit_keys:
            self._debug("commit_key_disabled", {"key": key_name})
            return
        if not self._is_app_allowed():
            self._debug(
                "app_not_allowed",
                {
                    "app": self._active_app_name(),
                    "only": self._apps_only,
                    "exclude": self._apps_exclude,
                },
            )
            self._buffer = ""
            return
        token = self._buffer
        self._buffer = ""
        if not token:
            return
        if not self._enabled:
            self._debug("engine_disabled", {"token": token})
            return

        prefix, trigger = self._split_prefix(token)
        if prefix is None:
            self._debug("prefix_not_matched", {"token": token})
            return

        bind, method = self._find_bind(trigger, prefixed=bool(prefix))
        if not bind:
            self._debug(
                "trigger_not_found",
                {"trigger": trigger, "method": method, "token": token},
            )
            return

        delete_trigger = bind.get("options", {}).get("delete_trigger", True)
        try:
            if delete_trigger:
                self._erase_token(len(prefix + trigger) + 1)
            self._emit_bind(bind)
            self._debug(
                "trigger_matched",
                {
                    "trigger": trigger,
                    "method": method,
                    "bind_id": bind.get("id"),
                    "title": bind.get("title"),
                },
            )
        except Exception as exc:  # pragma: no cover - runtime guard
            self._debug("input_error", {"error": str(exc)})

    def _split_prefix(self, token: str) -> tuple[str | None, str]:
        for prefix in self._prefixes:
            if token.startswith(prefix):
                return prefix, token[len(prefix) :]
        if self._allow_no_prefix:
            return "", token
        return None, token

    def _find_bind(self, trigger: str, prefixed: bool) -> tuple[dict | None, str]:
        bind = self._find_bind_exact(trigger, prefixed)
        if bind:
            return bind, "exact"
        if self._auto_layout:
            converted = convert_layout(trigger)
            bind = self._find_bind_exact(converted, prefixed)
            if bind:
                return bind, "layout"
        return None, "none"

    def _find_bind_exact(self, trigger: str, prefixed: bool) -> dict | None:
        for bind in self._binds:
            bind_trigger = str(bind.get("trigger", ""))
            options = bind.get("options", {}) or {}
            only_prefix = options.get("only_prefix", True)
            case_sensitive = options.get("case_sensitive", False)
            if not prefixed and only_prefix:
                continue
            if case_sensitive:
                if bind_trigger == trigger:
                    return bind
            else:
                if bind_trigger.lower() == trigger.lower():
                    return bind
        return None

    def _emit_bind(self, bind: dict) -> None:
        bind_type = bind.get("type", "Text")
        content = bind.get("content", "") or ""
        cursor_back = bind.get("cursor_back", 0) or 0
        if bind_type == "Multi":
            lines = [line for line in content.splitlines() if line.strip()]
            for index, line in enumerate(lines):
                self._kb.write(apply_variables(line, self._variables))
                if index < len(lines) - 1:
                    self._kb.send("enter")
            self._move_cursor_back(cursor_back)
        else:
            self._kb.write(apply_variables(content, self._variables))
            self._move_cursor_back(cursor_back)

    def _erase_token(self, count: int) -> None:
        for _ in range(max(0, count)):
            self._kb.send("backspace")

    def _move_cursor_back(self, count: int) -> None:
        steps = max(0, int(count or 0))
        for _ in range(steps):
            self._kb.send("left")

    def _debug(self, reason: str, meta: dict[str, Any]) -> None:
        self._log(
            {
                "type": "engine_debug",
                "entity": "engine",
                "profile_id": self._active_profile.get("id"),
                "profile_name": self._active_profile.get("name"),
                "meta": {"reason": reason, **meta},
            }
        )

    def _split_list(self, value: str) -> list[str]:
        return [item.strip().lower() for item in value.split(",") if item.strip()]

    def _is_app_allowed(self) -> bool:
        if not self._apps_only and not self._apps_exclude:
            return True
        app = self._active_app_name()
        if not app:
            return True
        if self._apps_only and app not in self._apps_only:
            return False
        if self._apps_exclude and app in self._apps_exclude:
            return False
        return True

    def _active_app_name(self) -> str:
        if sys.platform != "win32":
            return ""
        return get_active_process_name()

    def _refresh_hotkeys(self) -> None:
        if not self.available or self._kb is None:
            return
        self._clear_hotkeys()
        for hotkey in self._hotkeys:
            combo = str(hotkey.get("hotkey", "")).strip()
            if not combo:
                continue
            handle = self._kb.add_hotkey(combo, lambda hk=hotkey: self._on_hotkey(hk))
            self._hotkey_handles.append(handle)

    def _clear_hotkeys(self) -> None:
        if not self.available or self._kb is None:
            return
        for handle in self._hotkey_handles:
            try:
                self._kb.remove_hotkey(handle)
            except Exception:  # pragma: no cover - safety
                continue
        self._hotkey_handles = []

    def _on_hotkey(self, hotkey: dict[str, Any]) -> None:
        if not self._enabled:
            return
        if self._macro_running:
            return
        steps = hotkey.get("steps", []) or []
        if not steps:
            return
        self._macro_running = True
        thread = threading.Thread(
            target=self._run_macro,
            args=(hotkey, steps),
            daemon=True,
        )
        thread.start()

    def run_macro_steps(self, steps: list[dict[str, Any]], title: str = "") -> None:
        if not self._enabled or self._macro_running or not steps:
            return
        hotkey = {"id": "manual", "hotkey": "", "title": title}
        self._macro_running = True
        thread = threading.Thread(
            target=self._run_macro,
            args=(hotkey, steps),
            daemon=True,
        )
        thread.start()

    def _run_macro(self, hotkey: dict[str, Any], steps: list[dict[str, Any]]) -> None:
        if not self.available or self._kb is None:
            self._macro_running = False
            return
        self._log(
            {
                "type": "macro_run",
                "entity": "hotkey",
                "profile_id": self._active_profile.get("id"),
                "profile_name": self._active_profile.get("name"),
                "meta": {
                    "hotkey_id": hotkey.get("id"),
                    "hotkey": hotkey.get("hotkey"),
                    "title": hotkey.get("title", ""),
                },
            }
        )
        try:
            for step in steps:
                step_type = step.get("type")
                value = str(step.get("value", ""))
                delay = float(step.get("delay", 0) or 0)

                if step_type == "press_key":
                    if value:
                        self._kb.send(value)
                elif step_type == "type_text":
                    self._kb.write(value)
                    if step.get("enter"):
                        self._kb.send("enter")
                elif step_type == "press_enter":
                    self._kb.send("enter")
                elif step_type == "delay":
                    pass

                if delay > 0:
                    time.sleep(delay)
        except Exception as exc:  # pragma: no cover - runtime guard
            self._log(
                {
                    "type": "macro_error",
                    "entity": "hotkey",
                    "profile_id": self._active_profile.get("id"),
                    "profile_name": self._active_profile.get("name"),
                    "meta": {
                        "hotkey_id": hotkey.get("id"),
                        "hotkey": hotkey.get("hotkey"),
                        "error": str(exc),
                    },
                }
            )
        finally:
            self._macro_running = False


def get_active_process_name() -> str:
    if sys.platform != "win32":
        return ""
    try:
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return ""
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

        access = 0x1000 | 0x0400  # PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_VM_READ
        process = kernel32.OpenProcess(access, False, pid.value)
        if not process:
            return ""
        try:
            buf = ctypes.create_unicode_buffer(260)
            size = wintypes.DWORD(len(buf))
            if kernel32.QueryFullProcessImageNameW(process, 0, buf, ctypes.byref(size)):
                return os.path.basename(buf.value).lower()
        finally:
            kernel32.CloseHandle(process)
    except Exception:
        return ""
    return ""


def apply_variables(text: str, variables: dict[str, str]) -> str:
    value = text
    replacements = {
        "{discord_me}": variables.get("discord_me", ""),
        "{discord_zga}": variables.get("discord_zga", ""),
        "{discord_ga}": variables.get("discord_ga", ""),
        "{me_name}": variables.get("me_name", ""),
    }
    for key, replacement in replacements.items():
        value = value.replace(key, replacement)

    now = datetime.now()
    value = value.replace("{date}", now.strftime("%d.%m.%Y"))
    value = value.replace("{time}", now.strftime("%H:%M"))

    while True:
        start = value.find("{g:")
        if start == -1:
            break
        end = value.find("}", start)
        if end == -1:
            break
        block = value[start + 3 : end]
        if "|" in block:
            male, female = block.split("|", 1)
            replacement = male if variables.get("gender") != "female" else female
            value = value[:start] + replacement + value[end + 1 :]
        else:
            break
    return value


def convert_layout(text: str) -> str:
    mapping = {
        "ф": "a",
        "и": "b",
        "с": "c",
        "в": "d",
        "у": "e",
        "а": "f",
        "п": "g",
        "р": "h",
        "ш": "i",
        "о": "j",
        "л": "k",
        "д": "l",
        "ь": "m",
        "т": "n",
        "щ": "o",
        "з": "p",
        "й": "q",
        "к": "r",
        "ы": "s",
        "е": "t",
        "г": "u",
        "м": "v",
        "ц": "w",
        "ч": "x",
        "н": "y",
        "я": "z",
    }
    reverse = {v: k for k, v in mapping.items()}
    converted = []
    for ch in text:
        lower = ch.lower()
        if lower in mapping:
            converted.append(mapping[lower])
        elif lower in reverse:
            converted.append(reverse[lower])
        else:
            converted.append(ch)
    return "".join(converted)
