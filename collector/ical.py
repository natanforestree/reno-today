"""Just enough iCalendar (RFC 5545) to read event feeds: VEVENT properties,
text unescaping, and DTSTART/DTEND as dates or aware datetimes. Recurrence
rules (RRULE) are not expanded; the feeds we use list each date."""

import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from model import LA


def unfold(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"\n[ \t]", "", text)


def unescape(value):
    out, i = [], 0
    while i < len(value):
        if value[i] == "\\" and i + 1 < len(value):
            nxt = value[i + 1]
            out.append("\n" if nxt in "nN" else nxt)
            i += 2
        else:
            out.append(value[i])
            i += 1
    return "".join(out)


def parse_line(line):
    """'DTSTART;TZID=X:20261010T103000' -> ('DTSTART', {'TZID': 'X'}, '20261010T103000')."""
    quoted = False
    for i, c in enumerate(line):
        if c == '"':
            quoted = not quoted
        elif c == ":" and not quoted:
            break
    else:
        return None
    name, *params = line[:i].split(";")
    found = {}
    for p in params:
        key, _, val = p.partition("=")
        found[key.upper()] = val.strip('"')
    return name.upper(), found, line[i + 1:]


def events(text):
    """Each VEVENT as {NAME: (params, value)}; for repeated names the last wins."""
    current = None
    for line in unfold(text).split("\n"):
        if line == "BEGIN:VEVENT":
            current = {}
        elif line == "END:VEVENT":
            if current is not None:
                yield current
            current = None
        elif current is not None:
            parsed = parse_line(line)
            if parsed:
                current[parsed[0]] = (parsed[1], parsed[2])


def when(prop):
    """A DTSTART/DTEND (params, value) as a date (all-day) or an aware datetime."""
    if not prop:
        return None
    params, value = prop
    value = value.strip()
    try:
        if params.get("VALUE") == "DATE" or re.fullmatch(r"\d{8}", value):
            return datetime.strptime(value, "%Y%m%d").date()
        if value.endswith("Z"):
            return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        naive = datetime.strptime(value, "%Y%m%dT%H%M%S")
    except ValueError:
        return None
    try:
        tz = ZoneInfo(params["TZID"]) if params.get("TZID") else LA
    except (ZoneInfoNotFoundError, ValueError):
        tz = LA
    return naive.replace(tzinfo=tz)


def text(ev, name):
    prop = ev.get(name)
    return unescape(prop[1]).strip() if prop else ""
