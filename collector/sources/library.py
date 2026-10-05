"""Washoe County Library events (LibCal calendar 12809): baby and toddler
storytimes and everything else the branches run. The calendar's JSON answers
one day per request and robots.txt asks for 10 s between requests, so a full
read takes about 80 s; EVERY keeps that to twice a day."""

import time
from datetime import datetime, timedelta

import net
from model import FREE, LA, make_event, plain, price_range, venue
from sources.base import SourceError

NAME = "library"
LABEL = "Washoe County Library"
EVERY = timedelta(hours=12)
CRAWL_DELAY = 10
URL = ("https://events.washoecountylibrary.us/ajax/calendar/list?c=12809&date={day}"
       "&perpage=100&page=1&audience=&cats=&camps=&inc=0")
MAX_LENGTH = timedelta(hours=6)      # longer timed listings are typos (10:30 to 22:50)
LITTLE_AUDIENCES = {1785, 1784}      # Babies & Toddlers, Preschool
# Branch (LibCal "campus") -> (address, city). Checked on washoecountylibrary.us.
BRANCHES = {
    "Downtown Reno Library": ("301 S Center St, Reno, NV 89501", "Reno"),
    "Northwest Reno Library": ("2325 Robb Dr, Reno, NV 89523", "Reno"),
    "Sierra View Library": ("4001 S Virginia St, Reno, NV 89502", "Reno"),
    "South Valleys Library": ("15650-A Wedge Pkwy, Reno, NV 89511", "Reno"),
    "North Valleys Library": ("1075 N Hills Blvd Ste 340, Reno, NV 89506", "Reno"),
    "Sparks Library": ("1125 12th St, Sparks, NV 89431", "Sparks"),
    "Spanish Springs Library": ("7100A Pyramid Hwy, Sparks, NV 89436", "Sparks"),
    "Incline Village Library": ("845 Alder Ave, Incline Village, NV 89451", "Incline Village"),
    "Duncan/Traner Community Library": ("1650 Carville Dr, Reno, NV 89512", "Reno"),
    "Verdi Community Library": ("270 Bridge St, Verdi, NV 89439", "Verdi"),
    "Senior Center Library": ("1155 E 9th St, Reno, NV 89512", "Reno"),
    "Gerlach Community Library": ("555 E Sunset Blvd, Gerlach, NV 89412", "Gerlach"),
}


def fetch(ctx):
    results = []
    day = ctx.start.date()
    while day < ctx.end.date():
        if day != ctx.start.date():
            time.sleep(CRAWL_DELAY)
        data = net.get_json(URL.format(day=day.isoformat()))
        if not isinstance(data, dict) or not isinstance(data.get("results"), list):
            raise SourceError("unexpected response (no results list)")
        if (data.get("total_results") or 0) > len(data["results"]):
            print(f"library: {day} has more than one page; only the first was read")
        results += data["results"]
        day += timedelta(days=1)
    return parse(results)


def _price(cost):
    cost = (cost or "").replace("$", "").strip()
    if not cost:
        return dict(FREE)                # library programs are free unless a fee is listed
    try:
        return price_range(float(cost), float(cost))
    except ValueError:
        return None


def parse(results):
    events = []
    for r in results:
        campus = (r.get("campus") or "").strip() or "Washoe County Library"
        if r.get("online_event") or campus.lower().startswith("online"):
            continue
        try:
            start = datetime.strptime(r["startdt"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=LA)
            end = datetime.strptime(r["enddt"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=LA) if r.get("enddt") else None
        except (KeyError, TypeError, ValueError):
            continue
        all_day = bool(r.get("all_day"))
        if end and (end <= start or end - start > MAX_LENGTH):
            end = None
        address, city = BRANCHES.get(campus, (None, None))
        if address is None:
            print(f"library: unknown branch {campus!r}; add it to BRANCHES")
            address, city = "Washoe County, NV", "Reno"
        audiences = r.get("audiences") or []
        events.append(make_event(
            "library", str(r.get("id")), r.get("title") or "",
            start.date() if all_day else start, end=None if all_day else end, all_day=all_day,
            ongoing=all_day and bool(r.get("recurring_event")),
            venue=venue(campus, address), city=city, price=_price(r.get("registration_cost")),
            url=r.get("url"), text=plain(r.get("description") or r.get("shortdesc") or ""),
            tags=[a.get("name") for a in audiences] + [c.get("name") for c in r.get("categories_arr") or []],
            family=bool(LITTLE_AUDIENCES & {a.get("id") for a in audiences}), kind="organiser"))
    return events
