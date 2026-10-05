"""Reno Aces home games: MLB Stats API (Triple-A, sportId 11), no key."""

from datetime import date, datetime, timedelta

import net
from model import make_event, venue
from sources.base import SourceError

NAME = "aces"
LABEL = "Reno Aces"
URL = ("https://statsapi.mlb.com/api/v1/schedule?sportId=11&teamId=2310"
       "&startDate={start}&endDate={end}")
TEAM_ID = 2310
SKIP_STATES = {"cancelled", "postponed"}
BALLPARK = venue("Greater Nevada Field", "250 Evans Ave, Reno, NV 89501", 39.5281, -119.8086)


def fetch(ctx):
    last = (ctx.end - timedelta(days=1)).date().isoformat()
    data = net.get_json(URL.format(start=ctx.start.date().isoformat(), end=last))
    if not isinstance(data, dict) or not isinstance(data.get("dates"), list):
        raise SourceError("unexpected response (no dates)")
    return parse(data)


def parse(data):
    events = []
    for day in data.get("dates") or []:
        for g in day.get("games") or []:
            teams = g.get("teams") or {}
            home = (teams.get("home") or {}).get("team") or {}
            away = (teams.get("away") or {}).get("team") or {}
            status = g.get("status") or {}
            if home.get("id") != TEAM_ID or (status.get("detailedState") or "").lower() in SKIP_STATES:
                continue
            tbd = bool(status.get("startTimeTBD"))
            try:
                start = (date.fromisoformat(g.get("officialDate") or day["date"]) if tbd
                         else datetime.fromisoformat(g["gameDate"].replace("Z", "+00:00")))
            except (KeyError, TypeError, ValueError):
                continue
            name = (g.get("venue") or {}).get("name")
            events.append(make_event(
                "aces", str(g.get("gamePk")), f"Reno Aces vs {away.get('name') or 'TBA'}", start,
                all_day=tbd, venue=BALLPARK if name in (None, "Greater Nevada Field") else venue(name, "Reno, NV"),
                city="Reno", url=f"https://www.milb.com/gameday/{g.get('gamePk')}",
                tags=["sports", "baseball"], all_ages=True, outdoor=True, kind="organiser"))
    return events
