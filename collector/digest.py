"""The 07:xx Discord message (spec: "Discord digest"): today's picks as plain
text, at most 2,000 characters, then a link to the full page."""

from datetime import date, datetime, timedelta

import net
from model import LOCAL_AREAS
from places import open_on, short_hours

PAGE_URL = "https://renotoday.org/"
LIMIT = 2000
PER_SECTION = 5
LINE_MAX = 140
AREA_NAMES = {"tahoe": "Lake Tahoe", "carson": "Carson City", "virginia-city": "Virginia City"}
MULTI_DAY = timedelta(hours=20)


def on_day(e, day):
    """One-day events count on their start date; all-day, ongoing and 20 h+ events
    on every date they cover (a Fri–Sun festival is in each day's digest)."""
    first = last = e["start"][:10]
    if e.get("end") and (e["allDay"] or e["ongoing"]
                         or datetime.fromisoformat(e["end"]) - datetime.fromisoformat(e["start"]) >= MULTI_DAY):
        last = e["end"][:10]
    return first <= day <= last


def fmt_time(e):
    if e["allDay"]:
        return "all day"
    h, m = int(e["start"][11:13]), int(e["start"][14:16])
    return f"{h % 12 or 12}{f':{m:02d}' if m else ''}{'am' if h < 12 else 'pm'}"


def _cut(line):
    return line if len(line) <= LINE_MAX else line[:LINE_MAX - 1] + "…"


def item(e):
    parts = [f"{fmt_time(e)} {e['title']}"]
    if (e.get("venue") or {}).get("name"):
        parts.append(e["venue"]["name"])
    if (e.get("price") or {}).get("free"):
        parts.append("free")
    return _cut("• " + " · ".join(parts))


def drive_item(e):
    where = AREA_NAMES.get(e["area"], "nearby")
    return _cut(f"• {fmt_time(e)} {e['title']} ({where}, {e['drive']})" if e.get("drive")
                else f"• {fmt_time(e)} {e['title']} ({where})")


def header(day, wx):
    d = date.fromisoformat(day)
    when = f"{d:%A}, {d:%b} {d.day}"
    if not wx or wx.get("high") is None or wx.get("low") is None:
        return f"📅 {when}"
    return f"{wx['emoji']} {when} · {round(wx['low'])}° → {round(wx['high'])}°, {wx['summary'].lower()}"


def _also_rank(e):
    return ("21+" in e["hints"], not (e.get("price") or {}).get("free"),
            "all-ages" not in e["hints"], "daytime" not in e["hints"], e["start"])


def build(day, events, wx, places, guide, page_url=PAGE_URL, visitors=None):
    todays = [e for e in events if on_day(e, day) and not e["ongoing"]]
    local = [e for e in todays if e["area"] in LOCAL_AREAS]
    little = sorted((e for e in local if e["tier"] == "little"), key=lambda e: e["start"])
    also = sorted((e for e in local if e["tier"] != "little"), key=_also_rank)
    drive = sorted((e for e in todays if e["area"] not in LOCAL_AREAS),
                   key=lambda e: (e["tier"] != "little", e["start"]))
    options = open_on(places or [], day) if len(little) < 3 else []
    text = ""
    for cap in range(PER_SECTION, 0, -1):
        text = _render(day, wx, little, also, drive, options, guide, page_url, cap, visitors)
        if len(text) <= LIMIT:
            return text
    footer = "\n" + _footer(page_url, visitors)
    return text[:LIMIT - len(footer) - 1] + "…" + footer


def visitors_line(visitors):
    return f"👀 Yesterday: {visitors} visitor{'' if visitors == 1 else 's'}"


def _footer(page_url, visitors):
    link = f"Full list → {page_url}"
    return link if visitors is None else f"{visitors_line(visitors)}\n{link}"


def _render(day, wx, little, also, drive, options, guide, page_url, cap, visitors=None):
    lines = [header(day, wx)]
    if not (little or also or drive):
        lines.append("Nothing listed for today yet.")
    if little:
        lines += ["👶 For little ones"] + [item(e) for e in little[:cap]]
    if also:
        lines += ["🎟️ Also today"] + [item(e) for e in also[:cap]]
    if drive:
        lines += ["🚗 Worth the drive"] + [drive_item(e) for e in drive[:cap]]
    if options:
        names = [p["name"] if h == "dawn-dusk" else f"{p['name']} {short_hours(h)}" for p, h in options[:cap]]
        lines.append("🏠 Always an option: " + " · ".join(names))
    if guide:
        lines.append(f"📖 Loving Reno: {guide.get('shortTitle') or guide['title']}")
    lines.append(_footer(page_url, visitors))
    return "\n".join(lines)


def post(webhook_url, text):
    """Send the message. True when Discord accepted it."""
    if not webhook_url:
        return False
    sep = "&" if "?" in webhook_url else "?"
    try:
        # retries=0: net would retry 5xx/network errors, which could post twice;
        # a failed post is retried by the next hourly run.
        status = net.post_json(f"{webhook_url}{sep}wait=true",
                               {"content": text, "allowed_mentions": {"parse": []}, "flags": 4},
                               label="discord webhook", retries=0)
    except net.FetchError as err:
        print(f"digest: {err}")
        return False
    return 200 <= status < 300
