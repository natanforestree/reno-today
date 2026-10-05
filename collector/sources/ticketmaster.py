"""Ticketmaster Discovery API: concerts, shows, family shows and sports
within ~60 miles of Reno. Needs the TICKETMASTER_KEY secret."""

import re
from datetime import date, datetime

import net
from model import make_event, price_range, utc, venue
from sources.base import SourceError

NAME = "ticketmaster"
LABEL = "Ticketmaster"
URL = ("https://app.ticketmaster.com/discovery/v2/events.json?apikey={key}"
       "&latlong=39.5296,-119.8138&radius=60&unit=miles&locale=*"
       "&startDateTime={start}&endDateTime={end}&size=200&page={page}&sort=date,asc")
MAX_PAGES = 5            # the API refuses size * page beyond 1,000
JUNK = re.compile(r"\b(parking|season tickets?|gift cards?|vip packages?|upgrades?|suite rentals?)\b", re.I)
SKIP_STATUS = {"cancelled", "canceled", "postponed"}
FAMILY = {"family", "children's theatre"}


def fetch(ctx):
    key = ctx.env.get("TICKETMASTER_KEY")
    if not key:
        raise SourceError("not set up yet (TICKETMASTER_KEY missing)")
    items = []
    for page in range(MAX_PAGES):
        data = net.get_json(URL.format(key=key, start=utc(ctx.start), end=utc(ctx.end), page=page),
                            label="ticketmaster")
        if not isinstance(data, dict) or not isinstance(data.get("page"), dict):
            raise SourceError("unexpected response (no page info)")
        items += (data.get("_embedded") or {}).get("events") or []
        info = data["page"]
        if (info.get("number") or 0) + 1 >= (info.get("totalPages") or 0):
            break
    return parse(items)


def _start(dates):
    s = dates.get("start") or {}
    if s.get("dateTime") and not (s.get("timeTBA") or s.get("noSpecificTime")):
        return datetime.fromisoformat(s["dateTime"].replace("Z", "+00:00")), False
    if s.get("localDate") and not (s.get("dateTBD") or s.get("dateTBA")):
        return date.fromisoformat(s["localDate"]), True
    raise ValueError("no usable start")


def parse(items):
    events = []
    for ev in items:
        name = (ev.get("name") or "").strip()
        dates = ev.get("dates") or {}
        if not name or JUNK.search(name):
            continue
        if ((dates.get("status") or {}).get("code") or "").lower() in SKIP_STATUS:
            continue
        try:
            start, all_day = _start(dates)
            end_text = (dates.get("end") or {}).get("dateTime")
            end = datetime.fromisoformat(end_text.replace("Z", "+00:00")) if end_text and not all_day else None
        except ValueError:
            continue
        v = (((ev.get("_embedded") or {}).get("venues")) or [{}])[0]
        city = (v.get("city") or {}).get("name")
        address = ", ".join(p for p in [(v.get("address") or {}).get("line1"), city,
                                        (v.get("state") or {}).get("stateCode")] if p) or None
        loc = v.get("location") or {}
        classes = ev.get("classifications") or []
        cls = next((c for c in classes if c.get("primary")), classes[0] if classes else {})
        tags = [(cls.get(k) or {}).get("name") for k in ("segment", "genre", "subGenre")]
        tags = [t for t in tags if t and t != "Undefined"]
        prices = [p for p in ev.get("priceRanges") or [] if isinstance(p.get("min"), (int, float))]
        price = (price_range(min(p["min"] for p in prices), max(p.get("max", p["min"]) for p in prices))
                 if prices else None)
        events.append(make_event(
            "tm", ev.get("id") or name, name, start, end=end, all_day=all_day,
            venue=venue(v.get("name"), address, loc.get("latitude"), loc.get("longitude")),
            city=city, price=price, url=ev.get("url"),
            text=" ".join(filter(None, [ev.get("info"), ev.get("pleaseNote")])),
            tags=tags, family=bool(cls.get("family")) or bool({t.lower() for t in tags} & FAMILY),
            adult=bool((ev.get("ageRestrictions") or {}).get("legalAgeEnforced")), kind="ticketing"))
    return events
