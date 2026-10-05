"""Washoe County Regional Parks events: the Tockify calendar page's embedded
data (tockify.com/wcparks). Tockify's robots.txt rules out its /api/ feeds but
allows this page; we read it once per refresh and only ever link to event pages."""

import json
import re
from datetime import datetime, timezone

import net
from model import FREE, city_from_address, make_event, venue
from sources.base import SourceError

NAME = "wcparks"
LABEL = "Washoe County Parks"
URL = "https://tockify.com/wcparks"
MARKER = '"bootdata":'
FREE_EVENT = re.compile(r"\bfree (event|admission|entry|program)\b|\(free event\)", re.I)


def fetch(ctx):
    return parse(net.get_text(URL))


def _when(part):
    return datetime.fromtimestamp(part["millis"] / 1000, tz=timezone.utc)


def parse(page):
    at = page.find(MARKER)
    if at < 0:
        raise SourceError("no calendar data in the page (did Tockify change its page?)")
    try:
        boot, _ = json.JSONDecoder().raw_decode(page[at + len(MARKER):])
    except ValueError:
        raise SourceError("the calendar data didn't parse") from None
    query = boot.get("query") or {}
    seen, events = set(), []
    for bucket in ("upcoming", "pinboard"):
        for e in (query.get(bucket) or {}).get("events") or []:
            eid = e.get("eid") or {}
            key = (eid.get("uid"), eid.get("tid"))
            if key in seen or ((e.get("status") or {}).get("name") or "").lower() in ("cancelled", "canceled"):
                continue
            seen.add(key)
            when, c = e.get("when") or {}, e.get("content") or {}
            try:
                start = _when(when["start"])
                end = _when(when["end"]) if (when.get("end") or {}).get("millis") else None
            except (KeyError, TypeError, ValueError):
                continue
            all_day = bool(when.get("allDay"))
            if all_day:
                local_ms = when["start"]["millis"] + (when["start"].get("offset") or 0)
                start = datetime.fromtimestamp(local_ms / 1000, tz=timezone.utc).date()
                end = None
            title = " ".join(((c.get("summary") or {}).get("text") or "").split())
            text = (c.get("description") or {}).get("text") or ""
            address = c.get("address") or ""
            events.append(make_event(
                "wcparks", f"{eid.get('uid')}-{eid.get('tid')}", title, start, end=end, all_day=all_day,
                venue=venue(c.get("place"), address), city=city_from_address(address, "Reno"),
                price=dict(FREE) if FREE_EVENT.search(f"{title} {text}") else None,
                url=f"https://tockify.com/wcparks/detail/{eid.get('uid')}/{eid.get('tid')}",
                text=text, tags=((c.get("tagset") or {}).get("tags") or {}).get("default") or [],
                kind="organiser"))
    return events
