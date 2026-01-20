import sys
from datetime import datetime
from typing import Any

try:
    import keyboard as _keyboard  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    _keyboard = None


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
        self._variables: dict[str, str] = {}
        self._active_profile: dict[str, Any] = {}
        self.available = sys.platform == "win32" and _keyboard is not None

    def start(self) -> None:
        if not self.available or self._hook is not None:
            return
        self._hook = _keyboard.hook(self._on_event)

    def stop(self) -> None:
        if self._hook is None or not self.available:
            return
        _keyboard.unhook(self._hook)
        self._hook = None

    def update_config(
        self,
        profile: dict[str, Any],
        settings: dict[str, Any],
        binds: list[dict[str, Any]],
        variables: dict[str, Any],
    ) -> None:
        self._active_profile = profile
        self._enabled = bool(settings.get("binder_enabled", True))
        self._auto_layout = bool(settings.get("auto_layout", True))
        self._allow_no_prefix = bool(settings.get("allow_no_prefix", False))
        self._prefixes = settings.get("trigger_prefixes", ["."]) or ["."]
        self._commit_keys = set(settings.get("commit_keys", ["space"]))
        self._binds = binds
        self._variables = {
            "discord_me": str(variables.get("discord_me", "")),
            "discord_zga": str(variables.get("discord_zga", "")),
            "discord_ga": str(variables.get("discord_ga", "")),
            "me_name": str(variables.get("me_name", "")),
            "gender": str(variables.get("gender", "male")),
        }

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
        if bind_type == "Multi":
            lines = [line for line in content.splitlines() if line.strip()]
            for index, line in enumerate(lines):
                _keyboard.write(apply_variables(line, self._variables))
                if index < len(lines) - 1:
                    _keyboard.send("enter")
        else:
            _keyboard.write(apply_variables(content, self._variables))

    def _erase_token(self, count: int) -> None:
        for _ in range(max(0, count)):
            _keyboard.send("backspace")

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
