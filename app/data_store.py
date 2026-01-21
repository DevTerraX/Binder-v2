import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.config import DATA_DIR, PROFILES_FILE


class DataStore:
    def __init__(self, path: Path = PROFILES_FILE) -> None:
        self.path = path
        self.data = self._load()

    def _default_data(self) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        profile_id = str(uuid4())
        return {
            "active_profile_id": profile_id,
            "profiles": [
                {
                    "id": profile_id,
                    "name": "default",
                    "created_at": now,
                    "updated_at": now,
                    "settings": {
                        "trigger_prefixes": ["."],
                        "commit_keys": ["space"],
                        "binder_enabled": True,
                        "allow_no_prefix": False,
                        "auto_layout": True,
                        "hotkeys": {
                            "toggle": "Ctrl+Alt+B",
                            "open": "Ctrl+Alt+M",
                            "profile_switch": "",
                        },
                        "apps_filter": {
                            "only": "",
                            "exclude": "",
                        },
                    },
                    "variables": {
                        "gender": "male",
                        "discord_me": "me#9999",
                        "discord_zga": "zga#5678",
                        "discord_ga": "admin#1234",
                        "me_name": "AdminName",
                    },
                    "hotkeys": [],
                    "binds": [
                        {
                            "id": str(uuid4()),
                            "title": "Приветствие",
                            "category": "Ответы",
                            "trigger": "ку",
                            "type": "Text",
                            "content": "Привет, меня зовут {me_name}",
                        },
                        {
                            "id": str(uuid4()),
                            "title": "AJail",
                            "category": "Наказания",
                            "trigger": "ajail",
                            "type": "Command",
                            "content": "/ajail {id} {time}",
                        },
                        {
                            "id": str(uuid4()),
                            "title": "Телепорт",
                            "category": "Телепорты",
                            "trigger": "tp",
                            "type": "Command",
                            "content": "/tp {id}",
                        },
                    ],
                }
            ],
        }

    def _load(self) -> dict:
        if not self.path.exists():
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            data = self._default_data()
            self._save(data)
            return data
        with self.path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _save(self, data: dict | None = None) -> None:
        payload = data or self.data
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)

    def get_active_profile(self) -> dict:
        profile_id = self.data.get("active_profile_id")
        for profile in self.data.get("profiles", []):
            if profile["id"] == profile_id:
                return profile
        return self.data.get("profiles", [self._default_data()["profiles"][0]])[0]

    def list_profiles(self) -> list[dict]:
        return deepcopy(self.data.get("profiles", []))

    def list_binds(self, profile_id: str | None = None) -> list[dict]:
        profile = self.get_profile(profile_id)
        return deepcopy(profile.get("binds", []))

    def get_profile(self, profile_id: str | None = None) -> dict:
        if profile_id is None:
            return self.get_active_profile()
        for profile in self.data.get("profiles", []):
            if profile["id"] == profile_id:
                return profile
        return self.get_active_profile()

    def set_active_profile(self, profile_id: str) -> None:
        self.data["active_profile_id"] = profile_id
        self._save()

    def add_profile(self, name: str) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        profile_id = str(uuid4())
        template = self._default_data()["profiles"][0]
        profile = deepcopy(template)
        profile["id"] = profile_id
        profile["name"] = name
        profile["binds"] = []
        profile["created_at"] = now
        profile["updated_at"] = now
        self.data.setdefault("profiles", []).append(profile)
        self._save()
        return deepcopy(profile)

    def rename_profile(self, profile_id: str, new_name: str) -> bool:
        for profile in self.data.get("profiles", []):
            if profile["id"] == profile_id:
                profile["name"] = new_name
                profile["updated_at"] = datetime.now(timezone.utc).isoformat()
                self._save()
                return True
        return False

    def delete_profile(self, profile_id: str) -> bool:
        profiles = self.data.get("profiles", [])
        for idx, profile in enumerate(profiles):
            if profile["id"] == profile_id:
                profiles.pop(idx)
                if self.data.get("active_profile_id") == profile_id:
                    if profiles:
                        self.data["active_profile_id"] = profiles[0]["id"]
                    else:
                        self.data = self._default_data()
                self._save()
                return True
        return False

    def update_settings(self, profile_id: str, settings: dict) -> None:
        profile = self.get_profile(profile_id)
        profile["settings"] = deepcopy(settings)
        profile["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._save()

    def update_variables(self, profile_id: str, variables: dict) -> None:
        profile = self.get_profile(profile_id)
        profile["variables"] = deepcopy(variables)
        profile["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._save()

    def export_profile(self, profile_id: str) -> dict:
        return deepcopy(self.get_profile(profile_id))

    def import_profile(self, profile_data: dict, name_override: str | None = None) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        profile = deepcopy(profile_data)
        profile["id"] = str(uuid4())
        profile["name"] = name_override or profile.get("name", "imported")
        profile["created_at"] = now
        profile["updated_at"] = now
        profile["binds"] = [
            {**bind, "id": str(uuid4())} for bind in profile.get("binds", [])
        ]
        profile["hotkeys"] = [
            {**hotkey, "id": str(uuid4())} for hotkey in profile.get("hotkeys", [])
        ]
        self.data.setdefault("profiles", []).append(profile)
        self._save()
        return deepcopy(profile)

    def get_bind(self, bind_id: str, profile_id: str | None = None) -> dict | None:
        profile = self.get_profile(profile_id)
        for bind in profile.get("binds", []):
            if bind["id"] == bind_id:
                return deepcopy(bind)
        return None

    def add_bind(self, bind: dict, profile_id: str | None = None) -> dict:
        profile = self.get_profile(profile_id)
        new_bind = deepcopy(bind)
        new_bind["id"] = str(uuid4())
        profile.setdefault("binds", []).append(new_bind)
        profile["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._save()
        return deepcopy(new_bind)

    def update_bind(self, bind_id: str, bind: dict, profile_id: str | None = None) -> dict | None:
        profile = self.get_profile(profile_id)
        for idx, item in enumerate(profile.get("binds", [])):
            if item["id"] == bind_id:
                updated = deepcopy(bind)
                updated["id"] = bind_id
                profile["binds"][idx] = updated
                profile["updated_at"] = datetime.now(timezone.utc).isoformat()
                self._save()
                return deepcopy(updated)
        return None

    def delete_bind(self, bind_id: str, profile_id: str | None = None) -> bool:
        profile = self.get_profile(profile_id)
        binds = profile.get("binds", [])
        for idx, item in enumerate(binds):
            if item["id"] == bind_id:
                binds.pop(idx)
                profile["updated_at"] = datetime.now(timezone.utc).isoformat()
                self._save()
                return True
        return False

    def trigger_set(self, profile_id: str | None = None, exclude_id: str | None = None) -> set[str]:
        profile = self.get_profile(profile_id)
        triggers = set()
        for item in profile.get("binds", []):
            if exclude_id and item["id"] == exclude_id:
                continue
            triggers.add(item.get("trigger", ""))
        return triggers

    def list_hotkeys(self, profile_id: str | None = None) -> list[dict]:
        profile = self.get_profile(profile_id)
        return deepcopy(profile.get("hotkeys", []))

    def get_hotkey(self, hotkey_id: str, profile_id: str | None = None) -> dict | None:
        profile = self.get_profile(profile_id)
        for hotkey in profile.get("hotkeys", []):
            if hotkey.get("id") == hotkey_id:
                return deepcopy(hotkey)
        return None

    def add_hotkey(self, hotkey: dict, profile_id: str | None = None) -> dict:
        profile = self.get_profile(profile_id)
        new_hotkey = deepcopy(hotkey)
        new_hotkey["id"] = str(uuid4())
        profile.setdefault("hotkeys", []).append(new_hotkey)
        profile["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._save()
        return deepcopy(new_hotkey)

    def update_hotkey(self, hotkey_id: str, hotkey: dict, profile_id: str | None = None) -> dict | None:
        profile = self.get_profile(profile_id)
        for idx, item in enumerate(profile.get("hotkeys", [])):
            if item.get("id") == hotkey_id:
                updated = deepcopy(hotkey)
                updated["id"] = hotkey_id
                profile["hotkeys"][idx] = updated
                profile["updated_at"] = datetime.now(timezone.utc).isoformat()
                self._save()
                return deepcopy(updated)
        return None

    def delete_hotkey(self, hotkey_id: str, profile_id: str | None = None) -> bool:
        profile = self.get_profile(profile_id)
        hotkeys = profile.get("hotkeys", [])
        for idx, item in enumerate(hotkeys):
            if item.get("id") == hotkey_id:
                hotkeys.pop(idx)
                profile["updated_at"] = datetime.now(timezone.utc).isoformat()
                self._save()
                return True
        return False
