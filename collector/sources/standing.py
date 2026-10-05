"""Standing events kept by hand in standing.json: regular things with no feed.
Each entry: id, title, weekday (mon…sun), optional nth (2 = second of the month),
start/end ("HH:MM") or allDay, optional months, venue, address, city, url and the
flags free / family / allAges / outdoor."""

import json
import os
from datetime import datetime, timedelta

from model import FREE, LA, make_event, venue
from sources.base import SourceError

NAME = "standing"
LABEL = "Weekly regulars"
PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "standing.json")
WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def fetch(ctx):
    try:
        with open(PATH, encoding="utf-8") as f:
            entries = json.load(f)
    except FileNotFoundError:
        return []
    except ValueError as err:
        raise SourceError(f"standing.json is broken: {err}") from None
    return occurrences(entries, ctx.start.date(), (ctx.end - timedelta(days=1)).date())


def _on(entry, day):
    if WEEKDAYS[day.weekday()] != entry.get("weekday"):
        return False
    if entry.get("months") and day.month not in entry["months"]:
        return False
    return not entry.get("nth") or (day.day - 1) // 7 + 1 == entry["nth"]


def _at(day, hhmm):
    h, m = (int(x) for x in hhmm.split(":"))
    return datetime(day.year, day.month, day.day, h, m, tzinfo=LA)


def occurrences(entries, first, last):
    events = []
    for entry in entries:
        day = first
        while day <= last:
            if _on(entry, day):
                all_day = bool(entry.get("allDay"))
                start = day if all_day else _at(day, entry["start"])
                end = None if all_day or not entry.get("end") else _at(day, entry["end"])
                events.append(make_event(
                    "standing", f"{entry['id']}-{day.isoformat()}", entry["title"], start, end=end, all_day=all_day,
                    venue=venue(entry.get("venue"), entry.get("address")), city=entry.get("city"),
                    price=dict(FREE) if entry.get("free") else None, url=entry.get("url"),
                    family=bool(entry.get("family")), all_ages=bool(entry.get("allAges")),
                    outdoor=bool(entry.get("outdoor")), kind="organiser"))
            day += timedelta(days=1)
    return events
