#!/usr/bin/env python3
"""Fixture data for checking the page by eye or in a browser. Stdlib only.

    python3 dev/make_fixture.py                    # dated from today, Reno time
    python3 dev/make_fixture.py --today 2026-10-10

Serve the repo root (python3 -m http.server 8000) and open, for example:
    http://localhost:8000/docs/?data=../dev/fixture/full/&now=2026-10-10T10:45:00-07:00

Variants (dev/fixture/<name>/):
  full     a busy week: little-ones events (one "on now" at 10:45), every part of
           the day, an ongoing exhibit, day trips, a 21+ show, a Loving Reno pick,
           a title full of HTML (must show as text), places and weather.
  empty    events: [] with every source fine.
  partial  four events today, no weather.json, Ticketmaster failing.
  failing  every source failing and the data 9 hours old (the stale warning).
"""

import argparse
import json
import os
import sys
import zlib
from datetime import date, datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "collector"))
import classify  # noqa: E402
import model  # noqa: E402

OUT = os.path.join(HERE, "fixture")
LR = {"title": "2026 Ultimate Reno Halloween & Fall Guide", "url": "https://www.lovingreno.com/"}


def at(day, hh, mm=0):
    return datetime(day.year, day.month, day.day, hh, mm, tzinfo=model.LA)


def ev(day, hh, mm, title, *, city="Reno", place="Downtown Reno", free=False, price=None, end=None,
       all_day=False, family=False, adult=False, all_ages=False, outdoor=False, source="tm", lr=False,
       start=None, text=""):
    e = model.make_event(
        source, f"{title}-{day}-{hh}{mm}", title, start or (day if all_day else at(day, hh, mm)),
        end=end, all_day=all_day, venue=model.venue(place, f"{place}, {city}, NV"), city=city,
        price=model.FREE if free else (model.price_range(*price) if price else None),
        url=f"https://example.org/{source}/{zlib.crc32(title.encode()) % 10000}", text=text,
        family=family, adult=adult, all_ages=all_ages, outdoor=outdoor,
        kind="ticketing" if source == "tm" else "organiser")
    e = classify.classify(e)
    if lr:
        e["lovingReno"] = dict(LR)
    return model.finalize(e)


def week(d0):
    events = [
        ev(d0, 8, 0, "Riverside Farmers Market", place="Idlewild Park", free=True, outdoor=True, source="standing"),
        ev(d0, 9, 30, "Baby & Toddler Storytime", city="Sparks", place="Sparks Library", free=True, source="library"),
        ev(d0, 10, 30, "Small Wonder Wednesday", place="The Discovery", family=True, source="discovery",
           end=at(d0, 11, 30)),
        ev(d0, 0, 0, "Fall Festival at Rancho San Rafael", place="Rancho San Rafael Park", all_day=True, free=True,
           text="Fun for kids and families.", source="wcparks"),
        ev(d0, 13, 5, "Reno Aces vs Sacramento River Cats", place="Greater Nevada Field", price=(12, 30),
           all_ages=True, outdoor=True, source="aces"),
        ev(d0, 18, 0, "Wind Ensemble Fall Concert", place="Nightingale Concert Hall", free=True, source="unr"),
        ev(d0, 19, 30, "Brandi Carlile", place="Grand Sierra Resort", price=(45.5, 129), lr=True),
        ev(d0, 20, 0, '<img src=x onerror="alert(1)"> Totally Safe Show', place="Cargo Concert Hall", price=(20, 20)),
        ev(d0, 22, 0, "Late Night Comedy", place="Silver Legacy", price=(25, 25), adult=True),
        ev(d0, 12, 0, "Earth's Winding Sheet", place="Lilley Museum", source="unr",
           start=at(d0 - timedelta(days=30), 12), end=at(d0 + timedelta(days=40), 16)),
        ev(d0, 0, 0, "Lake Tahoe Oktoberfest", city="Tahoe City", place="Commons Beach", all_day=True, outdoor=True),
        ev(d0, 10, 0, "Pumpkin Patch Hayrides", city="Carson City", place="Lattin Farms", family=True, source="carson"),
    ]
    for i in range(1, 8):
        d = d0 + timedelta(days=i)
        if i % 2:
            events.append(ev(d, 10, 15, "Toddler Time", place="Northwest Reno Library", free=True, source="library"))
        events.append(ev(d, 19, 0, f"Evening Show {i}", place="Pioneer Center", price=(30, 75)))
        if i in (3, 6):
            events.append(ev(d, 11, 0, "Family Day in the Park", place="Idlewild Park", free=True, source="reno"))
    return sorted(events, key=lambda e: (e["start"], e["title"]))


def weather(d0):
    days = []
    for i in range(8):
        d = (d0 + timedelta(days=i)).isoformat()
        rainy = i == 2
        days.append({"date": d, "high": 76 - i, "low": 50 - i // 2, "summary": "Rain" if rainy else "Clear",
                     "emoji": "🌧️" if rainy else "☀️", "code": 63 if rainy else 0, "rain": 70 if rainy else 5,
                     "sunrise": "07:01", "sunset": "18:31",
                     "nice": [] if rainy else [{"from": "10:00", "to": "17:00"}],
                     "hours": [{"h": h, "t": 50 + h, "rain": 5} for h in range(24)]})
    return {"generatedAt": model.utc(at(d0, 7, 31)), "days": days}


PLACES = [
    {"name": "The Discovery", "area": "reno", "goodFor": "Little Discoveries area for ages 0–5", "setting": "indoor",
     "hours": {"mon": None, "tue": "10:00-17:00", "wed": "10:00-20:00", "thu": "10:00-17:00", "fri": "10:00-17:00",
               "sat": "10:00-17:00", "sun": "10:00-17:00"}, "months": None, "free": False,
     "url": "https://nvdm.org/", "address": "490 S Center St, Reno, NV 89501", "notes": "Free under age 1."},
    {"name": "Idlewild Park", "area": "reno", "goodFor": "playground, duck pond, river paths", "setting": "outdoor",
     "hours": {d: "06:00-19:00" for d in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")}, "months": None,
     "free": True, "url": "https://www.reno.gov/", "address": "1905 Idlewild Dr, Reno, NV 89509", "notes": ""},
    {"name": "Animal Ark Wildlife Sanctuary", "area": "reno", "goodFor": "rescued wild animals", "setting": "outdoor",
     "hours": {"mon": None, "tue": "10:00-16:30", "wed": "10:00-16:30", "thu": "10:00-16:30", "fri": "10:00-16:30",
               "sat": "10:00-16:30", "sun": "10:00-16:30"}, "months": [3, 4, 5, 6, 7, 8, 9, 10, 11], "free": False,
     "url": "https://www.animalark.org/", "address": "1265 Deerlodge Rd, Reno, NV", "notes": ""},
]
GUIDE = {"title": "2026 Ultimate Reno Halloween & Fall Guide: Haunted Houses", "shortTitle": LR["title"],
         "url": "https://www.lovingreno.com/2026/09/2026-reno-halloween-fall-guide-haunted.html", "published": "2026-09-24"}
LABELS = {"ticketmaster": "Ticketmaster", "unr": "UNR events", "wolfpack": "Nevada Wolf Pack", "aces": "Reno Aces",
          "weather": "Weather (Open-Meteo)", "lovingreno": "Loving Reno"}


def status(generated, failing=()):
    return {"generatedAt": generated, "sources": {
        k: {"label": v, "ok": k not in failing, "count": 0 if k in failing else 5,
            "lastSuccess": generated, "error": "HTTP 503 (" + k + ")" if k in failing else None}
        for k, v in LABELS.items()}}


def write(name, files):
    folder = os.path.join(OUT, name)
    os.makedirs(folder, exist_ok=True)
    for f in os.listdir(folder):
        os.remove(os.path.join(folder, f))
    for fname, obj in files.items():
        with open(os.path.join(folder, fname), "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=1)
    print(f"wrote dev/fixture/{name}/ ({', '.join(files)})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--today", help="YYYY-MM-DD (default: today in Reno)")
    args = ap.parse_args()
    d0 = date.fromisoformat(args.today) if args.today else datetime.now(model.LA).date()
    gen = model.utc(at(d0, 7, 31))
    full = week(d0)
    events = lambda evs, g=gen: {"generatedAt": g, "timezone": "America/Los_Angeles", "events": evs}  # noqa: E731
    write("full", {"events.json": events(full), "weather.json": weather(d0), "status.json": status(gen),
                   "guide.json": GUIDE, "places.json": PLACES})
    write("empty", {"events.json": events([]), "weather.json": weather(d0), "status.json": status(gen),
                    "guide.json": GUIDE, "places.json": PLACES})
    today = [e for e in full if e["start"][:10] == d0.isoformat() and not e["ongoing"]][:4]
    write("partial", {"events.json": events(today), "status.json": status(gen, failing=("ticketmaster",)),
                      "guide.json": GUIDE, "places.json": PLACES})
    old = model.utc(datetime.now(model.LA) - timedelta(hours=9))
    write("failing", {"events.json": events(full, old), "weather.json": weather(d0),
                      "status.json": status(old, failing=tuple(LABELS)), "guide.json": GUIDE, "places.json": PLACES})


if __name__ == "__main__":
    main()
