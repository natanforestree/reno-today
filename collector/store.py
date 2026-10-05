"""The repo's JSON files: docs/data/ for the page, state/ for the collector's
memory between runs (last refresh, digest date, last good events per source)."""

import json
import os
from datetime import datetime, timedelta

from model import utc

KEEP_LAST_GOOD = timedelta(hours=24)


def parse_time(value):
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None


class Store:
    def __init__(self, root):
        self.root = root

    def path(self, rel):
        return os.path.join(self.root, rel)

    def read(self, rel, default=None):
        try:
            with open(self.path(rel), encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, ValueError):
            return default

    def write(self, rel, obj):
        path = self.path(rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path + ".tmp", "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=1)
            f.write("\n")
        os.replace(path + ".tmp", path)

    def last_refresh(self):
        return parse_time((self.read("state/refresh.json") or {}).get("at"))

    def set_last_refresh(self, now):
        self.write("state/refresh.json", {"at": utc(now)})

    def digest_date(self):
        return (self.read("state/digest.json") or {}).get("date")

    def set_digest_date(self, day):
        self.write("state/digest.json", {"date": day})

    def remember(self, name, events, now):
        self.write(f"state/sources/{name}.json", {"at": utc(now), "events": events})

    def last_good(self, name, now):
        """(events, saved_at). Events are [] once they're older than KEEP_LAST_GOOD."""
        saved = self.read(f"state/sources/{name}.json") or {}
        at = parse_time(saved.get("at"))
        if at is None or now - at > KEEP_LAST_GOOD:
            return [], at
        return saved.get("events") or [], at
