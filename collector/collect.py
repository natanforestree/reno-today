#!/usr/bin/env python3
"""Reno Today collector. Runs hourly; decides whether to refresh and whether
to send the morning digest (docs/superpowers/specs/2026-10-05-reno-today-design.md)."""

import os
import sys
import traceback
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import classify  # noqa: E402
import dedupe  # noqa: E402
import digest  # noqa: E402
import guide  # noqa: E402
import model  # noqa: E402
import net  # noqa: E402
import schedule  # noqa: E402
import sources  # noqa: E402
import weather  # noqa: E402
from sources.base import Context, SourceError  # noqa: E402
from store import Store  # noqa: E402

ROOT = os.path.dirname(HERE)
VISITS_URL = "https://ruby-radar.nathanforestlee.workers.dev/api/visits/reno-today?days=2"


def _error_text(err):
    if isinstance(err, (net.FetchError, SourceError)):
        return str(err)
    traceback.print_exception(err)
    return f"collector error: {type(err).__name__}"


def _brief(err):
    """An error for the log without its traceback: our own errors are already safe
    to print; anything else shows only its type, as its message may hold a URL."""
    return str(err) if isinstance(err, (net.FetchError, SourceError)) else type(err).__name__


def _status(label, ok, count, last_success, error=None):
    return {"label": label, "ok": ok, "count": count, "lastSuccess": last_success, "error": error}


def collect_sources(srcs, ctx, store, now, previous):
    """Every source on its own; failures fall back to their last good events."""
    raw, status = [], {}
    for src in srcs:
        kept, at = store.last_good(src.NAME, now)
        every = getattr(src, "EVERY", None)
        if every and at is not None and now - at < every:
            raw += kept
            status[src.NAME] = _status(src.LABEL, True, len(kept), model.utc(at))
            continue
        try:
            got = src.fetch(ctx)
        except Exception as err:  # noqa: BLE001 - one broken source must not stop the rest
            message = _error_text(err)
            print(f"{src.NAME}: {message}")
            raw += kept
            last = model.utc(at) if at else (previous.get(src.NAME) or {}).get("lastSuccess")
            status[src.NAME] = _status(src.LABEL, False, len(kept), last, message)
            continue
        store.remember(src.NAME, [dict(e, _text=classify.cues(e.get("_text"))) for e in got], now)
        raw += got
        status[src.NAME] = _status(src.LABEL, True, len(got), model.utc(now))
    return raw, status


def build_events(raw, ctx, overrides):
    inside = [e for e in raw if model.in_window(e, ctx.start, ctx.end)]
    events = [classify.classify(e) for e in dedupe.dedupe(inside)]
    events = classify.apply_overrides(events, overrides)
    events.sort(key=lambda e: (e["start"], e["title"]))
    return [model.finalize(e) for e in events]


def _optional(name, label, fn, status, previous, now):
    """Weather and the guide: None on failure (the caller keeps the old file)."""
    try:
        value = fn()
    except Exception as err:  # noqa: BLE001
        message = _error_text(err)
        print(f"{name}: {message}")
        status[name] = _status(label, False, 0, (previous.get(name) or {}).get("lastSuccess"), message)
        return None
    status[name] = _status(label, True, 1 if value else 0, model.utc(now))
    return value


def yesterday_visitors(today):
    """Yesterday's page-visit count (a bare number, kept by the Ruby Radar worker), or None
    when it can't be had. Only the exception type is logged; this never stops the digest."""
    try:
        yesterday = (today - timedelta(days=1)).isoformat()
        body = net.get_json(VISITS_URL, label="visitor count", retries=0)
        count = next(d["count"] for d in body["days"] if d["day"] == yesterday)
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError("bad count")
        return count
    except Exception as err:  # noqa: BLE001
        print(f"visitor count: not available ({type(err).__name__})")
        return None


def run(root, now, env, srcs=None, post=None):
    store = Store(root)
    webhook = env.get("DISCORD_WEBHOOK_URL", "")
    decision = schedule.decide(now, store.last_refresh(), store.digest_date(),
                               digest_enabled=bool(webhook), force_digest=env.get("FORCE_DIGEST") == "true")
    if not decision.refresh:
        print(f"{now:%Y-%m-%d %H:%M}: nothing to do")
        return decision

    start, end = model.window(now)
    ctx = Context(start=start, end=end, env=env)
    previous = (store.read("docs/data/status.json") or {}).get("sources") or {}
    raw, status = collect_sources(sources.ALL if srcs is None else srcs, ctx, store, now, previous)
    any_source_ok = any(s["ok"] for s in status.values())     # event sources only, before the extras
    events = build_events(raw, ctx, classify.load_overrides(store.path("overrides.json")))

    card = _optional("lovingreno", "Loving Reno", guide.fetch, status, previous, now)
    if card is not None:
        store.write("docs/data/guide.json", card)
    else:
        card = store.read("docs/data/guide.json")
    if card and events:
        try:
            picks = guide.badges(events, card, guide.page_text(net.get_text(card["url"])))
            print(f"lovingreno: {picks} events are in the current guide")
        except Exception as err:  # noqa: BLE001 - decorative; must never cost the refresh
            print(f"lovingreno: badges skipped ({_brief(err)})")

    if events or any_source_ok:
        store.write("docs/data/events.json",
                    {"generatedAt": model.utc(now), "timezone": "America/Los_Angeles", "events": events})
    else:
        print("every source failed; keeping the previous events.json")
        events = (store.read("docs/data/events.json") or {}).get("events") or []

    wx = _optional("weather", "Weather (Open-Meteo)", lambda: weather.fetch(now), status, previous, now)
    if wx is not None:
        store.write("docs/data/weather.json", wx)
    else:
        wx = store.read("docs/data/weather.json")
    places = store.read("places.json", [])
    store.write("docs/data/places.json", places)
    store.write("docs/data/status.json", {"generatedAt": model.utc(now), "sources": status})
    store.set_last_refresh(now)
    print(f"{now:%Y-%m-%d %H:%M}: {len(events)} events; "
          + ", ".join(f"{k} {'ok' if v['ok'] else 'FAILED'}" for k, v in status.items()))

    if decision.digest:
        today = now.date().isoformat()
        try:
            day_wx = next((d for d in (wx or {}).get("days", []) if d.get("date") == today), None)
            visitors = yesterday_visitors(now.date())
            sent = (post or digest.post)(
                webhook, digest.build(today, events, day_wx, places, card, visitors=visitors))
        except Exception as err:  # noqa: BLE001 - the data is written; only the type, the webhook may be in the message
            print(f"digest not sent ({type(err).__name__})")
            sent = False
        if sent:
            store.set_digest_date(today)
            print("digest sent")
        else:
            print("digest not sent; the next hourly run will try again (until 10:59)")
    return decision


def main():
    run(ROOT, datetime.now(model.LA), dict(os.environ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
