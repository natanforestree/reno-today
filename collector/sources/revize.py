"""City calendars on Revize sites (City of Reno, City of Sparks): one JSON array
of every event, with recurring ones as RRULE strings. One class; an instance per city."""

import re
import urllib.parse
from datetime import datetime, timedelta

import net
import rrule
from model import LA, city_from_address, make_event, plain, venue
from sources.base import SourceError

URL = ("https://{host}/_assets_/plugins/revizeCalendar/calendar_data_handler.php"
       "?webspace={webspace}&relative_revize_url=//builder1.revize.com&protocol=https:")
SKIP_TITLE = re.compile(r"^\s*cancell?ed\b|\bclos(ed|ure)\b", re.I)
URL_IN_TEXT = re.compile(r"https?://\S+")


def _duration(text):
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", text or "")
    length = timedelta(hours=int(m.group(1)), minutes=int(m.group(2))) if m else None
    return length or None


def _midnight(dt):
    return dt.hour == 0 and dt.minute == 0


class RevizeSource:
    EVERY = timedelta(hours=12)

    def __init__(self, name, label, host, webspace, *, city, page_url, skip_calendars,
                 kid_calendars=(), calendar_names=None):
        self.NAME, self.LABEL = name, label
        self.url = URL.format(host=host, webspace=webspace)
        self.city, self.page_url = city, page_url
        self.skip, self.kids = set(skip_calendars), set(kid_calendars)
        self.names = calendar_names or {}

    def fetch(self, ctx):
        data = net.get_json(self.url)
        if not isinstance(data, list):
            raise SourceError("unexpected response (not a list of events)")
        return self.parse(data, ctx.start.date(), (ctx.end - timedelta(days=1)).date())

    def parse(self, items, first, last):
        events = []
        for e in items:
            cals = {str(c) for c in e.get("calendar_displays") or []}
            title = " ".join((e.get("title") or "").split())
            if not title or SKIP_TITLE.search(title) or (cals and cals <= self.skip):
                continue
            try:
                start = datetime.fromisoformat(e["start"]).replace(second=0, microsecond=0)
                end = datetime.fromisoformat(e["end"]).replace(second=0, microsecond=0) if e.get("end") else None
            except (KeyError, TypeError, ValueError):
                continue
            all_day = bool(e.get("allDay")) or (_midnight(start) and end is not None and _midnight(end) and end > start)
            length = _duration(e.get("duration")) or (end - start if end and not all_day and end > start else None)
            raw_location = e.get("location") or ""
            found = URL_IN_TEXT.search(raw_location)
            location = URL_IN_TEXT.sub("", raw_location).strip(" ,")
            own = str(e.get("url") or "")
            link = own if own.startswith("http") else (found.group(0) if found else self.page_url)
            common = dict(
                all_day=all_day, venue=venue(location.split(",")[0].strip() or None, location or None),
                city=city_from_address(location, self.city), url=link,
                text=plain(urllib.parse.unquote(e.get("desc") or "")),
                tags=[self.names[c] for c in cals if c in self.names],
                family=bool(cals & self.kids), kind="organiser")
            for s in (rrule.expand(e["rrule"], first, last) if e.get("rrule") else [start]):
                if all_day:
                    last_day = (end - timedelta(days=1)).date() if end and (end - timedelta(days=1)).date() > s.date() else None
                    events.append(make_event(self.NAME, f"{e.get('id')}-{s:%Y%m%d%H%M}", title, s.date(),
                                             end=last_day, **common))
                else:
                    at = s.replace(tzinfo=LA)
                    events.append(make_event(self.NAME, f"{e.get('id')}-{s:%Y%m%d%H%M}", title, at,
                                             end=at + length if length else None, **common))
        return events
