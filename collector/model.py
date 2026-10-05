"""The event shape every source produces, and the time and place helpers they
share. The public fields are the spec's "Data" section; fields starting with
"_" are for classification and merging only and never reach docs/data/."""

import html
import re
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

LA = ZoneInfo("America/Los_Angeles")
DAYS = 8                                # today + 7
ONGOING_AFTER = timedelta(days=3)       # longer than this is an exhibit or a run
LOCAL_AREAS = ("reno", "sparks")
FREE = {"free": True}

# Lower-case city -> area. Anything not listed is "other".
CITY_AREAS = {
    "reno": "reno", "sparks": "sparks", "verdi": "reno",   # Verdi is 15 min out: local
    "carson city": "carson", "virginia city": "virginia-city",
    "stateline": "tahoe", "south lake tahoe": "tahoe", "incline village": "tahoe",
    "crystal bay": "tahoe", "kings beach": "tahoe", "tahoe vista": "tahoe",
    "tahoe city": "tahoe", "olympic valley": "tahoe", "truckee": "tahoe",
    "homewood": "tahoe", "zephyr cove": "tahoe", "gold hill": "virginia-city",
}
# Rough drive from downtown Reno.
DRIVE = {
    "carson city": "~35 min", "virginia city": "~40 min", "truckee": "~35 min",
    "incline village": "~45 min", "crystal bay": "~45 min", "kings beach": "~50 min",
    "tahoe vista": "~50 min", "olympic valley": "~50 min", "tahoe city": "~55 min",
    "homewood": "~60 min", "zephyr cove": "~65 min", "stateline": "~70 min",
    "south lake tahoe": "~75 min", "fernley": "~35 min", "dayton": "~35 min",
    "minden": "~50 min", "gardnerville": "~55 min", "fallon": "~65 min",
    "washoe valley": "~25 min", "new washoe city": "~25 min",
}
AREA_DRIVE = {"carson": "~35 min", "virginia-city": "~40 min", "tahoe": "~45–75 min"}
KNOWN_TOWNS = set(CITY_AREAS) | set(DRIVE)

_STATE = r"(?:NV|Nev|Nevada|CA|Calif|California)\.?(?:[\s,]+\d{5}(?:-\d{4})?)?"
# "<town>, NV 89501, USA" at the end of an address; the commas, zip and country are optional.
_STATE_AT_END = re.compile(rf"^(?P<before>.*?)[\s,]+{_STATE}(?:[\s,]+(?:USA|US|United States))?[\s,.]*$", re.I)
_TRAILING_STATE = re.compile(rf"[\s,]+{_STATE}$", re.I)


def _clean(text):
    return " ".join(html.unescape(text or "").split())


def _town_key(city):
    """'Reno, NV 89501' -> 'reno'."""
    return _TRAILING_STATE.sub("", _clean(city)).strip(" ,.").lower()


def area_for(city):
    return CITY_AREAS.get(_town_key(city), "other")


def drive_for(city, area):
    if area in LOCAL_AREAS:
        return None
    return DRIVE.get(_town_key(city)) or AREA_DRIVE.get(area)


def _known_town_at_end(text):
    """'40 E. 4th St. Reno' -> 'Reno' (the longest known town the text ends with)."""
    words = text.split()
    for i in range(len(words)):
        town = " ".join(words[i:]).strip(" ,.")
        if town.lower() in KNOWN_TOWNS:
            return town
    return None


def city_from_address(address, default=None):
    """The town in an address: the words just before the state ('561 Crystal Park Rd,
    Verdi, NV 89439' -> 'Verdi'; '40 E. 4th St. Reno, Nevada 89501' -> 'Reno'), or a
    known town the address ends with ('Victorian Square, Sparks'). An unknown town is
    kept (its area is "other"); a bare street or no town at all gives `default`."""
    text = _clean(address)
    m = _STATE_AT_END.match(text)
    part = (m.group("before") if m else text).split(",")[-1].strip(" .")
    town = _known_town_at_end(part)
    if town:
        return town
    if m and part and not re.search(r"\d", part):
        return part
    return default


def day_start(d):
    """Midnight in Reno at the start of date d."""
    return datetime.combine(d, time(0), LA)


def window(now):
    """(start, end) of the days shown: today 00:00 to 8 days later, Reno time."""
    first = now.astimezone(LA).date()
    return day_start(first), day_start(first + timedelta(days=DAYS))


def iso(dt):
    return dt.astimezone(LA).isoformat(timespec="seconds")


def utc(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def plain(text):
    """HTML to one line of plain text."""
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", text or "")).split())


def _coord(value):
    try:
        return round(float(value), 5)
    except (TypeError, ValueError):
        return None


def venue(name=None, address=None, lat=None, lon=None):
    name, address = (name or "").strip() or None, (address or "").strip() or None
    if not (name or address):
        return None
    return {"name": name, "address": address, "lat": _coord(lat), "lon": _coord(lon)}


def price_range(low, high):
    """{"free": True} for 0–0, {"min", "max"} otherwise, None when unknown."""
    if low is None and high is None:
        return None
    low = high if low is None else low
    high = low if high is None else high
    if low == 0 and high == 0:
        return dict(FREE)
    return {"min": round(float(low), 2), "max": round(float(high), 2)}


def _as_date(value):
    return value.astimezone(LA).date() if isinstance(value, datetime) else value


def make_event(source, source_id, title, start, *, end=None, all_day=False, ongoing=False,
               venue=None, city=None, price=None, url=None, text="", tags=(),
               family=False, adult=False, all_ages=False, outdoor=False, kind="organiser"):
    """One normalised event. start/end are aware datetimes, or dates when all_day
    (end = the last day, inclusive). kind is "organiser" (the venue's or
    organiser's own feed) or "ticketing" (decides which listing wins on merge)."""
    if all_day:
        start = day_start(_as_date(start))
        end = day_start(_as_date(end)) if end else None
    else:
        start = start.astimezone(LA)
        end = end.astimezone(LA) if end else None
    if end is not None and end < start:
        end = None
    area = area_for(city)
    link = url.strip() if isinstance(url, str) and re.match(r"https?://", url.strip(), re.I) else None
    return {
        "id": f"{source}:{source_id}",
        "title": " ".join((title or "").split()),
        "start": iso(start),
        "end": iso(end) if end else None,
        "allDay": bool(all_day),
        "ongoing": bool(ongoing) or (end is not None and end - start > ONGOING_AFTER),
        "venue": venue,
        "area": area,
        "drive": drive_for(city, area),
        "price": price,
        "tier": "general",
        "hints": [],
        "links": [{"source": source, "url": link}] if link else [],
        "lovingReno": None,
        "_text": (text or "")[:2000],
        "_tags": sorted({t.strip().lower() for t in tags if t and t.strip()}),
        "_family": bool(family),
        "_adult": bool(adult),
        "_allAges": bool(all_ages),
        "_outdoor": bool(outdoor),
        "_kind": kind,
    }


def finalize(event):
    """The event as written to docs/data/events.json (no private fields)."""
    return {k: v for k, v in event.items() if not k.startswith("_")}


def local_date(event):
    return event["start"][:10]


def end_date(event):
    return (event["end"] or event["start"])[:10]


def in_window(event, start, end):
    """True if the event touches the days from start up to (not including) end."""
    first, last = start.date().isoformat(), (end - timedelta(days=1)).date().isoformat()
    return local_date(event) <= last and end_date(event) >= first
