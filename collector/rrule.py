"""Just enough RFC 5545 recurrence for the City of Reno and Sparks calendars:
FREQ=DAILY/WEEKLY/MONTHLY, INTERVAL, BYDAY (with ordinals such as 2SA or -1FR
when monthly), one BYSETPOS, BYMONTHDAY, COUNT, RDATE and EXDATE. UNTIL is read
as an inclusive date, because these calendars write it as midnight at the start
of the last day. Times are naive local times; seconds are dropped."""

import re
from datetime import date, datetime, timedelta

DAYS = {"MO": 0, "TU": 1, "WE": 2, "TH": 3, "FR": 4, "SA": 5, "SU": 6}


def _dt(value):
    value = value.strip()
    if "T" in value:
        return datetime.strptime(value[:15], "%Y%m%dT%H%M%S").replace(second=0)
    return datetime.strptime(value[:8], "%Y%m%d")


def parse(spec):
    """(dtstart, rule dict, rdates, exdates); dtstart is None if missing."""
    dtstart, rule, rdates, exdates = None, {}, [], []
    for line in (spec or "").replace("\\n", "\n").splitlines():
        name, _, value = line.partition(":")
        name = name.split(";")[0].strip().upper()
        try:
            if name == "DTSTART":
                dtstart = _dt(value)
            elif name == "RRULE":
                rule = dict(p.split("=", 1) for p in value.strip().split(";") if "=" in p)
            elif name == "RDATE":
                rdates += [_dt(v) for v in value.split(",") if v.strip()]
            elif name == "EXDATE":
                exdates += [_dt(v) for v in value.split(",") if v.strip()]
        except ValueError:
            continue
    return dtstart, rule, rdates, exdates


def _weekdays_in_month(year, month, weekday):
    d, out = date(year, month, 1), []
    while d.month == month:
        if d.weekday() == weekday:
            out.append(d)
        d += timedelta(days=1)
    return out


def _monthly_byday(day, rule):
    setpos = int(rule["BYSETPOS"]) if rule.get("BYSETPOS", "").lstrip("-").isdigit() else None
    for part in rule["BYDAY"].split(","):
        m = re.fullmatch(r"([+-]?\d+)?([A-Z]{2})", part.strip())
        if not m or m.group(2) not in DAYS or DAYS[m.group(2)] != day.weekday():
            continue
        n = int(m.group(1)) if m.group(1) else setpos
        if n is None:
            return True
        same = _weekdays_in_month(day.year, day.month, day.weekday())
        try:
            if same[n - 1 if n > 0 else n] == day:
                return True
        except IndexError:
            continue
    return False


def _matches(day, start, rule):
    freq = rule.get("FREQ")
    interval = int(rule.get("INTERVAL") or 1)
    if freq == "DAILY":
        return (day - start).days % interval == 0
    if freq == "WEEKLY":
        wanted = {DAYS[d[-2:]] for d in rule.get("BYDAY", "").split(",") if d[-2:] in DAYS} or {start.weekday()}
        weeks = ((day - timedelta(days=day.weekday())) - (start - timedelta(days=start.weekday()))).days // 7
        return day.weekday() in wanted and weeks % interval == 0
    if freq == "MONTHLY":
        if ((day.year - start.year) * 12 + day.month - start.month) % interval:
            return False
        if rule.get("BYMONTHDAY"):
            return day.day in {int(x) for x in rule["BYMONTHDAY"].split(",") if x.strip().lstrip("-").isdigit()}
        if rule.get("BYDAY"):
            return _monthly_byday(day, rule)
        return day.day == start.day
    return False


def expand(spec, first, last):
    """Occurrence starts (naive local datetimes) whose date is in [first, last]."""
    dtstart, rule, rdates, exdates = parse(spec)
    if dtstart is None:
        return []
    until = None
    if rule.get("UNTIL"):
        try:
            until = _dt(rule["UNTIL"]).date()
        except ValueError:
            until = None
    count = int(rule["COUNT"]) if (rule.get("COUNT") or "").isdigit() else None
    found = {dtstart} if first <= dtstart.date() <= last else set()
    if rule.get("FREQ"):
        day, n = dtstart.date(), 0
        stop = min(last, until) if until else last
        while day <= stop:
            if _matches(day, dtstart.date(), rule):
                n += 1
                if count and n > count:
                    break
                if day >= first:
                    found.add(datetime.combine(day, dtstart.time()))
            day += timedelta(days=1)
    found |= {r for r in rdates if first <= r.date() <= last and (until is None or r.date() <= until)}
    skip_days = {e.date() for e in exdates}
    return sorted(o for o in found if o.date() not in skip_days)
