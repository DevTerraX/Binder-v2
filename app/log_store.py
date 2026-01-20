import json
from datetime import datetime, timezone
from typing import Any

from app.config import LOG_DIR, LOG_FILE


def append_event(event: dict[str, Any]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        **event,
    }
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def read_events(limit: int | None = None) -> list[dict[str, Any]]:
    if not LOG_FILE.exists():
        return []
    entries: list[dict[str, Any]] = []
    with LOG_FILE.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
            if limit is not None and len(entries) >= limit:
                break
    return entries
