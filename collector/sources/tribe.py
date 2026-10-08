"""Calendars on WordPress sites running The Events Calendar ("Tribe"): its REST
API, JSON, no key. One class; sources/__init__.py makes an instance per site."""

import html
import re
from datetime import datetime, timedelta

import net
from model import FREE, LA, make_event, plain, price_range, venue
from sources.base import SourceError

PATH = ("/wp-json/tribe/events/v1/events?start_date={first}&end_date={last}%2023:59:59"
        "&per_page=50&page={page}")
MAX_PAGES = 4
MONEY = re.compile(r"\$\s*(\d+(?:\.\d{1,2})?)")


def price_from(cost):
    """'Free' -> free; '$10 – $25' -> 10–25; anything without a $ amount -> None."""
    text = html.unescape(cost or "").strip()
    amounts = [float(a) for a in MONEY.findall(text)]
    if amounts:
        return price_range(min(amounts), max(amounts))
    return dict(FREE) if re.fullmatch(r"(?i)\s*free\s*", text) else None


def _names(items):
    return {html.unescape(i.get("name") or "").strip().lower() for i in items or [] if isinstance(i, dict)}


class TribeSource:
    def __init__(self, name, label, base, *, city, place=None, family_all=False, family_categories=(),
                 family_before=None, adult_categories=(), skip_categories=(), only_categories=(),
                 ignore_categories=(), kind="organiser"):
        self.NAME, self.LABEL = name, label
        self.base, self.city, self.place = base.rstrip("/"), city, place
        self.family_all, self.family_categories = family_all, set(family_categories)
        self.family_before = family_before
        self.adult_categories, self.skip_categories = set(adult_categories), set(skip_categories)
        self.only_categories = set(only_categories)          # when set, keep only events in one of these
        self.ignore_categories = set(ignore_categories)      # categories too loose to use as tags
        self.kind = kind                                     # "listing" for calendars of other people's events

    def fetch(self, ctx):
        first = ctx.start.date().isoformat()
        last = (ctx.end - timedelta(days=1)).date().isoformat()
        items = []
        for page in range(1, MAX_PAGES + 1):
            data = net.get_json(self.base + PATH.format(first=first, last=last, page=page))
            if not isinstance(data, dict) or not isinstance(data.get("events"), list):
                raise SourceError("unexpected response (no events list)")
            items += data["events"]
            if page >= (data.get("total_pages") or 1):
                break
        return self.parse(items)

    def parse(self, items):
        events = []
        for e in items:
            cats, tags = _names(e.get("categories")), _names(e.get("tags"))
            if cats & self.skip_categories or (self.only_categories and not cats & self.only_categories):
                continue
            try:
                start = datetime.strptime(e["start_date"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=LA)
                end = (datetime.strptime(e["end_date"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=LA)
                       if e.get("end_date") else None)
            except (KeyError, TypeError, ValueError):
                continue
            all_day = bool(e.get("all_day"))
            v = e.get("venue") if isinstance(e.get("venue"), dict) else {}
            name = html.unescape(v.get("venue") or "") or (self.place[0] if self.place else None)
            address = (", ".join(p for p in [v.get("address"), v.get("city"), v.get("stateprovince") or v.get("state"),
                                             v.get("zip")] if p)
                       or (self.place[1] if self.place else None))
            daytime = all_day or self.family_before is None or start.hour < self.family_before
            events.append(make_event(
                self.NAME, str(e.get("id")), html.unescape(e.get("title") or ""),
                start.date() if all_day else start,
                end=(end.date() if end else None) if all_day else end, all_day=all_day,
                venue=venue(name, address, v.get("geo_lat"), v.get("geo_lng")),
                city=v.get("city") or self.city, price=price_from(e.get("cost")), url=e.get("url"),
                text=plain(e.get("description") or ""), tags=(cats | tags) - self.ignore_categories,
                family=self.family_all or bool(cats & self.family_categories and daytime),
                adult=bool(cats & self.adult_categories), kind=self.kind))
        return events
