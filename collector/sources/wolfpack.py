"""Nevada Wolf Pack home games: the athletics site's iCal feed, no key."""

import html
import re
from datetime import datetime

import ical
import net
from model import make_event, venue
from sources.base import SourceError

NAME = "wolfpack"
LABEL = "Nevada Wolf Pack"
URL = "https://nevadawolfpack.com/calendar.ashx/calendar.ics"
HOME = {("reno", "nev."), ("stateline", "nev.")}


def fetch(ctx):
    text = net.get_text(URL)
    if "BEGIN:VCALENDAR" not in text:
        raise SourceError("not an iCal feed")
    return parse(text)


def clean_title(summary):
    s = re.sub(r"^\[[A-Z]\]\s*", "", summary)
    s = re.sub(r"\s+-\s+Presented by:.*$", "", s, flags=re.I)
    return " ".join(s.replace("University of Nevada ", "Nevada ").split())


def parse(text):
    events = []
    for ev in ical.events(text):
        parts = [p.strip() for p in ical.text(ev, "LOCATION").split(",")]
        if len(parts) < 2 or (parts[0].lower(), parts[1].lower()) not in HOME:
            continue
        start = ical.when(ev.get("DTSTART"))
        if start is None:
            continue
        all_day = not isinstance(start, datetime)
        end = ical.when(ev.get("DTEND"))
        events.append(make_event(
            "wolfpack", ical.text(ev, "UID"), clean_title(ical.text(ev, "SUMMARY")), start,
            end=end if (not all_day and isinstance(end, datetime)) else None, all_day=all_day,
            venue=venue(", ".join(p for p in parts[2:] if p) or None, f"{parts[0]}, NV"),
            city=parts[0], url=html.unescape(ical.text(ev, "URL")) or None,
            tags=["sports"], kind="organiser"))
    return events
