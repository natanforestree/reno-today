"""University of Nevada, Reno events: Localist API, JSON, no key."""

from datetime import datetime, timedelta

import net
from model import FREE, make_event, plain, price_range, venue
from sources.base import SourceError

NAME = "unr"
LABEL = "UNR events"
URL = "https://events.unr.edu/api/2/events?start={start}&end={end}&pp=100&page={page}"
MAX_PAGES = 5
LOCAL_CITIES = {"reno", "sparks"}
# Listings only students and staff can go to.
INTERNAL_TYPES = {"training & workshops", "professional development", "staff engagement",
                  "prospective & new students", "clubs & organizations",
                  "health, safety & wellness"}
CAMPUS = "University of Nevada, Reno"


def fetch(ctx):
    first = ctx.start.date().isoformat()
    last = (ctx.end - timedelta(days=1)).date().isoformat()
    items = []
    for page in range(1, MAX_PAGES + 1):
        data = net.get_json(URL.format(start=first, end=last, page=page))
        if not isinstance(data, dict) or not isinstance(data.get("events"), list):
            raise SourceError("unexpected response (no events list)")
        items += data["events"]
        if page >= ((data.get("page") or {}).get("total") or 1):
            break
    return parse(items)


def parse(items):
    events = []
    for wrapper in items:
        event = _one((wrapper or {}).get("event") or {})
        if event:
            events.append(event)
    return events


def _names(objs):
    return {(o.get("name") or "").strip().lower() for o in objs or [] if isinstance(o, dict)}


def _price(e):
    if e.get("free"):
        return dict(FREE)
    try:
        cost = float(str(e.get("ticket_cost") or "").replace("$", "").strip())
    except ValueError:
        return None
    return price_range(cost, cost)


def _one(e):
    if e.get("experience") == "virtual" or e.get("private") or e.get("status") != "live":
        return None
    geo = e.get("geo") or {}
    city = (geo.get("city") or "").strip()
    groups = _names(e.get("groups"))
    filters = e.get("filters") or {}
    types = _names(filters.get("event_types"))
    if city and city.lower() not in LOCAL_CITIES:
        return None
    if (not city and "extension" in groups) or "counseling services" in groups:
        return None
    if types and types <= INTERNAL_TYPES:
        return None
    instances = e.get("event_instances") or []
    inst = (instances[0].get("event_instance") if instances else None) or {}
    try:
        start = datetime.fromisoformat(inst["start"])
        end = datetime.fromisoformat(inst["end"]) if inst.get("end") else None
    except (KeyError, TypeError, ValueError):
        return None
    all_day = bool(inst.get("all_day"))
    return make_event(
        "unr", str(inst.get("id") or e.get("id")), e.get("title") or "",
        start.date() if all_day else start,
        end=None if all_day else end, all_day=all_day,
        ongoing="exhibitions (recurring)" in types,
        venue=venue((e.get("location_name") or "").strip() or CAMPUS,
                    geo.get("street") or f"{CAMPUS}, Reno, NV",
                    geo.get("latitude"), geo.get("longitude")),
        city=city or "Reno", price=_price(e), url=e.get("localist_url"),
        text=e.get("description_text") or plain(e.get("description") or ""),
        tags=types | groups | _names(filters.get("event_special_topics")),
        kind="organiser")
