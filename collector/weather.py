"""Open-Meteo forecast for Reno (no key): daily high/low and summary, hourly
temperature and rain chance, and the "nice outside" windows."""

import net
from model import utc

URL = ("https://api.open-meteo.com/v1/forecast?latitude=39.5296&longitude=-119.8138"
       "&daily=temperature_2m_max,temperature_2m_min,weather_code,precipitation_probability_max,sunrise,sunset"
       "&hourly=temperature_2m,precipitation_probability,weather_code,is_day"
       "&temperature_unit=fahrenheit&timezone=America%2FLos_Angeles&forecast_days=8")
NICE_LOW, NICE_HIGH, NICE_RAIN = 55, 85, 30      # °F, °F, % chance (spec)
MIN_NICE_HOURS = 2

# (highest WMO code, summary, emoji)
CODES = [(0, "Clear", "☀️"), (1, "Mostly clear", "🌤️"), (2, "Partly cloudy", "⛅"), (3, "Cloudy", "☁️"),
         (48, "Fog", "🌫️"), (57, "Drizzle", "🌦️"), (67, "Rain", "🌧️"), (77, "Snow", "🌨️"),
         (82, "Showers", "🌦️"), (86, "Snow showers", "🌨️"), (99, "Thunderstorms", "⛈️")]


def describe(code):
    for top, text, emoji in CODES:
        if code is not None and code <= top:
            return text, emoji
    return "Unknown", "🌡️"


def nice_windows(hours):
    """Runs of at least MIN_NICE_HOURS daylight hours that are mild and dry."""
    runs, current = [], []
    for h in hours + [None]:                       # None flushes the last run
        ok = (h is not None and h["day"] and h["t"] is not None and NICE_LOW <= h["t"] <= NICE_HIGH
              and h["rain"] is not None and h["rain"] < NICE_RAIN)
        if ok:
            current.append(h["h"])
            continue
        if len(current) >= MIN_NICE_HOURS:
            runs.append(current)
        current = []
    return [{"from": f"{r[0]:02d}:00", "to": f"{r[-1] + 1:02d}:00"} for r in runs]


def _round(v):
    return None if v is None else round(v)


def parse(payload, now):
    daily, hourly = payload["daily"], payload["hourly"]
    by_day = {}
    for i, stamp in enumerate(hourly["time"]):
        by_day.setdefault(stamp[:10], []).append({
            "h": int(stamp[11:13]), "t": _round(hourly["temperature_2m"][i]),
            "rain": hourly["precipitation_probability"][i], "day": bool(hourly["is_day"][i]),
        })
    days = []
    for i, day in enumerate(daily["time"]):
        code = daily["weather_code"][i]
        summary, emoji = describe(code)
        hours = by_day.get(day, [])
        days.append({
            "date": day, "high": _round(daily["temperature_2m_max"][i]),
            "low": _round(daily["temperature_2m_min"][i]), "summary": summary, "emoji": emoji,
            "code": code, "rain": daily["precipitation_probability_max"][i],
            "sunrise": (daily["sunrise"][i] or "")[11:16], "sunset": (daily["sunset"][i] or "")[11:16],
            "nice": nice_windows(hours),
            "hours": [{"h": h["h"], "t": h["t"], "rain": h["rain"]} for h in hours],
        })
    return {"generatedAt": utc(now), "days": days}


def fetch(now):
    data = net.get_json(URL)
    try:
        return parse(data, now)
    except (KeyError, IndexError, TypeError) as err:
        raise net.FetchError("open-meteo", f"unexpected response: {err!r}") from None
