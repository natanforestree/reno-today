"""The "Always an option" list: which standing places are open on a given day."""

from datetime import date

WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def hours_on(place, day):
    """That day's hours ('10:00-17:00' or 'dawn-dusk'), or None when closed or out of season."""
    d = date.fromisoformat(day)
    months = place.get("months")
    if months and d.month not in months:
        return None
    return (place.get("hours") or {}).get(WEEKDAYS[d.weekday()])


def open_on(places, day):
    return [(p, h) for p in places if (h := hours_on(p, day))]


def _clock(hhmm):
    h, m = (int(x) for x in hhmm.split(":"))
    return f"{h % 12 or 12}" if m == 0 else f"{h % 12 or 12}:{m:02d}"


def short_hours(hours):
    """'10:00-17:00' -> '10–5', '09:30-16:00' -> '9:30–4', 'dawn-dusk' -> 'dawn–dusk'."""
    start, _, end = hours.partition("-")
    if ":" not in start or ":" not in end:
        return hours.replace("-", "–")
    return f"{_clock(start)}–{_clock(end)}"
