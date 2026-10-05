#!/usr/bin/env python3
"""Reno Today collector. Runs hourly; decides whether to refresh and whether
to send the morning digest (docs/superpowers/specs/2026-10-05-reno-today-design.md)."""

import os
import sys
import traceback
from datetime import datetime

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


def _error_text(err):
    if isinstance(err, (net.FetchError, SourceError)):
        return str(err)
    traceback.print_exception(err)
    return f"collector error: {type(err).__name__}"


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
    events = build_events(raw, ctx, classify.load_overrides(store.path("overrides.json")))
    if events or any(s["ok"] for s in status.values()):
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
    card = _optional("lovingreno", "Loving Reno", guide.fetch, status, previous, now)
    if card is not None:
        store.write("docs/data/guide.json", card)
    else:
        card = store.read("docs/data/guide.json")
    places = store.read("places.json", [])
    store.write("docs/data/places.json", places)
    store.write("docs/data/status.json", {"generatedAt": model.utc(now), "sources": status})
    store.set_last_refresh(now)
    print(f"{now:%Y-%m-%d %H:%M}: {len(events)} events; "
          + ", ".join(f"{k} {'ok' if v['ok'] else 'FAILED'}" for k, v in status.items()))

    if decision.digest:
        today = now.date().isoformat()
        day_wx = next((d for d in (wx or {}).get("days", []) if d.get("date") == today), None)
        text = digest.build(today, events, day_wx, places, card)
        if (post or digest.post)(webhook, text):
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
