# Reno Today Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A cozy pixel-art page plus a 7:xx am Discord message listing everything happening in the Reno area each day, with things you can bring a one-year-old to listed first.

**Architecture:** A Python standard-library collector (`collector/`) runs hourly in GitHub Actions. The Cloudflare Worker that already times Ruby Radar dispatches it on its `:30` tick. Each run decides whether to refresh (every ~3 h) and whether to send the morning digest. A refresh pulls each source independently, then normalises, de-duplicates, classifies and applies hand overrides. It writes JSON to `docs/data/` and commits it. GitHub Pages serves `docs/`: plain JavaScript, no build step. The page reads the data straight from the repo's raw files first, so a stuck Pages deploy can't make it stale (the problem Ruby Radar hit on 2026-10-05).

**Tech Stack:** Python 3.12 stdlib (`urllib`, `zoneinfo`, `json`, `xml.etree`, `unittest`), GitHub Actions, GitHub Pages, plain ES modules plus `node --test` (Node 22), Aseprite Lua scripts, and the existing Cloudflare Worker (`natanforestree/finals-radar/worker/`).

**Spec:** `docs/superpowers/specs/2026-10-05-reno-today-design.md`. Read it before starting any task. Where this plan and the spec differ, this plan wins; every difference is listed under "Deliberate differences from the spec" below.

## Global Constraints

- The collector uses the **Python standard library only**: no `pip install`, no `requirements.txt`. Times use `America/Los_Angeles` via `zoneinfo`.
- **Window:** the next 8 days (today + 7), local Reno dates.
- **Refresh rule:** "full refresh if the last one was ≥ 2 h 50 min ago, otherwise exit without committing".
- **Digest rule:** "from 07:00 local, if today's digest hasn't been sent: full refresh, then post the Discord digest, then record the date in `state/digest.json`". The date is recorded only on success. "after 10:59 it gives up for the day".
- **Discord:** the message is "plain message content (≤ 2,000 chars, trimmed to fit)", with "up to 5 items per section, and empty sections are skipped". "Always an option" appears when there are fewer than 3 little-ones events.
- **"Nice outside":** 55–85°F, rain chance < 30 %, daylight.
- **Merging duplicates:** same local date, starts within 30 minutes, and either token overlap ≥ 0.8 or the same venue with overlap ≥ 0.6.
- **Being a polite client:**
  - Identify ourselves with a User-Agent that includes the repo URL.
  - Send at most a few requests per source per refresh.
  - Respect `robots.txt`.
  - Skip sites that block programs.
- **Facts only:** "Store and show only facts (name, time, place, price, link). Never copy write-ups."
  - Descriptions are used in memory for classification and are **never** written to `docs/data/`.
  - From Loving Reno we store only titles and URLs.
  - Last-good results in `state/sources/` (committed to the public repo) keep `_text` reduced to `classify.cues(...)`, the matched keywords only. Real recordings in `tests/fixtures/real/` reduce description fields the same way.
- **Secrets:**
  - `TICKETMASTER_KEY` and `DISCORD_WEBHOOK_URL` live only in repo secrets.
  - They never appear in committed files, `status.json` error text or logs. `net.FetchError` strips query strings and accepts a `label` for this.
  - Values move via the clipboard after a prefix check, then the clipboard is cleared (the Ruby Radar lesson).
- **Page:**
  - Phone first, checked at 390 px and 1280 px.
  - Plain JS, no build step. "All text from data is escaped".
  - Only `http(s)` links are rendered.
  - It must work with an empty or partial `events.json`.
- **Page assets:** external stylesheets only from Google Fonts, and no external scripts.
- **Repos:**
  - New **public** repo `natanforestree/reno-today`, with Pages from `main` `/docs`.
  - The Worker lives in `natanforestree/finals-radar/worker/`.
  - The island lives in `natanforestree/arcadipelago` (local `~/Documents/code/games`).
- **Commits:** every commit message ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. The commit commands below show only the first line; add the trailer each time (`git commit -m "…" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"`).
- **Test commands** (run from the repo root):
  - Python: `python3 -m unittest discover -s tests -v`
  - Page logic: `npm test`
  - Worker: `cd ~/Documents/code/finals-radar/worker && npm test`
  - Arcadipelago: `cd ~/Documents/code/games/site && npm test`
- **Things Nathan does himself** (Claude never creates accounts, types passwords or clicks credential-generation buttons):
  - creating the Ticketmaster developer account and key
  - creating the Discord webhook
  - editing the GitHub fine-grained token

## Deliberate differences from the spec

1. **Pipeline order:** the spec's diagram has normalise → classify → dedupe. This plan runs normalise → **dedupe → classify** → overrides. A merged event is then classified once, from the union of both listings' facts, which gives the same result with less code.
2. **Digest times:** the digest shows `10:30am` / `1:05pm` instead of the spec example's bare `10:30` / `1:05`. Without am/pm, "1:05" is ambiguous.
3. **Worth the drive** in the digest is always a header plus bullets (up to 5), like the other sections. The spec example shows a single inline item. Each bullet starts with the time and names the **area** (e.g. `• 11am Lake Tahoe Oktoberfest (Lake Tahoe, ~55 min)`), not the town, because events carry an area, not a town.
4. **`guide.json`** also stores `shortTitle`: the title up to its first colon. Loving Reno titles run to 200+ characters.
5. **The page reads `docs/data/` from `raw.githubusercontent.com` first**, falling back to the Pages copy. Data commits then show within ~5 min even when Pages builds fail (seen 2026-10-05).
6. **The workflow has a manual `force_digest` input** for testing the Discord message outside 07:00–10:59.
7. **Extra badges are left out:** the page shows hint badges for all ages / outdoors / 21+ only, because the card already shows the time and a "daytime" badge would be noise.
8. **Drive times:** the table is per town. The South Shore (Stateline ~70 min, South Lake Tahoe ~75 min) is longer than the spec's "Tahoe ~45–60", which fits the North Shore.
9. **Arcadipelago's minimum island width drops from 96 to 80 px.** With the Reno island ≤ 80 px wide, this is the smallest change that lets seven islands fit the landscape stage (Task 30).
10. **Multi-day events** show on every day they cover (page and digest) when they're all-day, ongoing or 20 h+ long. A Fri–Sun festival appears each day; a show ending at 1 am doesn't spill into the next day.
11. **"Everything else" has an "All day" group** before Morning / Afternoon / Evening / Late (spec lists the four timed groups). All-day events need a home; the group is hidden when empty.
12. **`places.json` fields:** `setting` is `indoor` | `outdoor` | `both` (the spec says indoor/outdoor), plus `free`, `address` and `checked` (the date the hours were verified).
13. **Loving Reno feed URL:** `/feeds/posts/summary` instead of `/feeds/posts/default`: same posts, without full post bodies (we only keep titles and URLs).
14. **`status.json`** also stores each source's `label` and a top-level `generatedAt`.
15. **Last-good results keep keyword cues, not descriptions** (`classify.cues`). The spec's "store only facts" applies to the committed `state/` files too; classification of reused events is unchanged.

## Review Focus

These are the inputs most likely to break the app for Nathan that the spec doesn't spell out. Each one has a test in the task that owns the code.

1. **A source answers 200 with an empty or reshaped body.** Ticketmaster omits `_embedded` when nothing matches, and Localist could drop `events`. "No matches" must count as a successful zero. A missing top-level key must count as a failure that keeps the last-good events.
   Tests: Task 10 (Ticketmaster: no `_embedded` → `[]`; no `page` → `SourceError`); Task 7 (UNR: no `events` → `SourceError`).
2. **Hostile or messy third-party text.** Examples: `<img onerror>` in a title, `javascript:` links, `@everyone` in a title posted to Discord.
   Tests: Task 2 (`make_event` drops non-http links); Task 18 (`esc`, `safeUrl`); Task 14 (`allowed_mentions` is empty).
3. **Someone viewing from another time zone, or late at night.** "Today" and every time shown must be Reno's, not the device's.
   Tests: Task 18 (`renoDate` at 23:30 Pacific and from a UTC clock; times read from the ISO offset).
4. **DST change days and refresh spacing across them.** On 2026-11-01, wall-clock subtraction would see 2 h where 3 h passed.
   Tests: Task 6 (elapsed time measured in UTC across fall-back); Task 2 (the window across the change has the right midnights).
5. **The Discord webhook deleted (404) or rate-limited (429).** The run must still write and commit data, must not record the digest date, and must retry next hour until 10:59.
   Tests: Task 14 (`post` returns False on 404); Task 15 (failed post → data written, date unset, the next hour retries).

## File structure

```
reno-today/
├── README.md                    what it is, how it runs, setup, how to add a source
├── package.json                 {"type":"module"} + `npm test` for the page logic (no deps)
├── .gitignore
├── overrides.json               hand corrections (tier / hide / addHint), starts as []
├── places.json                  "Always an option" list (phase 2), starts as []
├── collector/
│   ├── collect.py               entry point: decide → sources → build → write → digest
│   ├── net.py                   HTTP: User-Agent, gzip, timeout, one retry, redacted errors
│   ├── model.py                 event shape (make_event/finalize), time + area helpers
│   ├── ical.py                  minimal iCalendar reader
│   ├── classify.py              tier + hints rules, overrides
│   ├── dedupe.py                merge duplicates
│   ├── schedule.py              refresh/digest decision
│   ├── store.py                 JSON files: docs/data/, state/, last-good per source
│   ├── weather.py               Open-Meteo → weather.json
│   ├── guide.py                 Loving Reno guide card (+ badges in phase 3)
│   ├── places.py                which places are open on a day
│   ├── digest.py                Discord message build + post
│   └── sources/
│       ├── __init__.py          ALL = [ticketmaster, unr, wolfpack, aces, …]
│       ├── base.py              Context, SourceError
│       ├── ticketmaster.py
│       ├── unr.py
│       ├── wolfpack.py
│       └── aces.py              (phase 2 adds more modules here)
├── tests/
│   ├── helpers.py               puts collector/ on sys.path, fixture loaders, la()
│   ├── fixtures/                small hand-made fixtures shaped like real responses
│   ├── fixtures/real/           real responses recorded during the build (invariant tests)
│   ├── test_*.py                one per collector module
│   └── page/lib.test.js         node --test for docs/lib.js
├── docs/
│   ├── index.html  style.css  app.js  lib.js
│   ├── art/arch.png  art/favicon.png
│   └── data/                    events.json weather.json status.json guide.json places.json
├── state/                       refresh.json digest.json sources/<name>.json (committed)
├── art/                         lib.lua arch.lua favicon.lua (+ .aseprite outputs)
├── dev/make_fixture.py          page fixtures: full / empty / partial / failing
└── .github/workflows/
    ├── collect.yml              hourly collector (dispatched by the Worker)
    └── test.yml                 unit tests on code pushes
```

**Event dict:** this is the contract between the collector modules. `model.make_event` builds it; every module after that reads and writes these keys:

```python
{
  "id": "unr:53622698677071",          # "<source>:<stable id>"
  "title": str, "start": "2026-10-10T10:30:00-07:00", "end": str | None,
  "allDay": bool, "ongoing": bool,
  "venue": {"name": str|None, "address": str|None, "lat": float|None, "lon": float|None} | None,
  "area": "reno"|"sparks"|"tahoe"|"carson"|"virginia-city"|"other", "drive": str|None,
  "price": {"free": True} | {"min": float, "max": float} | None,
  "tier": "little"|"general", "hints": [ "all-ages"|"outdoors"|"daytime"|"21+" ],
  "links": [{"source": str, "url": str}], "lovingReno": {"title", "url"} | None,
  # private (dropped by model.finalize before writing docs/data/events.json):
  "_text": str, "_tags": [str], "_family": bool, "_adult": bool,
  "_allAges": bool, "_outdoor": bool, "_kind": "organiser"|"ticketing",
}
```

All-day events have `start` at local midnight. For an all-day event, `end` is midnight at the start of its **last** day, or `None`.

---

# Phase 1: Core

### Task 1: Repo scaffold, test harness and `net.py`

**Files:**
- Create: `README.md`, `.gitignore`, `package.json`, `overrides.json`, `places.json`, `collector/net.py`, `tests/helpers.py`, `tests/test_net.py`

**Interfaces:**
- Produces:
  - `net.UA` (str containing `github.com/natanforestree/reno-today`)
  - `net.FetchError(where, message, status=None)`, with `.status` (int or None)
  - `net.request(url, *, data=None, headers=None, method=None, timeout=20, retries=1, label=None) -> (status, bytes)`
  - `net.get_bytes / get_text / get_json(url, **kw)`
  - `net.post_json(url, payload, **kw) -> status`
  - `net.RETRY_PAUSE` (seconds; tests set it to 0)
  - `tests/helpers.py`: `fixture_path(name)`, `fixture_text(name)`, `fixture_json(name)`, `la(y, m, d, hh=0, mm=0)`, `LA`

The local repo already exists at `/Users/nathan/Documents/code/reno-today` (branch `main`, one commit with the spec). Work there.

- [ ] **Step 1: Write the scaffold files**

`.gitignore`:
```
__pycache__/
*.pyc
.DS_Store
*.tmp
dev/fixture/
node_modules/
```

`package.json`:
```json
{
  "name": "reno-today",
  "private": true,
  "type": "module",
  "description": "Reno Today page logic tests (no dependencies)",
  "scripts": {
    "test": "node --test \"tests/page/*.test.js\""
  }
}
```

`overrides.json` and `places.json` each contain `[]` and a newline.

`README.md` (later tasks extend it):
```markdown
# Reno Today

Everything happening in the Reno area each day, things you can bring a
toddler to first. Live at https://natanforestree.github.io/reno-today/ plus a
7:xx am Discord message.

- `collector/` (Python, standard library only) gathers events from each source,
  merges duplicates, classifies them and writes `docs/data/`.
- `.github/workflows/collect.yml` runs it hourly; the Cloudflare Worker in
  `natanforestree/finals-radar` (`worker/`) dispatches it on its :30 tick.
- `docs/` is the page (GitHub Pages, plain JavaScript).

Design: `docs/superpowers/specs/2026-10-05-reno-today-design.md`.

## Tests

    python3 -m unittest discover -s tests -v   # collector
    npm test                                   # page logic
```

`tests/helpers.py`:
```python
"""Shared test setup: puts collector/ on the import path, loads fixtures."""

import json
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "collector"))

LA = ZoneInfo("America/Los_Angeles")


def fixture_path(name):
    return os.path.join(HERE, "fixtures", name)


def fixture_text(name):
    with open(fixture_path(name), encoding="utf-8") as f:
        return f.read()


def fixture_json(name):
    return json.loads(fixture_text(name))


def la(y, m, d, hh=0, mm=0):
    """An aware America/Los_Angeles datetime."""
    return datetime(y, m, d, hh, mm, tzinfo=LA)
```

- [ ] **Step 2: Write the failing tests** `tests/test_net.py`

```python
import gzip
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import helpers  # noqa: F401  (puts collector/ on the path)
import net


class Handler(BaseHTTPRequestHandler):
    hits = {}
    posted = None
    posted_type = None

    def log_message(self, *args):
        pass

    def _send(self, status, body=b"", headers=()):
        self.send_response(status)
        for k, v in headers:
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        Handler.hits[path] = Handler.hits.get(path, 0) + 1
        if path == "/gzip":
            self._send(200, gzip.compress(b'{"ok": true}'), [("Content-Encoding", "gzip")])
        elif path == "/ua":
            self._send(200, self.headers.get("User-Agent", "").encode())
        elif path == "/flaky":
            self._send(503, b"oops") if Handler.hits[path] == 1 else self._send(200, b"fine")
        elif path.startswith("/missing"):
            self._send(404, b"nope")
        elif path == "/bad-json":
            self._send(200, b"{not json")
        else:
            self._send(500)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        Handler.posted = json.loads(self.rfile.read(length))
        Handler.posted_type = self.headers.get("Content-Type")
        self._send(204)


class NetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        net.RETRY_PAUSE = 0

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        Handler.hits = {}

    def test_decodes_gzip_json(self):
        self.assertEqual(net.get_json(self.base + "/gzip"), {"ok": True})

    def test_sends_our_user_agent(self):
        self.assertIn("github.com/natanforestree/reno-today", net.get_text(self.base + "/ua"))

    def test_retries_a_server_error_once(self):
        self.assertEqual(net.get_text(self.base + "/flaky"), "fine")
        self.assertEqual(Handler.hits["/flaky"], 2)

    def test_does_not_retry_a_client_error(self):
        with self.assertRaises(net.FetchError) as cm:
            net.get_text(self.base + "/missing")
        self.assertEqual(cm.exception.status, 404)
        self.assertEqual(Handler.hits["/missing"], 1)

    def test_bad_json_is_a_fetch_error(self):
        with self.assertRaises(net.FetchError):
            net.get_json(self.base + "/bad-json")

    def test_errors_never_include_the_query_string(self):
        with self.assertRaises(net.FetchError) as cm:
            net.get_text(self.base + "/missing?apikey=SECRET123")
        self.assertNotIn("SECRET123", str(cm.exception))
        self.assertIn("HTTP 404", str(cm.exception))

    def test_label_replaces_the_url_in_errors(self):
        with self.assertRaises(net.FetchError) as cm:
            net.get_text(self.base + "/missing/token-in-path", label="discord webhook")
        self.assertNotIn("token-in-path", str(cm.exception))
        self.assertIn("discord webhook", str(cm.exception))

    def test_unreachable_host_is_a_fetch_error(self):
        with self.assertRaises(net.FetchError) as cm:
            net.get_text("http://127.0.0.1:9/", timeout=2)
        self.assertIsNone(cm.exception.status)

    def test_post_json(self):
        self.assertEqual(net.post_json(self.base + "/hook", {"content": "hi"}), 204)
        self.assertEqual(Handler.posted, {"content": "hi"})
        self.assertEqual(Handler.posted_type, "application/json")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the tests to make sure they fail**

Run: `python3 -m unittest discover -s tests -v`
Expected: ERROR `ModuleNotFoundError: No module named 'net'`

- [ ] **Step 4: Implement** `collector/net.py`

The module is named `net`, not `http`, so it doesn't shadow the standard library's `http` package that `urllib` uses.

```python
"""HTTP for the collector: our User-Agent, gzip, a timeout and one retry.

Errors name the host and path but never the query string (API keys live
there), and callers can pass `label` to hide the URL entirely (the Discord
webhook's token is in its path)."""

import gzip
import http.client
import json
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "reno-today/1.0 (+https://github.com/natanforestree/reno-today)"
TIMEOUT = 20
RETRY_PAUSE = 2.0


class FetchError(Exception):
    """A request that failed for good. `status` is the HTTP status, or None."""

    def __init__(self, where, message, status=None):
        super().__init__(f"{message} ({where})")
        self.status = status


def _where(url, label):
    if label:
        return label
    parts = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def request(url, *, data=None, headers=None, method=None, timeout=TIMEOUT, retries=1, label=None):
    """(status, body bytes). Network errors and 5xx are retried once; 4xx fail at once."""
    sent = {"User-Agent": UA, "Accept-Encoding": "gzip"}
    sent.update(headers or {})
    where = _where(url, label)
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=data, headers=sent, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as res:
                body = res.read()
                if res.headers.get("Content-Encoding") == "gzip":
                    body = gzip.decompress(body)
                return res.status, body
        except urllib.error.HTTPError as err:
            if err.code < 500 or attempt == retries:
                raise FetchError(where, f"HTTP {err.code}", err.code) from None
        except (urllib.error.URLError, http.client.HTTPException, TimeoutError, ConnectionError, OSError) as err:
            if attempt == retries:
                reason = getattr(err, "reason", None) or type(err).__name__
                raise FetchError(where, f"network error: {reason}") from None
        time.sleep(RETRY_PAUSE)
    raise AssertionError("unreachable")


def get_bytes(url, **kw):
    return request(url, **kw)[1]


def get_text(url, **kw):
    return get_bytes(url, **kw).decode("utf-8", errors="replace")


def get_json(url, **kw):
    body = get_bytes(url, **kw)
    try:
        return json.loads(body)
    except ValueError as err:
        raise FetchError(_where(url, kw.get("label")), f"bad JSON: {err}") from None


def post_json(url, payload, **kw):
    """POST a JSON body; returns the HTTP status (FetchError on 4xx/5xx)."""
    data = json.dumps(payload).encode("utf-8")
    return request(url, data=data, headers={"Content-Type": "application/json"},
                   method="POST", **kw)[0]
```

- [ ] **Step 5: Run the tests to make sure they pass**

Run: `python3 -m unittest discover -s tests -v`
Expected: 9 tests, OK

- [ ] **Step 6: Commit**

```bash
git add .gitignore package.json README.md overrides.json places.json collector/net.py tests/helpers.py tests/test_net.py
git commit -m "Collector scaffold: test harness and HTTP helper"
```

---

### Task 2: `model.py` (event shape, time and area helpers)

**Files:**
- Create: `collector/model.py`, `tests/test_model.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - Constants: `LA`, `DAYS = 8`, `LOCAL_AREAS = ("reno", "sparks")`, `FREE = {"free": True}`
  - Time: `window(now) -> (start, end)`, `day_start(date)`, `iso(dt) -> str`, `utc(dt) -> "…Z"`
  - Places: `area_for(city)`, `drive_for(city, area)`, `city_from_address(address, default=None)`
  - Values: `plain(html) -> str`, `venue(name=None, address=None, lat=None, lon=None) -> dict | None`, `price_range(low, high) -> dict | None`
  - Events: `make_event(source, source_id, title, start, *, end=None, all_day=False, ongoing=False, venue=None, city=None, price=None, url=None, text="", tags=(), family=False, adult=False, all_ages=False, outdoor=False, kind="organiser") -> event dict`, `finalize(event) -> dict` (without `_` keys)
  - Dates: `local_date(event)`, `end_date(event)`, `in_window(event, start, end) -> bool`

- [ ] **Step 1: Write the failing tests** `tests/test_model.py`

```python
import unittest
from datetime import date, datetime, timezone

from helpers import la
import model


class WindowTest(unittest.TestCase):
    def test_today_through_seven_days_ahead(self):
        start, end = model.window(la(2026, 10, 5, 8, 15))
        self.assertEqual(model.iso(start), "2026-10-05T00:00:00-07:00")
        self.assertEqual(model.iso(end), "2026-10-13T00:00:00-07:00")

    def test_window_across_the_dst_change_keeps_local_midnights(self):
        start, end = model.window(la(2026, 10, 28, 23, 59))
        self.assertEqual(model.iso(start), "2026-10-28T00:00:00-07:00")
        self.assertEqual(model.iso(end), "2026-11-05T00:00:00-08:00")

    def test_utc(self):
        self.assertEqual(model.utc(la(2026, 10, 10, 7, 30)), "2026-10-10T14:30:00Z")


class AreaTest(unittest.TestCase):
    def test_local_areas_have_no_drive(self):
        self.assertEqual(model.area_for("Reno"), "reno")
        self.assertEqual(model.area_for(" sparks "), "sparks")
        self.assertIsNone(model.drive_for("Reno", "reno"))

    def test_day_trips(self):
        self.assertEqual(model.area_for("Stateline"), "tahoe")
        self.assertEqual(model.drive_for("Stateline", "tahoe"), "~70 min")
        self.assertEqual(model.area_for("Carson City"), "carson")
        self.assertEqual(model.drive_for("Carson City", "carson"), "~35 min")
        self.assertEqual(model.area_for("Virginia City"), "virginia-city")

    def test_city_from_address(self):
        self.assertEqual(model.city_from_address("561 Crystal Park Road, Verdi, NV 89439"), "Verdi")
        self.assertEqual(model.city_from_address("1 Main St, South Lake Tahoe, CA"), "South Lake Tahoe")
        self.assertEqual(model.area_for(model.city_from_address("561 Crystal Park Road, Verdi, NV 89439")), "reno")
        self.assertIsNone(model.city_from_address("Idlewild Park"))
        self.assertEqual(model.city_from_address("Idlewild Park", "Reno"), "Reno")

    def test_unknown_city_is_other(self):
        self.assertEqual(model.area_for("Sacramento"), "other")
        self.assertEqual(model.area_for(None), "other")
        self.assertIsNone(model.drive_for("Sacramento", "other"))
        self.assertEqual(model.drive_for("Fernley", "other"), "~35 min")


class ValuesTest(unittest.TestCase):
    def test_plain_strips_tags_and_entities(self):
        self.assertEqual(model.plain("<p>Kids &amp; <b>families</b></p>\n welcome"),
                         "Kids & families welcome")

    def test_price_range(self):
        self.assertEqual(model.price_range(0, 0), {"free": True})
        self.assertEqual(model.price_range(25, 60), {"min": 25.0, "max": 60.0})
        self.assertEqual(model.price_range(25, None), {"min": 25.0, "max": 25.0})
        self.assertIsNone(model.price_range(None, None))

    def test_venue(self):
        self.assertEqual(model.venue("GSR", "2500 E 2nd St", "39.52321", "-119.7762"),
                         {"name": "GSR", "address": "2500 E 2nd St", "lat": 39.52321, "lon": -119.7762})
        self.assertIsNone(model.venue("", "  "))
        self.assertEqual(model.venue(None, "Reno, NV")["lat"], None)


class MakeEventTest(unittest.TestCase):
    def test_timed_event_is_written_in_reno_time(self):
        e = model.make_event("tm", "abc", "  Big   Show ", datetime(2026, 10, 11, 2, 30, tzinfo=timezone.utc),
                             city="Reno", url="https://example.com/x")
        self.assertEqual(e["id"], "tm:abc")
        self.assertEqual(e["title"], "Big Show")
        self.assertEqual(e["start"], "2026-10-10T19:30:00-07:00")
        self.assertIsNone(e["end"])
        self.assertFalse(e["allDay"])
        self.assertEqual(e["area"], "reno")
        self.assertEqual(e["links"], [{"source": "tm", "url": "https://example.com/x"}])
        self.assertEqual(e["tier"], "general")
        self.assertEqual(e["hints"], [])

    def test_all_day_uses_local_midnight(self):
        e = model.make_event("wolfpack", "1", "Game", date(2026, 11, 2), all_day=True, city="Reno")
        self.assertEqual(e["start"], "2026-11-02T00:00:00-08:00")
        self.assertTrue(e["allDay"])

    def test_end_before_start_is_dropped(self):
        e = model.make_event("x", "1", "T", la(2026, 10, 10, 12), end=la(2026, 10, 10, 11), city="Reno")
        self.assertIsNone(e["end"])

    def test_long_runs_are_ongoing(self):
        e = model.make_event("x", "1", "Exhibit", la(2026, 10, 1, 10), end=la(2026, 11, 20, 17), city="Reno")
        self.assertTrue(e["ongoing"])
        short = model.make_event("x", "2", "Fest", la(2026, 10, 9, 10), end=la(2026, 10, 11, 17), city="Reno")
        self.assertFalse(short["ongoing"])

    def test_only_http_links_are_kept(self):
        for bad in ("javascript:alert(1)", "data:text/html,hi", "", None, "ftp://x"):
            e = model.make_event("x", "1", "T", la(2026, 10, 10, 12), city="Reno", url=bad)
            self.assertEqual(e["links"], [], bad)

    def test_tags_are_lower_case_and_sorted(self):
        e = model.make_event("x", "1", "T", la(2026, 10, 10, 12), city="Reno", tags=["Family", " Music ", "", None])
        self.assertEqual(e["_tags"], ["family", "music"])

    def test_finalize_drops_private_fields(self):
        e = model.make_event("x", "1", "T", la(2026, 10, 10, 12), city="Reno", text="secret write-up")
        out = model.finalize(e)
        self.assertFalse([k for k in out if k.startswith("_")])
        self.assertNotIn("secret write-up", str(out))


class InWindowTest(unittest.TestCase):
    def setUp(self):
        self.start, self.end = model.window(la(2026, 10, 5, 9))

    def test_inside_and_outside(self):
        inside = model.make_event("x", "1", "T", la(2026, 10, 12, 20), city="Reno")
        before = model.make_event("x", "2", "T", la(2026, 10, 4, 20), city="Reno")
        after = model.make_event("x", "3", "T", la(2026, 10, 13, 0), city="Reno")
        self.assertTrue(model.in_window(inside, self.start, self.end))
        self.assertFalse(model.in_window(before, self.start, self.end))
        self.assertFalse(model.in_window(after, self.start, self.end))

    def test_exhibit_that_started_earlier_but_runs_through_today(self):
        e = model.make_event("x", "1", "Exhibit", la(2026, 8, 1, 10), end=la(2026, 11, 1, 17), city="Reno")
        self.assertTrue(model.in_window(e, self.start, self.end))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run them to make sure they fail**

Run: `python3 -m unittest discover -s tests -p test_model.py -v` (from the repo root)
Expected: `ModuleNotFoundError: No module named 'model'`

- [ ] **Step 3: Implement** `collector/model.py`

```python
"""The event shape every source produces, and the time and place helpers they
share. The public fields are the spec's "Data" section; fields starting with
"_" are for classification and merging only and never reach docs/data/."""

import html
import re
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

LA = ZoneInfo("America/Los_Angeles")
DAYS = 8                                # today + 7
ONGOING_AFTER = timedelta(days=3)       # longer than this is an exhibit or a run
LOCAL_AREAS = ("reno", "sparks")
FREE = {"free": True}

# Lower-case city -> area. Anything not listed is "other".
CITY_AREAS = {
    "reno": "reno", "sparks": "sparks", "verdi": "reno",   # Verdi is 15 min out: local
    "carson city": "carson", "virginia city": "virginia-city",
    "stateline": "tahoe", "south lake tahoe": "tahoe", "incline village": "tahoe",
    "crystal bay": "tahoe", "kings beach": "tahoe", "tahoe vista": "tahoe",
    "tahoe city": "tahoe", "olympic valley": "tahoe", "truckee": "tahoe",
    "homewood": "tahoe", "zephyr cove": "tahoe",
}
# Rough drive from downtown Reno.
DRIVE = {
    "carson city": "~35 min", "virginia city": "~40 min", "truckee": "~35 min",
    "incline village": "~45 min", "crystal bay": "~45 min", "kings beach": "~50 min",
    "tahoe vista": "~50 min", "olympic valley": "~50 min", "tahoe city": "~55 min",
    "homewood": "~60 min", "zephyr cove": "~65 min", "stateline": "~70 min",
    "south lake tahoe": "~75 min", "fernley": "~35 min", "dayton": "~35 min",
    "minden": "~50 min", "gardnerville": "~55 min", "fallon": "~65 min",
    "washoe valley": "~25 min", "new washoe city": "~25 min",
}
AREA_DRIVE = {"carson": "~35 min", "virginia-city": "~40 min", "tahoe": "~45–75 min"}


def area_for(city):
    return CITY_AREAS.get((city or "").strip().lower(), "other")


def drive_for(city, area):
    if area in LOCAL_AREAS:
        return None
    return DRIVE.get((city or "").strip().lower()) or AREA_DRIVE.get(area)


def city_from_address(address, default=None):
    """'561 Crystal Park Rd, Verdi, NV 89439' -> 'Verdi' (the part before the state)."""
    parts = [p.strip() for p in (address or "").split(",") if p.strip()]
    for i, part in enumerate(parts):
        if i and re.fullmatch(r"(NV|Nev\.?|Nevada|CA|Calif\.?|California)( \d{5}(-\d{4})?)?", part, re.I):
            return parts[i - 1]
    return default


def day_start(d):
    """Midnight in Reno at the start of date d."""
    return datetime.combine(d, time(0), LA)


def window(now):
    """(start, end) of the days shown: today 00:00 to 8 days later, Reno time."""
    first = now.astimezone(LA).date()
    return day_start(first), day_start(first + timedelta(days=DAYS))


def iso(dt):
    return dt.astimezone(LA).isoformat(timespec="seconds")


def utc(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def plain(text):
    """HTML to one line of plain text."""
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", text or "")).split())


def _coord(value):
    try:
        return round(float(value), 5)
    except (TypeError, ValueError):
        return None


def venue(name=None, address=None, lat=None, lon=None):
    name, address = (name or "").strip() or None, (address or "").strip() or None
    if not (name or address):
        return None
    return {"name": name, "address": address, "lat": _coord(lat), "lon": _coord(lon)}


def price_range(low, high):
    """{"free": True} for 0–0, {"min", "max"} otherwise, None when unknown."""
    if low is None and high is None:
        return None
    low = high if low is None else low
    high = low if high is None else high
    if low == 0 and high == 0:
        return dict(FREE)
    return {"min": round(float(low), 2), "max": round(float(high), 2)}


def _as_date(value):
    return value.astimezone(LA).date() if isinstance(value, datetime) else value


def make_event(source, source_id, title, start, *, end=None, all_day=False, ongoing=False,
               venue=None, city=None, price=None, url=None, text="", tags=(),
               family=False, adult=False, all_ages=False, outdoor=False, kind="organiser"):
    """One normalised event. start/end are aware datetimes, or dates when all_day
    (end = the last day, inclusive). kind is "organiser" (the venue's or
    organiser's own feed) or "ticketing" (decides which listing wins on merge)."""
    if all_day:
        start = day_start(_as_date(start))
        end = day_start(_as_date(end)) if end else None
    else:
        start = start.astimezone(LA)
        end = end.astimezone(LA) if end else None
    if end is not None and end < start:
        end = None
    area = area_for(city)
    link = url.strip() if isinstance(url, str) and re.match(r"https?://", url.strip(), re.I) else None
    return {
        "id": f"{source}:{source_id}",
        "title": " ".join((title or "").split()),
        "start": iso(start),
        "end": iso(end) if end else None,
        "allDay": bool(all_day),
        "ongoing": bool(ongoing) or (end is not None and end - start > ONGOING_AFTER),
        "venue": venue,
        "area": area,
        "drive": drive_for(city, area),
        "price": price,
        "tier": "general",
        "hints": [],
        "links": [{"source": source, "url": link}] if link else [],
        "lovingReno": None,
        "_text": (text or "")[:2000],
        "_tags": sorted({t.strip().lower() for t in tags if t and t.strip()}),
        "_family": bool(family),
        "_adult": bool(adult),
        "_allAges": bool(all_ages),
        "_outdoor": bool(outdoor),
        "_kind": kind,
    }


def finalize(event):
    """The event as written to docs/data/events.json (no private fields)."""
    return {k: v for k, v in event.items() if not k.startswith("_")}


def local_date(event):
    return event["start"][:10]


def end_date(event):
    return (event["end"] or event["start"])[:10]


def in_window(event, start, end):
    """True if the event touches the days from start up to (not including) end."""
    first, last = start.date().isoformat(), (end - timedelta(days=1)).date().isoformat()
    return local_date(event) <= last and end_date(event) >= first
```

- [ ] **Step 4: Run them to make sure they pass**

Run: `python3 -m unittest discover -s tests -v`
Expected: all tests OK (Task 1's 9 + this task's 19)

- [ ] **Step 5: Commit**

```bash
git add collector/model.py tests/test_model.py
git commit -m "Event model: shape, Reno time, areas and drive times"
```

---

### Task 3: `ical.py` (minimal iCalendar reader)

**Files:**
- Create: `collector/ical.py`, `tests/test_ical.py`

**Interfaces:**
- Consumes: `model.LA`
- Produces:
  - `ical.events(text) -> iterator of dict NAME -> (params dict, raw value)`
  - `ical.text(ev, name) -> str` (unescaped)
  - `ical.when(prop) -> date | aware datetime | None`
  - `ical.unescape(s)`, `ical.unfold(text)`, `ical.parse_line(line)`

- [ ] **Step 1: Write the failing tests** `tests/test_ical.py`

```python
import unittest
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import helpers  # noqa: F401
import ical

FEED = (
    "BEGIN:VCALENDAR\r\nVERSION:2.0\r\n"
    "BEGIN:VEVENT\r\nUID:a1\r\nDTSTART:20261010T013000Z\r\nDTEND:20261010T033000Z\r\n"
    "LOCATION:Reno\\, Nev.\\, Mackay Stadium\r\n"
    "SUMMARY:A very long title that is folded\r\n  across two lines\r\n"
    "DESCRIPTION:Line one\\nLine two\\; with semicolon\\\\done\r\nEND:VEVENT\r\n"
    "BEGIN:VEVENT\r\nUID:a2\r\nDTSTART;VALUE=DATE:20261102\r\nSUMMARY:All day\r\nEND:VEVENT\r\n"
    "BEGIN:VEVENT\r\nUID:a3\r\nDTSTART;TZID=America/New_York:20261010T100000\r\nSUMMARY:East\r\nEND:VEVENT\r\n"
    "BEGIN:VEVENT\r\nUID:a4\r\nDTSTART:20261010T100000\r\nSUMMARY:Floating\r\nEND:VEVENT\r\n"
    "BEGIN:VEVENT\r\nUID:a5\r\nDTSTART;TZID=Pacific Standard Time:20261010T100000\r\nSUMMARY:Windows\r\nEND:VEVENT\r\n"
    "BEGIN:VEVENT\r\nUID:a6\r\nDTSTART:2026-10-10\r\nSUMMARY:Broken date\r\nEND:VEVENT\r\n"
    'BEGIN:VEVENT\r\nUID:a7\r\nATTENDEE;CN="Doe: Jane":mailto:j@example.com\r\nDTSTART:20261010\r\nEND:VEVENT\r\n'
    "END:VCALENDAR\r\n"
)
LA = ZoneInfo("America/Los_Angeles")


class IcalTest(unittest.TestCase):
    def setUp(self):
        self.evs = list(ical.events(FEED))

    def test_finds_every_event(self):
        self.assertEqual([ical.text(e, "UID") for e in self.evs], ["a1", "a2", "a3", "a4", "a5", "a6", "a7"])

    def test_unfolds_and_unescapes_text(self):
        e = self.evs[0]
        self.assertEqual(ical.text(e, "SUMMARY"), "A very long title that is folded across two lines")
        self.assertEqual(ical.text(e, "LOCATION"), "Reno, Nev., Mackay Stadium")
        self.assertEqual(ical.text(e, "DESCRIPTION"), "Line one\nLine two; with semicolon\\done")
        self.assertEqual(ical.text(e, "NOPE"), "")

    def test_utc_times(self):
        self.assertEqual(ical.when(self.evs[0].get("DTSTART")), datetime(2026, 10, 10, 1, 30, tzinfo=timezone.utc))

    def test_dates(self):
        self.assertEqual(ical.when(self.evs[1].get("DTSTART")), date(2026, 11, 2))
        self.assertEqual(ical.when(self.evs[6].get("DTSTART")), date(2026, 10, 10))

    def test_tzid_times(self):
        self.assertEqual(ical.when(self.evs[2].get("DTSTART")),
                         datetime(2026, 10, 10, 10, 0, tzinfo=ZoneInfo("America/New_York")))

    def test_floating_and_unknown_zones_mean_reno_time(self):
        self.assertEqual(ical.when(self.evs[3].get("DTSTART")), datetime(2026, 10, 10, 10, 0, tzinfo=LA))
        self.assertEqual(ical.when(self.evs[4].get("DTSTART")), datetime(2026, 10, 10, 10, 0, tzinfo=LA))

    def test_bad_or_missing_values_are_none(self):
        self.assertIsNone(ical.when(self.evs[5].get("DTSTART")))
        self.assertIsNone(ical.when(None))

    def test_quoted_parameter_with_a_colon(self):
        params, value = self.evs[6]["ATTENDEE"]
        self.assertEqual(params["CN"], "Doe: Jane")
        self.assertEqual(value, "mailto:j@example.com")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run them to make sure they fail**

Run: `python3 -m unittest discover -s tests -v`
Expected: `ModuleNotFoundError: No module named 'ical'`

- [ ] **Step 3: Implement** `collector/ical.py`

```python
"""Just enough iCalendar (RFC 5545) to read event feeds: VEVENT properties,
text unescaping, and DTSTART/DTEND as dates or aware datetimes. Recurrence
rules (RRULE) are not expanded; the feeds we use list each date."""

import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from model import LA


def unfold(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"\n[ \t]", "", text)


def unescape(value):
    out, i = [], 0
    while i < len(value):
        if value[i] == "\\" and i + 1 < len(value):
            nxt = value[i + 1]
            out.append("\n" if nxt in "nN" else nxt)
            i += 2
        else:
            out.append(value[i])
            i += 1
    return "".join(out)


def parse_line(line):
    """'DTSTART;TZID=X:20261010T103000' -> ('DTSTART', {'TZID': 'X'}, '20261010T103000')."""
    quoted = False
    for i, c in enumerate(line):
        if c == '"':
            quoted = not quoted
        elif c == ":" and not quoted:
            break
    else:
        return None
    name, *params = line[:i].split(";")
    found = {}
    for p in params:
        key, _, val = p.partition("=")
        found[key.upper()] = val.strip('"')
    return name.upper(), found, line[i + 1:]


def events(text):
    """Each VEVENT as {NAME: (params, value)}; for repeated names the last wins."""
    current = None
    for line in unfold(text).split("\n"):
        if line == "BEGIN:VEVENT":
            current = {}
        elif line == "END:VEVENT":
            if current is not None:
                yield current
            current = None
        elif current is not None:
            parsed = parse_line(line)
            if parsed:
                current[parsed[0]] = (parsed[1], parsed[2])


def when(prop):
    """A DTSTART/DTEND (params, value) as a date (all-day) or an aware datetime."""
    if not prop:
        return None
    params, value = prop
    value = value.strip()
    try:
        if params.get("VALUE") == "DATE" or re.fullmatch(r"\d{8}", value):
            return datetime.strptime(value, "%Y%m%d").date()
        if value.endswith("Z"):
            return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        naive = datetime.strptime(value, "%Y%m%dT%H%M%S")
    except ValueError:
        return None
    try:
        tz = ZoneInfo(params["TZID"]) if params.get("TZID") else LA
    except (ZoneInfoNotFoundError, ValueError):
        tz = LA
    return naive.replace(tzinfo=tz)


def text(ev, name):
    prop = ev.get(name)
    return unescape(prop[1]).strip() if prop else ""
```

- [ ] **Step 4: Run them to make sure they pass**

Run: `python3 -m unittest discover -s tests -v`
Expected: all OK

- [ ] **Step 5: Commit**

```bash
git add collector/ical.py tests/test_ical.py
git commit -m "Minimal iCalendar reader"
```

---

### Task 4: `classify.py` (tier, hints and overrides)

**Files:**
- Create: `collector/classify.py`, `tests/test_classify.py`

**Interfaces:**
- Consumes: event dicts from `model.make_event` (including the `_` fields).
- Produces:
  - `classify.classify(event) -> new event dict` with `tier` and `hints` set
  - `classify.load_overrides(path) -> list of rules`
  - `classify.apply_overrides(events, rules) -> list`
  - `classify.HINTS = ("all-ages", "outdoors", "daytime", "21+")` (the display order)
  - `classify.cues(text) -> str`: only the words of a description that `classify` looks for (used by Task 15 when saving last-good results, and by the recording scripts in Tasks 7 and 23)

- [ ] **Step 1: Write the failing tests** `tests/test_classify.py`

```python
import json
import os
import tempfile
import unittest

from helpers import la
import classify
import model


def ev(title, hh=10, text="", venue_name=None, tags=(), **kw):
    v = model.venue(venue_name, "Reno, NV") if venue_name else None
    return model.make_event("x", title, title, la(2026, 10, 10, hh), venue=v, city="Reno",
                            text=text, tags=tags, **kw)


class TierTest(unittest.TestCase):
    CASES = [
        # (title, text, tags, flags, expected tier)
        ("Baby & Toddler Storytime", "", (), {}, "little"),
        ("Lapsit Rhymes", "", (), {}, "little"),
        ("Preschool Science Hour", "", (), {}, "little"),
        ("Sensory Play Morning", "", (), {}, "little"),
        ("Puppet Show: The Three Bears", "", (), {}, "little"),
        ("Family Day at the Museum", "", (), {}, "little"),
        ("Fall Festival", "Fun for kids and families of all ages.", (), {}, "little"),
        ("Disney On Ice", "", ("Family",), {}, "little"),
        ("Sesame Street Live", "", (), {"family": True}, "little"),
        ("Kid Rock", "", (), {}, "general"),                       # "kid" alone isn't "kids"
        ("Babyface Live", "", (), {}, "general"),                  # word boundary
        ("Chamber Orchestra", "An evening of Brahms.", (), {}, "general"),
        ("Family Feud Trivia Night", "21+ with ID.", (), {}, "general"),   # 21+ wins
        ("Kids Comedy Hour", "", (), {"adult": True}, "general"),          # age-enforced wins
    ]

    def test_cases(self):
        for title, text, tags, flags, tier in self.CASES:
            with self.subTest(title=title):
                self.assertEqual(classify.classify(ev(title, text=text, tags=tags, **flags))["tier"], tier)


class HintsTest(unittest.TestCase):
    def test_adult_words(self):
        for text in ("21+ only", "Ages 21 and over", "18+ show", "Bar crawl downtown", "Wine tasting flight",
                     "A burlesque revue"):
            with self.subTest(text=text):
                self.assertIn("21+", classify.classify(ev("Night Out", hh=20, text=text))["hints"])

    def test_bar_venues_are_21_plus(self):
        e = classify.classify(ev("DJ Night", hh=22, venue_name="The Loft Lounge"))
        self.assertIn("21+", e["hints"])
        self.assertNotIn("21+", classify.classify(ev("Concert", hh=20, venue_name="Bartley Ranch"))["hints"])

    def test_daytime_and_outdoors(self):
        e = classify.classify(ev("Farmers Market", hh=9, venue_name="Idlewild Park"))
        self.assertEqual(e["hints"], ["outdoors", "daytime"])
        self.assertEqual(classify.classify(ev("Concert", hh=19))["hints"], [])

    def test_all_day_counts_as_daytime(self):
        e = model.make_event("x", "1", "Expo", la(2026, 10, 10).date(), all_day=True, city="Reno")
        self.assertIn("daytime", classify.classify(e)["hints"])

    def test_all_ages_only_when_the_source_says_so_and_not_21(self):
        self.assertIn("all-ages", classify.classify(ev("Ballgame", all_ages=True))["hints"])
        self.assertNotIn("all-ages", classify.classify(ev("Ballgame", all_ages=True, adult=True))["hints"])

    def test_classify_does_not_mutate_its_input(self):
        e = ev("Storytime")
        classify.classify(e)
        self.assertEqual(e["tier"], "general")


class CuesTest(unittest.TestCase):
    def test_keeps_only_the_words_classify_looks_for(self):
        self.assertEqual(classify.cues("A gentle class for toddlers and their grown-ups. 21+ after 9pm."),
                         "toddlers 21+")
        self.assertEqual(classify.cues("Kids, kids, kids!"), "Kids kids")
        self.assertEqual(classify.cues("An evening of chamber music."), "")
        self.assertEqual(classify.cues(None), "")

    def test_classifying_from_cues_matches_classifying_from_the_text(self):
        for text in ("Songs and puppets for little ones", "Wine tasting, 21 and over", "Chamber music",
                     "Kids eat free before the bar crawl"):
            full = classify.classify(ev("Event", text=text))
            short = classify.classify(ev("Event", text=classify.cues(text)))
            self.assertEqual((full["tier"], full["hints"]), (short["tier"], short["hints"]), text)


class OverridesTest(unittest.TestCase):
    def setUp(self):
        self.events = [classify.classify(ev("Storytime at Sparks Library")),
                       classify.classify(ev("Trivia Night", hh=19)),
                       classify.classify(ev("Spam Event"))]

    def test_rules(self):
        rules = [{"match": "trivia", "addHint": "21+"},
                 {"match": "id:x:Spam Event", "hide": True},
                 {"match": "^storytime", "tier": "general"}]
        out = classify.apply_overrides(self.events, rules)
        self.assertEqual([e["title"] for e in out], ["Storytime at Sparks Library", "Trivia Night"])
        self.assertEqual(out[0]["tier"], "general")
        self.assertIn("21+", out[1]["hints"])
        self.assertEqual(self.events[0]["tier"], "little", "input untouched")

    def test_adding_21_plus_removes_little_and_all_ages(self):
        e = classify.classify(ev("Kids Disco", all_ages=True))
        out = classify.apply_overrides([e], [{"match": "disco", "addHint": "21+"}])[0]
        self.assertEqual(out["tier"], "general")
        self.assertNotIn("all-ages", out["hints"])

    def test_load_skips_broken_rules_and_tolerates_a_broken_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "overrides.json")
            with open(path, "w") as f:
                json.dump([{"match": "(unclosed"}, {"tier": "little"}, {"match": "ok", "hide": True}], f)
            self.assertEqual(classify.load_overrides(path), [{"match": "ok", "hide": True}])
            with open(path, "w") as f:
                f.write("{not json")
            self.assertEqual(classify.load_overrides(path), [])
            self.assertEqual(classify.load_overrides(os.path.join(d, "missing.json")), [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run them to make sure they fail**

Run: `python3 -m unittest discover -s tests -v`
Expected: `ModuleNotFoundError: No module named 'classify'`

- [ ] **Step 3: Implement** `collector/classify.py`

```python
"""Tier and hints for each event (spec: "Classification"). The rules are plain
regular expressions so they're testable and easy to adjust; overrides.json has
the last word."""

import json
import re

LITTLE_WORDS = re.compile(
    r"\b(story ?times?|bab(y|ies)|toddlers?|lap-?sits?|little ones|preschool(ers?)?|"
    r"famil(y|ies)|kids|children(['’]s)?|sensory|puppets?|play ?groups?)\b", re.I)
# Exact (lower-cased) source categories that mean "made for little ones". Looser
# categories such as a tourism site's "Kids & Families" are judged by the source
# module, which sets family=True only where it holds (see sources/tribe.py).
LITTLE_TAGS = {"family", "children's theatre", "children's music", "story time",
               "storytime", "babies & toddlers", "preschool"}
ADULT_WORDS = re.compile(
    r"(\b(21|18) ?\+|\b(21|18) (and|&) (over|older|up)\b|\b(bar|pub) crawls?\b|"
    r"\b(wine|beer) tastings?\b|\bburlesque\b)", re.I)
ADULT_VENUES = re.compile(r"\b(lounge|bar|tavern|pub|saloon|nightclub)\b", re.I)
OUTDOOR_WORDS = re.compile(
    r"\b(park|trails?|festival grounds|outdoors?|markets?|amphitheat(er|re)|beach)\b", re.I)
HINTS = ("all-ages", "outdoors", "daytime", "21+")


def classify(event):
    e = dict(event)
    venue_name = (e.get("venue") or {}).get("name") or ""
    text = f"{e['title']} {e.get('_text', '')}"
    adult = bool(e.get("_adult") or ADULT_WORDS.search(text) or ADULT_VENUES.search(venue_name))
    little = not adult and bool(e.get("_family") or LITTLE_WORDS.search(text)
                                or set(e.get("_tags", [])) & LITTLE_TAGS)
    hints = []
    if e.get("_allAges") and not adult:
        hints.append("all-ages")
    if e.get("_outdoor") or OUTDOOR_WORDS.search(f"{e['title']} {venue_name}"):
        hints.append("outdoors")
    if e["allDay"] or int(e["start"][11:13]) < 17:
        hints.append("daytime")
    if adult:
        hints.append("21+")
    e["tier"] = "little" if little else "general"
    e["hints"] = hints
    return e


def cues(text):
    """Only the words of a description that classify() looks for, e.g. "toddlers 21+".
    Saved last-good results keep these instead of the description: write-ups aren't
    ours to store (spec: "Store and show only facts")."""
    found = [m.group(0) for pattern in (LITTLE_WORDS, ADULT_WORDS) for m in pattern.finditer(text or "")]
    return " ".join(dict.fromkeys(found))


def load_overrides(path):
    """Rules from overrides.json; broken rules (or a broken file) are skipped."""
    try:
        with open(path, encoding="utf-8") as f:
            rules = json.load(f)
    except FileNotFoundError:
        return []
    except ValueError as err:
        print(f"overrides: ignoring {path}: {err}")
        return []
    good = []
    for rule in rules if isinstance(rules, list) else []:
        match = rule.get("match") if isinstance(rule, dict) else None
        if not isinstance(match, str) or not match:
            print(f"overrides: skipping a rule without a match: {rule!r}")
            continue
        if not match.startswith("id:"):
            try:
                re.compile(match)
            except re.error as err:
                print(f"overrides: skipping bad pattern {match!r}: {err}")
                continue
        good.append(rule)
    return good


def _matches(rule, event):
    m = rule["match"]
    return event["id"] == m[3:] if m.startswith("id:") else bool(re.search(m, event["title"], re.I))


def apply_overrides(events, rules):
    """Rules: {"match": "id:<id>" or a title regex, "tier"?, "hide"?, "addHint"?}."""
    out = []
    for event in events:
        e, hidden = dict(event), False
        for rule in rules:
            if not _matches(rule, e):
                continue
            hidden = hidden or bool(rule.get("hide"))
            if rule.get("tier") in ("little", "general"):
                e["tier"] = rule["tier"]
            hint = rule.get("addHint")
            if hint in HINTS and hint not in e["hints"]:
                e["hints"] = [h for h in HINTS if h in e["hints"] or h == hint]
                if hint == "21+":
                    e["tier"] = "general"
                    e["hints"] = [h for h in e["hints"] if h != "all-ages"]
        if not hidden:
            out.append(e)
    return out
```

- [ ] **Step 4: Run them to make sure they pass**

Run: `python3 -m unittest discover -s tests -v`
Expected: all OK

- [ ] **Step 5: Commit**

```bash
git add collector/classify.py tests/test_classify.py
git commit -m "Classifier: little-ones tier, hints and overrides"
```

---

### Task 5: `dedupe.py` (merge duplicates)

**Files:**
- Create: `collector/dedupe.py`, `tests/test_dedupe.py`

**Interfaces:**
- Consumes: event dicts (before classification; uses `id`, `title`, `start`, `allDay`, `venue`, `links`, `price`, `_kind` and the other `_` fields).
- Produces:
  - `dedupe.dedupe(events) -> list` (merged, sorted by start then id)
  - Helpers: `dedupe.is_duplicate(a, b) -> bool`, `dedupe.merge(group) -> event`, `dedupe.tokens(text) -> set`, `dedupe.overlap(a, b) -> float`

- [ ] **Step 1: Write the failing tests** `tests/test_dedupe.py`

```python
import unittest
from datetime import date

from helpers import la
import dedupe
import model


def ev(source, sid, title, start, venue_name=None, kind="organiser", price=None, url=None, all_day=False, **kw):
    v = model.venue(venue_name, "Reno, NV") if venue_name else None
    return model.make_event(source, sid, title, start, venue=v, city="Reno", kind=kind, price=price,
                            url=url or f"https://{source}.example/{sid}", all_day=all_day, **kw)


class TokensTest(unittest.TestCase):
    def test_tokens_drop_filler_and_years(self):
        self.assertEqual(dedupe.tokens("The 2026 Reno Aces vs. the Sacramento River Cats — Live!"),
                         {"reno", "aces", "sacramento", "river", "cats"})

    def test_overlap_uses_the_shorter_title(self):
        a, b = dedupe.tokens("Reno Aces vs Sacramento River Cats"), dedupe.tokens("Reno Aces vs Sacramento")
        self.assertEqual(dedupe.overlap(a, b), 1.0)

    def test_one_word_titles_must_match_exactly(self):
        self.assertEqual(dedupe.overlap({"storytime"}, {"toddler", "storytime"}), 0.0)
        self.assertEqual(dedupe.overlap({"storytime"}, {"storytime"}), 1.0)


class DuplicateTest(unittest.TestCase):
    def test_same_show_from_two_sources_merges(self):
        unr = ev("unr", "1", "Wind Ensemble Fall Concert", la(2026, 10, 10, 19, 30), "Nightingale Concert Hall")
        tm = ev("tm", "Z1", "UNR Wind Ensemble: Fall Concert", la(2026, 10, 10, 19, 30), "Nightingale Hall",
                kind="ticketing", price={"min": 10.0, "max": 15.0})
        self.assertTrue(dedupe.is_duplicate(unr, tm))

    def test_start_times_more_than_30_minutes_apart_do_not_merge(self):
        a = ev("unr", "1", "Fall Concert", la(2026, 10, 10, 19, 0), "Hall")
        b = ev("tm", "2", "Fall Concert", la(2026, 10, 10, 19, 31), "Hall")
        self.assertFalse(dedupe.is_duplicate(a, b))

    def test_same_venue_allows_a_looser_title_match(self):
        a = ev("unr", "1", "Brahms Requiem Choir Orchestra", la(2026, 10, 10, 19), "Pioneer Center")
        b = ev("tm", "2", "Brahms Requiem Choir Reno Phil", la(2026, 10, 10, 19), "Pioneer Center for the Performing Arts")
        self.assertTrue(dedupe.is_duplicate(a, b))  # overlap 3/4 = 0.75: below 0.8, enough at the same venue
        c = ev("tm", "3", "Brahms Requiem Choir Reno Phil", la(2026, 10, 10, 19), "Grand Sierra Resort")
        self.assertFalse(dedupe.is_duplicate(a, c))

    def test_different_events_from_one_source_stay_apart(self):
        a = ev("library", "1", "Baby Storytime", la(2026, 10, 10, 10, 0), "Downtown Library")
        b = ev("library", "2", "Toddler Storytime", la(2026, 10, 10, 10, 30), "Downtown Library")
        self.assertFalse(dedupe.is_duplicate(a, b))

    def test_exact_repeat_from_one_source_merges(self):
        a = ev("tm", "1", "Comedy Night", la(2026, 10, 10, 20), "Silver Legacy", kind="ticketing")
        b = ev("tm", "2", "Comedy Night", la(2026, 10, 10, 20), "Silver Legacy", kind="ticketing")
        self.assertTrue(dedupe.is_duplicate(a, b))

    def test_all_day_listing_matches_a_timed_one_on_the_same_day(self):
        wp = ev("wolfpack", "1", "Nevada Men's Basketball vs Idaho", date(2026, 11, 18), all_day=True)
        tm = ev("tm", "2", "Nevada Wolf Pack Men's Basketball vs. Idaho Vandals", la(2026, 11, 18, 19),
                "Lawlor Events Center", kind="ticketing")
        self.assertTrue(dedupe.is_duplicate(wp, tm))


class MergeTest(unittest.TestCase):
    def test_fields_come_from_the_most_specific_source(self):
        unr = ev("unr", "1", "Wind Ensemble Fall Concert", la(2026, 10, 10, 19, 30), "Nightingale Concert Hall",
                 text="Free parking.", tags=["Arts & Culture"])
        tm = ev("tm", "Z1", "UNR Wind Ensemble: Fall Concert", la(2026, 10, 10, 19, 0), "Nightingale Hall",
                kind="ticketing", price={"min": 10.0, "max": 15.0}, family=True)
        [m] = dedupe.dedupe([tm, unr])
        self.assertEqual(m["id"], "unr:1")
        self.assertEqual(m["title"], "Wind Ensemble Fall Concert")
        self.assertEqual(m["start"], "2026-10-10T19:30:00-07:00")      # organiser's time
        self.assertEqual(m["venue"]["name"], "Nightingale Concert Hall")
        self.assertEqual(m["price"], {"min": 10.0, "max": 15.0})         # ticketing's price
        self.assertEqual([l["source"] for l in m["links"]], ["unr", "tm"])
        self.assertTrue(m["_family"])
        self.assertEqual(m["_tags"], ["arts & culture"])

    def test_timed_listing_replaces_an_all_day_one(self):
        wp = ev("wolfpack", "1", "Nevada Men's Basketball vs Idaho", date(2026, 11, 18), all_day=True)
        tm = ev("tm", "2", "Nevada Wolf Pack Men's Basketball vs. Idaho Vandals", la(2026, 11, 18, 19),
                "Lawlor Events Center", kind="ticketing")
        [m] = dedupe.dedupe([wp, tm])
        self.assertFalse(m["allDay"])
        self.assertEqual(m["start"], "2026-11-18T19:00:00-08:00")
        self.assertEqual(m["venue"]["name"], "Lawlor Events Center")

    def test_unrelated_events_pass_through_in_order(self):
        a = ev("unr", "1", "Morning Talk", la(2026, 10, 10, 9))
        b = ev("tm", "2", "Evening Show", la(2026, 10, 10, 20), kind="ticketing")
        c = ev("aces", "3", "Ballgame", la(2026, 10, 11, 13))
        self.assertEqual([e["id"] for e in dedupe.dedupe([c, b, a])], ["unr:1", "tm:2", "aces:3"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run them to make sure they fail**

Run: `python3 -m unittest discover -s tests -v`
Expected: `ModuleNotFoundError: No module named 'dedupe'`

- [ ] **Step 3: Implement** `collector/dedupe.py`

```python
"""Merge the same event listed by more than one source (spec: "Merging
duplicates"). Same local date, starts within 30 minutes, and titles that
mostly match (or match less well at the same venue)."""

import re
from datetime import datetime

FILLER = {"the", "a", "an", "and", "of", "at", "in", "on", "vs", "v", "with",
          "presents", "presented", "by", "featuring", "feat", "ft", "live", "tour"}
KIND_RANK = {"organiser": 0, "ticketing": 1}   # organiser's own feed wins time and place


def tokens(text):
    text = (text or "").lower().replace("'", "").replace("’", "")
    return {w for w in re.findall(r"[a-z0-9]+", text)
            if w not in FILLER and not re.fullmatch(r"(19|20)\d\d", w)}


def overlap(a, b):
    """Shared share of the shorter title; one-word titles must match exactly."""
    if not a or not b:
        return 0.0
    if min(len(a), len(b)) < 2:
        return 1.0 if a == b else 0.0
    return len(a & b) / min(len(a), len(b))


def _source(e):
    return e["id"].split(":", 1)[0]


def same_time(a, b):
    if a["start"][:10] != b["start"][:10]:
        return False
    if a["allDay"] or b["allDay"]:
        return True
    gap = datetime.fromisoformat(a["start"]) - datetime.fromisoformat(b["start"])
    return abs(gap.total_seconds()) <= 30 * 60


def same_venue(a, b):
    va = tokens((a.get("venue") or {}).get("name"))
    vb = tokens((b.get("venue") or {}).get("name"))
    return bool(va and vb) and len(va & vb) / min(len(va), len(vb)) >= 0.5


def is_duplicate(a, b):
    if not same_time(a, b):
        return False
    ta, tb = tokens(a["title"]), tokens(b["title"])
    if _source(a) == _source(b):
        no_venues = not a.get("venue") and not b.get("venue")
        return ta == tb and a["start"] == b["start"] and (no_venues or same_venue(a, b))
    o = overlap(ta, tb)
    return o >= 0.8 or (o >= 0.6 and same_venue(a, b))


def merge(group):
    ranked = sorted(group, key=lambda e: (KIND_RANK.get(e.get("_kind"), 0), e["id"]))
    m = dict(ranked[0])
    timed = [e for e in ranked if not e["allDay"]]
    if m["allDay"] and timed:
        m["start"], m["end"], m["allDay"] = timed[0]["start"], timed[0]["end"], False
    placed = next((e for e in ranked if e.get("venue")), ranked[0])
    m["venue"], m["area"], m["drive"] = placed.get("venue"), placed["area"], placed["drive"]
    by_price = sorted(ranked, key=lambda e: e.get("_kind") != "ticketing")
    m["price"] = next((e["price"] for e in by_price if e.get("price")), None)
    links, seen = [], set()
    for e in ranked:
        for link in e["links"]:
            if link["url"] not in seen:
                seen.add(link["url"])
                links.append(link)
    m["links"] = links
    m["ongoing"] = all(e["ongoing"] for e in ranked)
    m["_text"] = " ".join(e.get("_text", "") for e in ranked)[:4000]
    m["_tags"] = sorted(set().union(*(e.get("_tags", []) for e in ranked)))
    for flag in ("_family", "_adult", "_allAges", "_outdoor"):
        m[flag] = any(e.get(flag) for e in ranked)
    return m


def dedupe(events):
    by_day = {}
    for e in sorted(events, key=lambda e: (e["start"], e["id"])):
        groups = by_day.setdefault(e["start"][:10], [])
        for group in groups:
            if any(is_duplicate(e, other) for other in group):
                group.append(e)
                break
        else:
            groups.append([e])
    merged = [merge(g) if len(g) > 1 else g[0] for groups in by_day.values() for g in groups]
    return sorted(merged, key=lambda e: (e["start"], e["id"]))
```

- [ ] **Step 4: Run them to make sure they pass**

Run: `python3 -m unittest discover -s tests -v`
Expected: all OK. Don't loosen a threshold to make a test pass: the 0.8 and 0.6 thresholds and the 30 minutes are the spec's.

- [ ] **Step 5: Commit**

```bash
git add collector/dedupe.py tests/test_dedupe.py
git commit -m "Merge duplicate listings across sources"
```

---

### Task 6: `schedule.py` (refresh and digest decision)

**Files:**
- Create: `collector/schedule.py`, `tests/test_schedule.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `schedule.Decision(refresh: bool, digest: bool)` (frozen dataclass)
  - `schedule.decide(now, last_refresh, digest_date, digest_enabled=True, force_digest=False) -> Decision`, where:
    - `now` is an aware datetime in LA
    - `last_refresh` is an aware datetime or None
    - `digest_date` is `'YYYY-MM-DD'` or None
  - Constants: `schedule.REFRESH_EVERY`, `DIGEST_FROM = 7`, `DIGEST_UNTIL = 11`

- [ ] **Step 1: Write the failing tests** `tests/test_schedule.py`

```python
import unittest
from datetime import timedelta

from helpers import la
from schedule import Decision, decide


class ScheduleTest(unittest.TestCase):
    def test_first_run_refreshes(self):
        self.assertEqual(decide(la(2026, 10, 10, 3, 30), None, None), Decision(True, False))

    def test_refresh_every_2h50(self):
        now = la(2026, 10, 10, 14, 30)
        self.assertFalse(decide(now, now - timedelta(hours=2, minutes=49), "2026-10-10").refresh)
        self.assertTrue(decide(now, now - timedelta(hours=2, minutes=50), "2026-10-10").refresh)

    def test_digest_window_is_07_00_to_10_59(self):
        recent = la(2026, 10, 10, 6, 0)
        self.assertFalse(decide(la(2026, 10, 10, 6, 59), recent, "2026-10-09").digest)
        self.assertEqual(decide(la(2026, 10, 10, 7, 0), recent, "2026-10-09"), Decision(True, True))
        self.assertTrue(decide(la(2026, 10, 10, 10, 59), recent, "2026-10-09").digest)
        self.assertFalse(decide(la(2026, 10, 10, 11, 0), recent, "2026-10-09").digest)

    def test_digest_already_sent_today(self):
        now = la(2026, 10, 10, 8, 30)
        self.assertEqual(decide(now, now - timedelta(hours=1), "2026-10-10"), Decision(False, False))

    def test_failed_digest_retries_next_hour(self):
        now = la(2026, 10, 10, 8, 30)
        self.assertEqual(decide(now, now - timedelta(hours=1), "2026-10-09"), Decision(True, True))

    def test_no_webhook_means_no_digest_and_no_extra_refreshes(self):
        now = la(2026, 10, 10, 8, 30)
        self.assertEqual(decide(now, now - timedelta(hours=1), None, digest_enabled=False), Decision(False, False))

    def test_force_digest(self):
        now = la(2026, 10, 10, 15, 0)
        self.assertEqual(decide(now, now - timedelta(minutes=5), "2026-10-10", force_digest=True),
                         Decision(True, True))

    def test_digest_on_dst_change_days(self):
        # 2026-03-08 (spring forward) and 2026-11-01 (fall back): 07:30 local is still digest time.
        self.assertTrue(decide(la(2026, 3, 8, 7, 30), la(2026, 3, 8, 4, 0), "2026-03-07").digest)
        self.assertTrue(decide(la(2026, 11, 1, 7, 30), la(2026, 11, 1, 4, 0), "2026-10-31").digest)

    def test_elapsed_time_is_real_time_across_fall_back(self):
        # 00:30 PDT to 02:30 PST on 2026-11-01 is 3 real hours, though the wall clock moved 2.
        last = la(2026, 11, 1, 0, 30)               # PDT (-07:00)
        now = la(2026, 11, 1, 2, 30)                # PST (-08:00)
        self.assertTrue(decide(now, last, "2026-11-01").refresh)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run them to make sure they fail**

Run: `python3 -m unittest discover -s tests -v`
Expected: `ModuleNotFoundError: No module named 'schedule'`

- [ ] **Step 3: Implement** `collector/schedule.py`

```python
"""Each hourly run decides whether to refresh and whether to send the digest
(spec: "Each run decides what to do")."""

from dataclasses import dataclass
from datetime import timedelta, timezone

REFRESH_EVERY = timedelta(hours=2, minutes=50)
DIGEST_FROM, DIGEST_UNTIL = 7, 11      # local hours: try from 07:00, give up after 10:59


@dataclass(frozen=True)
class Decision:
    refresh: bool
    digest: bool


def decide(now, last_refresh, digest_date, digest_enabled=True, force_digest=False):
    """now: aware Reno datetime. last_refresh: aware datetime or None.
    digest_date: 'YYYY-MM-DD' the digest was last sent, or None."""
    digest = force_digest or (digest_enabled and DIGEST_FROM <= now.hour < DIGEST_UNTIL
                              and digest_date != now.date().isoformat())
    # Subtract in UTC: two datetimes sharing the same ZoneInfo subtract by wall clock.
    stale = (last_refresh is None or
             now.astimezone(timezone.utc) - last_refresh.astimezone(timezone.utc) >= REFRESH_EVERY)
    return Decision(refresh=digest or stale, digest=digest)
```

- [ ] **Step 4: Run them to make sure they pass**

Run: `python3 -m unittest discover -s tests -v`
Expected: all OK

- [ ] **Step 5: Commit**

```bash
git add collector/schedule.py tests/test_schedule.py
git commit -m "Hourly decision: refresh every ~3h, digest 07:00-10:59"
```

---
### Task 7: Source framework and UNR events (Localist)

**Files:**
- Create: `collector/sources/__init__.py`, `collector/sources/base.py`, `collector/sources/unr.py`, `tests/test_unr.py`, `tests/fixtures/unr.json`, `tests/fixtures/real/unr.json` (recorded), `dev/try_source.py`

**Interfaces:**
- Consumes: `net.get_json`, `net.FetchError`, `model.make_event / venue / price_range / plain / FREE`
- Produces:
  - `sources.base.SourceError(Exception)`
  - `sources.base.Context(start, end, env={})` (frozen dataclass; `start` is today 00:00 Reno, `end` is start + 8 days, exclusive)
  - `sources.ALL`: a list of source objects. **Every source** (a module or an object) has `NAME` (status key), `LABEL` (shown on the page), `fetch(ctx) -> list[event]` (raises `net.FetchError` or `SourceError`) and optionally `EVERY` (a `timedelta`: reuse the last good result if it's younger than this). Sources return events possibly outside the window; `collect.py` filters.
  - `unr.parse(items) -> list[event]`
  - `dev/try_source.py <name>`: runs one source live and prints what it found

Facts checked on 2026-10-05:
- **Endpoint:** `https://events.unr.edu/api/2/events?start=YYYY-MM-DD&end=YYYY-MM-DD&pp=100&page=N`. It returns `{"events": [{"event": {...}}], "page": {"current", "total", ...}}`, with **one entry per occurrence** (`event_instances` holds just that one).
- **Volume:** about 150 entries in 8 days (2 pages).
- **What to drop:**
  - virtual events
  - anything outside Reno/Sparks (many are Extension events in Las Vegas)
  - Extension events with no city
  - Counseling Services
  - events whose only types are staff/student internals
- **What to keep:** `experience` is `inperson` or `hybrid`.
- **Exhibits:** have the type `Exhibitions (recurring)`.

- [ ] **Step 1: Write the fixture** `tests/fixtures/unr.json`

This is hand-made, shaped like the real API response (the titles are real).

```json
{
  "events": [
    {"event": {"id": 1, "title": "2026 Nevada Radon Poster Contest", "status": "live", "experience": "virtual", "private": false,
      "location_name": "", "free": true, "ticket_cost": "0.00",
      "geo": {"city": null, "street": null, "latitude": null, "longitude": null},
      "groups": [{"name": "Extension"}], "filters": {"event_types": [{"name": "Community Outreach"}]},
      "event_instances": [{"event_instance": {"id": 101, "start": "2026-10-05T00:00:00-07:00", "end": null, "all_day": true}}],
      "localist_url": "https://events.unr.edu/event/2026-nevada-radon-poster-contest", "description_text": "Grades 6-12."}},
    {"event": {"id": 2, "title": "4-H Vegas Rangers Archery Club", "status": "live", "experience": "inperson", "private": false,
      "location_name": "Clark County Shooting Sports Complex", "free": false, "ticket_cost": "",
      "geo": {"city": "Las Vegas", "street": null, "latitude": null, "longitude": null},
      "groups": [{"name": "Extension"}], "filters": {"event_types": [{"name": "Youth Camps & Programs"}]},
      "event_instances": [{"event_instance": {"id": 102, "start": "2026-10-05T16:30:00-07:00", "end": "2026-10-05T18:30:00-07:00", "all_day": false}}],
      "localist_url": "https://events.unr.edu/event/4-h-vegas-rangers", "description_text": ""}},
    {"event": {"id": 3, "title": "A Few of Our Favorite Things: 65 Years of Special Collections", "status": "live", "experience": "inperson", "private": false,
      "location_name": "Mathewson-IGT Knowledge Center", "free": false, "ticket_cost": null,
      "geo": {"city": null, "street": null, "latitude": null, "longitude": null},
      "groups": [{"name": "University Libraries"}], "filters": {"event_types": [{"name": "Exhibitions (recurring)"}]},
      "event_instances": [{"event_instance": {"id": 103, "start": "2026-10-06T08:00:00-07:00", "end": "2026-10-06T17:00:00-07:00", "all_day": false}}],
      "localist_url": "https://events.unr.edu/event/a-few-of-our-favorite-things", "description_text": "An exhibit."}},
    {"event": {"id": 4, "title": "Voice Area Recital - Graduate Students and Seniors", "status": "live", "experience": "inperson", "private": false,
      "location_name": "University Foundation Arts (UFA) Building", "free": true, "ticket_cost": "",
      "geo": {"city": null, "street": null, "latitude": null, "longitude": null},
      "groups": [{"name": "School of Music"}], "filters": {"event_types": [{"name": "Arts & Culture"}]},
      "event_instances": [{"event_instance": {"id": 104, "start": "2026-10-06T13:00:00-07:00", "end": "2026-10-06T14:30:00-07:00", "all_day": false}}],
      "localist_url": "https://events.unr.edu/event/voice-area-recital", "description_text": ""}},
    {"event": {"id": 5, "title": "Let's Talk", "status": "live", "experience": "inperson", "private": false,
      "location_name": "Great Basin Hall (GBH)", "free": false, "ticket_cost": "",
      "geo": {"city": null, "street": null, "latitude": null, "longitude": null},
      "groups": [{"name": "Counseling Services"}], "filters": {"event_types": [{"name": "Social Events"}]},
      "event_instances": [{"event_instance": {"id": 105, "start": "2026-10-06T10:00:00-07:00", "end": "2026-10-06T12:00:00-07:00", "all_day": false}}],
      "localist_url": "https://events.unr.edu/event/lets-talk", "description_text": ""}},
    {"event": {"id": 6, "title": "Grant Writing Basics", "status": "live", "experience": "inperson", "private": false,
      "location_name": "Pennington Student Achievement Center", "free": false, "ticket_cost": "",
      "geo": {"city": null, "street": null, "latitude": null, "longitude": null},
      "groups": [{"name": "Office of Research"}],
      "filters": {"event_types": [{"name": "Training & Workshops"}, {"name": "Professional Development"}]},
      "event_instances": [{"event_instance": {"id": 106, "start": "2026-10-07T09:00:00-07:00", "end": "2026-10-07T10:00:00-07:00", "all_day": false}}],
      "localist_url": "https://events.unr.edu/event/grant-writing", "description_text": ""}},
    {"event": {"id": 7, "title": "Family Science Saturday", "status": "live", "experience": "inperson", "private": false,
      "location_name": "Fleischmann Planetarium", "free": false, "ticket_cost": "5.00",
      "geo": {"city": "Reno", "street": "1650 N Virginia St", "latitude": "39.5466", "longitude": "-119.8175"},
      "groups": [{"name": "Fleischmann Planetarium"}], "filters": {"event_types": [{"name": "Family Engagement"}]},
      "event_instances": [{"event_instance": {"id": 107, "start": "2026-10-10T10:00:00-07:00", "end": "2026-10-10T12:00:00-07:00", "all_day": false}}],
      "localist_url": "https://events.unr.edu/event/family-science-saturday",
      "description_text": "Hands-on science for kids and families."}},
    {"event": {"id": 8, "title": "Dementia Conversations", "status": "live", "experience": "inperson", "private": false,
      "location_name": "Washoe County Senior Center", "free": false, "ticket_cost": "",
      "geo": {"city": null, "street": null, "latitude": null, "longitude": null},
      "groups": [{"name": "Extension"}], "filters": {"event_types": [{"name": "Community Outreach"}]},
      "event_instances": [{"event_instance": {"id": 108, "start": "2026-10-07T10:00:00-07:00", "end": "2026-10-07T11:30:00-07:00", "all_day": false}}],
      "localist_url": "https://events.unr.edu/event/dementia-conversations", "description_text": ""}},
    {"event": {"id": 9, "title": "Homecoming Week", "status": "live", "experience": "inperson", "private": false,
      "location_name": "", "free": false, "ticket_cost": "",
      "geo": {"city": "Reno", "street": null, "latitude": null, "longitude": null},
      "groups": [{"name": "Student Engagement"}], "filters": {"event_types": [{"name": "Social Events"}]},
      "event_instances": [{"event_instance": {"id": 109, "start": "2026-10-09T00:00:00-07:00", "end": null, "all_day": true}}],
      "localist_url": "https://events.unr.edu/event/homecoming-week", "description_text": ""}}
  ],
  "page": {"current": 1, "size": 100, "total": 1, "total_items": 9}
}
```

- [ ] **Step 2: Write the failing tests** `tests/test_unr.py`

```python
import os
import unittest
from datetime import datetime
from unittest import mock

from helpers import fixture_json, fixture_path, la
import net
from sources import unr
from sources.base import Context, SourceError

CTX = Context(start=la(2026, 10, 5), end=la(2026, 10, 13))


class UnrParseTest(unittest.TestCase):
    def setUp(self):
        self.by_id = {e["id"]: e for e in unr.parse(fixture_json("unr.json")["events"])}

    def test_keeps_only_public_reno_listings(self):
        self.assertEqual(sorted(self.by_id), ["unr:103", "unr:104", "unr:107", "unr:109"])

    def test_exhibit_is_ongoing_on_campus(self):
        e = self.by_id["unr:103"]
        self.assertTrue(e["ongoing"])
        self.assertEqual(e["venue"]["name"], "Mathewson-IGT Knowledge Center")
        self.assertEqual(e["area"], "reno")
        self.assertEqual((e["start"], e["end"]), ("2026-10-06T08:00:00-07:00", "2026-10-06T17:00:00-07:00"))
        self.assertEqual(e["links"], [{"source": "unr", "url": "https://events.unr.edu/event/a-few-of-our-favorite-things"}])

    def test_prices(self):
        self.assertEqual(self.by_id["unr:104"]["price"], {"free": True})
        self.assertEqual(self.by_id["unr:107"]["price"], {"min": 5.0, "max": 5.0})
        self.assertIsNone(self.by_id["unr:103"]["price"])

    def test_all_day(self):
        e = self.by_id["unr:109"]
        self.assertTrue(e["allDay"])
        self.assertEqual(e["start"], "2026-10-09T00:00:00-07:00")
        self.assertEqual(e["venue"]["name"], "University of Nevada, Reno")

    def test_classification_inputs(self):
        e = self.by_id["unr:107"]
        self.assertIn("family engagement", e["_tags"])
        self.assertIn("kids and families", e["_text"])
        self.assertEqual((e["venue"]["lat"], e["venue"]["lon"]), (39.5466, -119.8175))
        self.assertEqual(e["_kind"], "organiser")


class UnrFetchTest(unittest.TestCase):
    def test_follows_pages_with_the_window_dates(self):
        items = fixture_json("unr.json")["events"]
        pages = {1: {"events": items[:4], "page": {"current": 1, "total": 2}},
                 2: {"events": items[4:], "page": {"current": 2, "total": 2}}}
        urls = []

        def fake_get_json(url, **kw):
            urls.append(url)
            return pages[int(url.rsplit("page=", 1)[1])]

        with mock.patch.object(net, "get_json", fake_get_json):
            got = unr.fetch(CTX)
        self.assertEqual(len(urls), 2)
        self.assertIn("start=2026-10-05&end=2026-10-12", urls[0])
        self.assertEqual(len(got), 4)

    def test_a_reshaped_body_is_a_source_error(self):
        with mock.patch.object(net, "get_json", lambda url, **kw: {"error": "maintenance"}):
            with self.assertRaises(SourceError):
                unr.fetch(CTX)

    def test_real_recording_parses(self):
        if not os.path.exists(fixture_path("real/unr.json")):
            self.skipTest("no real recording yet")
        events = unr.parse(fixture_json("real/unr.json")["events"])
        self.assertTrue(events)
        for e in events:
            self.assertIn(e["area"], ("reno", "sparks"))
            self.assertTrue(e["title"])
            datetime.fromisoformat(e["start"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run them to make sure they fail**

Run: `python3 -m unittest discover -s tests -v`
Expected: `ModuleNotFoundError: No module named 'sources'`

- [ ] **Step 4: Implement the framework and the source**

`collector/sources/base.py`:
```python
"""What every source shares."""

from dataclasses import dataclass, field
from datetime import datetime


class SourceError(Exception):
    """This source can't be read this run (unexpected response, not set up...)."""


@dataclass(frozen=True)
class Context:
    start: datetime                   # today 00:00, America/Los_Angeles
    end: datetime                     # start + 8 days (exclusive)
    env: dict = field(default_factory=dict)
```

`collector/sources/__init__.py`:
```python
"""Event sources. Each has NAME (status key), LABEL (shown on the page) and
fetch(ctx) -> list of model.make_event dicts, raising net.FetchError or
sources.base.SourceError when it can't be read. Optional EVERY (timedelta):
collect.py reuses the last good result while it's younger than that."""

from sources import unr

ALL = [unr]
```

`collector/sources/unr.py`:
```python
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
```

`dev/try_source.py`:
```python
#!/usr/bin/env python3
"""Run one source against the real site and print what it found.

    python3 dev/try_source.py unr
    TICKETMASTER_KEY=... python3 dev/try_source.py ticketmaster
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "collector"))

import model  # noqa: E402
import sources  # noqa: E402
from sources.base import Context  # noqa: E402


def main(name):
    src = next((s for s in sources.ALL if s.NAME == name), None)
    if src is None:
        sys.exit(f"unknown source {name!r}; have: {', '.join(s.NAME for s in sources.ALL)}")
    start, end = model.window(datetime.now(model.LA))
    found = [e for e in src.fetch(Context(start, end, dict(os.environ))) if model.in_window(e, start, end)]
    print(f"{src.LABEL}: {len(found)} events in the next {model.DAYS} days")
    for e in found[:20]:
        where = (e["venue"] or {}).get("name") or "?"
        print(f"  {e['start'][:16]}  {e['area']:<13} {e['title'][:60]}  @ {where}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
```

- [ ] **Step 5: Run the tests to make sure they pass**

Run: `python3 -m unittest discover -s tests -v`
Expected: all OK, with `test_real_recording_parses` **skipped**

- [ ] **Step 6: Record a real response and try it live**

```bash
mkdir -p tests/fixtures/real
curl -sS -A "reno-today/1.0 (+https://github.com/natanforestree/reno-today)" \
  "https://events.unr.edu/api/2/events?days=8&pp=100&page=1" | python3 -c "
import json, sys
sys.path.insert(0, 'collector')
import classify
d = json.load(sys.stdin)
d['events'] = d['events'][:60]
for w in d['events']:
    w['event']['description'] = ''
    w['event']['description_text'] = classify.cues(w['event'].get('description_text'))
    for k in ('stream_info', 'stream_embed_code', 'stream_url', 'directions'):
        w['event'].pop(k, None)     # write-ups and virtual-meeting join links/passcodes
json.dump(d, open('tests/fixtures/real/unr.json', 'w'), indent=1)"
python3 -m unittest tests.test_unr -v 2>&1 | tail -3     # run from tests/ is not needed; discover also works
python3 dev/try_source.py unr
```
Expected:
- The recording test passes.
- `try_source` prints roughly 40–100 events, all in `reno`, with real UNR titles and no Las Vegas venues.

If `python3 -m unittest tests.test_unr` can't import `helpers`, use `python3 -m unittest discover -s tests -p test_unr.py -v` instead.

- [ ] **Step 7: Commit**

```bash
git add collector/sources tests/test_unr.py tests/fixtures/unr.json tests/fixtures/real/unr.json dev/try_source.py
git commit -m "Sources framework + UNR events (Localist)"
```

---

### Task 8: Nevada Wolf Pack home games (iCal)

**Files:**
- Create: `collector/sources/wolfpack.py`, `tests/test_wolfpack.py`, `tests/fixtures/wolfpack.ics`, `tests/fixtures/real/wolfpack.ics` (recorded)
- Modify: `collector/sources/__init__.py` (add to `ALL`)

**Interfaces:**
- Consumes: `ical.events / text / when`, `net.get_text`, `model.make_event / venue`, `SourceError`
- Produces: `wolfpack.parse(text) -> list[event]` (home games only), `wolfpack.clean_title(summary)`, `NAME = "wolfpack"`

The feed is `https://nevadawolfpack.com/calendar.ashx/calendar.ics` (SIDEARM, about 250 events, the whole season). Its quirks:
- `LOCATION` looks like `Reno\, Nev.\, Mackay Stadium`, or `Reno\, Nev. \, Lawlor Events Center` with stray spaces.
- Away games read `Albuquerque\, N.M.`.
- A home game can be in `Stateline\, Nev.` (Tahoe).
- `SUMMARY` starts with a result tag (`[W] `, `[L] `, `[T] `, `[N] `) once played, and may end with ` - Presented by: …`.
- Time-TBA games use `DTSTART;VALUE=DATE`.
- `URL` contains `&amp;`.

- [ ] **Step 1: Write the fixture** `tests/fixtures/wolfpack.ics` (CRLF line endings aren't needed; the parser accepts LF)

```
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//SIDEARM Sports//NONSGML SIDEARM//EN
BEGIN:VEVENT
UID:vcal_14076-nevadawolfpack.com
DTSTART:20261024T210000Z
DTEND:20261025T000000Z
LOCATION:Reno\, Nev.\, Mackay Stadium
SUMMARY:University of Nevada Football vs San José State - Presented by: 
URL:https://nevadawolfpack.com/calendar.aspx?game_id=14076&amp;sport_id=2
END:VEVENT
BEGIN:VEVENT
UID:vcal_14074-nevadawolfpack.com
DTSTART:20261010T230000Z
LOCATION:El Paso\, Texas
SUMMARY:University of Nevada Football at UTEP
URL:https://nevadawolfpack.com/calendar.aspx?game_id=14074&amp;sport_id=2
END:VEVENT
BEGIN:VEVENT
UID:vcal_14224-nevadawolfpack.com
DTSTART;VALUE=DATE:20261118
LOCATION:Reno\, Nev.\, Lawlor Events Center
SUMMARY:University of Nevada Men's Basketball vs Idaho
URL:https://nevadawolfpack.com/calendar.aspx?game_id=14224&amp;sport_id=5
END:VEVENT
BEGIN:VEVENT
UID:vcal_14215-nevadawolfpack.com
DTSTART:20261108T213000Z
LOCATION:Stateline\, Nev.\, Tahoe Blue Event Center
SUMMARY:University of Nevada Men's Basketball vs Saint Mary's
URL:https://nevadawolfpack.com/calendar.aspx?game_id=14215&amp;sport_id=5
END:VEVENT
BEGIN:VEVENT
UID:vcal_14250-nevadawolfpack.com
DTSTART:20261108T020000Z
LOCATION:Reno\, Nev. \, Lawlor Events Center
SUMMARY:[W] University of Nevada Women's Basketball vs Sacramento State
URL:https://nevadawolfpack.com/calendar.aspx?game_id=14250&amp;sport_id=6
END:VEVENT
BEGIN:VEVENT
UID:vcal_14290-nevadawolfpack.com
DTSTART;VALUE=DATE:20261030
LOCATION:Reno\, Nev.
SUMMARY:University of Nevada Women's Cross Country vs Credit Union One Mountain West Championships
URL:https://nevadawolfpack.com/calendar.aspx?game_id=14290&amp;sport_id=8
END:VEVENT
BEGIN:VEVENT
UID:vcal_14187-nevadawolfpack.com
DTSTART;VALUE=DATE:20261111
LOCATION:
SUMMARY:University of Nevada Women's Soccer vs TBA
END:VEVENT
END:VCALENDAR
```

- [ ] **Step 2: Write the failing tests** `tests/test_wolfpack.py`

```python
import os
import unittest
from unittest import mock

from helpers import fixture_path, fixture_text, la
import net
from sources import wolfpack
from sources.base import Context, SourceError


class WolfpackTest(unittest.TestCase):
    def setUp(self):
        self.by_id = {e["id"].split(":", 1)[1]: e for e in wolfpack.parse(fixture_text("wolfpack.ics"))}

    def test_home_games_only(self):
        self.assertEqual(sorted(self.by_id), ["vcal_14076-nevadawolfpack.com", "vcal_14215-nevadawolfpack.com",
                                              "vcal_14224-nevadawolfpack.com", "vcal_14250-nevadawolfpack.com",
                                              "vcal_14290-nevadawolfpack.com"])

    def test_title_venue_time_and_link(self):
        e = self.by_id["vcal_14076-nevadawolfpack.com"]
        self.assertEqual(e["title"], "Nevada Football vs San José State")
        self.assertEqual(e["venue"]["name"], "Mackay Stadium")
        self.assertEqual(e["start"], "2026-10-24T14:00:00-07:00")
        self.assertEqual(e["end"], "2026-10-24T17:00:00-07:00")
        self.assertEqual(e["links"][0]["url"], "https://nevadawolfpack.com/calendar.aspx?game_id=14076&sport_id=2")
        self.assertEqual(e["area"], "reno")

    def test_result_tag_and_spacing(self):
        e = self.by_id["vcal_14250-nevadawolfpack.com"]
        self.assertEqual(e["title"], "Nevada Women's Basketball vs Sacramento State")
        self.assertEqual(e["venue"]["name"], "Lawlor Events Center")

    def test_time_tba_is_all_day(self):
        e = self.by_id["vcal_14224-nevadawolfpack.com"]
        self.assertTrue(e["allDay"])
        self.assertEqual(e["start"], "2026-11-18T00:00:00-08:00")

    def test_stateline_counts_as_tahoe(self):
        e = self.by_id["vcal_14215-nevadawolfpack.com"]
        self.assertEqual((e["area"], e["drive"]), ("tahoe", "~70 min"))

    def test_no_venue_name(self):
        e = self.by_id["vcal_14290-nevadawolfpack.com"]
        self.assertIsNone(e["venue"]["name"])
        self.assertEqual(e["venue"]["address"], "Reno, NV")

    def test_not_a_calendar_is_a_source_error(self):
        ctx = Context(la(2026, 10, 5), la(2026, 10, 13))
        with mock.patch.object(net, "get_text", lambda url, **kw: "<html>maintenance</html>"):
            with self.assertRaises(SourceError):
                wolfpack.fetch(ctx)

    def test_real_recording_parses(self):
        if not os.path.exists(fixture_path("real/wolfpack.ics")):
            self.skipTest("no real recording yet")
        events = wolfpack.parse(fixture_text("real/wolfpack.ics"))
        self.assertTrue(events)
        self.assertTrue(all(e["area"] in ("reno", "tahoe") for e in events))
        self.assertFalse([e for e in events if e["title"].startswith("[")])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run them to make sure they fail**

Run: `python3 -m unittest discover -s tests -v`
Expected: `ImportError: cannot import name 'wolfpack'`

- [ ] **Step 4: Implement** `collector/sources/wolfpack.py`, and add `wolfpack` to `ALL`

```python
"""Nevada Wolf Pack home games: the athletics site's iCal feed, no key."""

import html
import re
from datetime import datetime

import ical
import net
from model import make_event, venue
from sources.base import SourceError

NAME = "wolfpack"
LABEL = "Nevada Wolf Pack"
URL = "https://nevadawolfpack.com/calendar.ashx/calendar.ics"
HOME = {("reno", "nev."), ("stateline", "nev.")}


def fetch(ctx):
    text = net.get_text(URL)
    if "BEGIN:VCALENDAR" not in text:
        raise SourceError("not an iCal feed")
    return parse(text)


def clean_title(summary):
    s = re.sub(r"^\[[A-Z]\]\s*", "", summary)
    s = re.sub(r"\s+-\s+Presented by:.*$", "", s, flags=re.I)
    return " ".join(s.replace("University of Nevada ", "Nevada ").split())


def parse(text):
    events = []
    for ev in ical.events(text):
        parts = [p.strip() for p in ical.text(ev, "LOCATION").split(",")]
        if len(parts) < 2 or (parts[0].lower(), parts[1].lower()) not in HOME:
            continue
        start = ical.when(ev.get("DTSTART"))
        if start is None:
            continue
        all_day = not isinstance(start, datetime)
        end = ical.when(ev.get("DTEND"))
        events.append(make_event(
            "wolfpack", ical.text(ev, "UID"), clean_title(ical.text(ev, "SUMMARY")), start,
            end=end if (not all_day and isinstance(end, datetime)) else None, all_day=all_day,
            venue=venue(", ".join(p for p in parts[2:] if p) or None, f"{parts[0]}, NV"),
            city=parts[0], url=html.unescape(ical.text(ev, "URL")) or None,
            tags=["sports"], kind="organiser"))
    return events
```

In `collector/sources/__init__.py`: `from sources import unr, wolfpack` and `ALL = [unr, wolfpack]`.

- [ ] **Step 5: Run the tests to make sure they pass**

Run: `python3 -m unittest discover -s tests -v`
Expected: all OK (the recording test is skipped)

- [ ] **Step 6: Record and try it live**

```bash
curl -sS -A "reno-today/1.0 (+https://github.com/natanforestree/reno-today)" \
  "https://nevadawolfpack.com/calendar.ashx/calendar.ics" -o tests/fixtures/real/wolfpack.ics
python3 -m unittest discover -s tests -p test_wolfpack.py -v
python3 dev/try_source.py wolfpack
```
Expected:
- The recording test passes.
- `try_source` prints the home games in the next 8 days. There may be 0–4, and 0 is fine.

- [ ] **Step 7: Commit**

```bash
git add collector/sources/wolfpack.py collector/sources/__init__.py tests/test_wolfpack.py tests/fixtures/wolfpack.ics tests/fixtures/real/wolfpack.ics
git commit -m "Wolf Pack home games from the athletics iCal feed"
```

---

### Task 9: Reno Aces home games (MLB Stats API)

**Files:**
- Create: `collector/sources/aces.py`, `tests/test_aces.py`, `tests/fixtures/aces.json`, `tests/fixtures/real/aces.json` (recorded)
- Modify: `collector/sources/__init__.py`

**Interfaces:**
- Consumes: `net.get_json`, `model.make_event / venue`, `SourceError`
- Produces: `aces.parse(data) -> list[event]`, `NAME = "aces"`

The endpoint is `https://statsapi.mlb.com/api/v1/schedule?sportId=11&teamId=2310&startDate=YYYY-MM-DD&endDate=YYYY-MM-DD` and returns `{"dates": [{"date", "games": [...]}]}`.
- **Home games:** `teams.home.team.id == 2310`.
- **When:** `gameDate` (UTC) and `officialDate` (local date).
- **Status:** `status.detailedState` and `status.startTimeTBD`.
- **Off-season:** the season ends in September, so October returns `"dates": []`. Zero events is a normal result.

- [ ] **Step 1: Write the fixture** `tests/fixtures/aces.json`

```json
{
  "totalGames": 4,
  "dates": [
    {"date": "2026-05-13", "games": [
      {"gamePk": 815155, "gameDate": "2026-05-14T01:05:00Z", "officialDate": "2026-05-13",
       "status": {"detailedState": "Scheduled", "startTimeTBD": false},
       "teams": {"away": {"team": {"id": 400, "name": "Las Vegas Aviators"}}, "home": {"team": {"id": 2310, "name": "Reno Aces"}}},
       "venue": {"id": 3789, "name": "Greater Nevada Field"}},
      {"gamePk": 815999, "gameDate": "2026-05-13T18:05:00Z", "officialDate": "2026-05-13",
       "status": {"detailedState": "Scheduled", "startTimeTBD": false},
       "teams": {"away": {"team": {"id": 2310, "name": "Reno Aces"}}, "home": {"team": {"id": 529, "name": "Sacramento River Cats"}}},
       "venue": {"id": 2529, "name": "Sutter Health Park"}}
    ]},
    {"date": "2026-05-14", "games": [
      {"gamePk": 815156, "gameDate": "2026-05-15T01:05:00Z", "officialDate": "2026-05-14",
       "status": {"detailedState": "Postponed", "startTimeTBD": false},
       "teams": {"away": {"team": {"id": 400, "name": "Las Vegas Aviators"}}, "home": {"team": {"id": 2310, "name": "Reno Aces"}}},
       "venue": {"id": 3789, "name": "Greater Nevada Field"}},
      {"gamePk": 815157, "gameDate": "2026-05-14T07:33:00Z", "officialDate": "2026-05-14",
       "status": {"detailedState": "Scheduled", "startTimeTBD": true},
       "teams": {"away": {"team": {"id": 400, "name": "Las Vegas Aviators"}}, "home": {"team": {"id": 2310, "name": "Reno Aces"}}},
       "venue": {"id": 3789, "name": "Greater Nevada Field"}}
    ]}
  ]
}
```

- [ ] **Step 2: Write the failing tests** `tests/test_aces.py`

```python
import os
import unittest
from unittest import mock

from helpers import fixture_json, fixture_path, la
import net
from sources import aces
from sources.base import Context, SourceError


class AcesTest(unittest.TestCase):
    def setUp(self):
        self.by_id = {e["id"]: e for e in aces.parse(fixture_json("aces.json"))}

    def test_home_games_that_are_on(self):
        self.assertEqual(sorted(self.by_id), ["aces:815155", "aces:815157"])

    def test_game(self):
        e = self.by_id["aces:815155"]
        self.assertEqual(e["title"], "Reno Aces vs Las Vegas Aviators")
        self.assertEqual(e["start"], "2026-05-13T18:05:00-07:00")
        self.assertEqual(e["venue"]["name"], "Greater Nevada Field")
        self.assertEqual(e["venue"]["address"], "250 Evans Ave, Reno, NV 89501")
        self.assertEqual(e["links"][0]["url"], "https://www.milb.com/gameday/815155")
        self.assertTrue(e["_allAges"] and e["_outdoor"])

    def test_time_tbd_is_all_day_on_the_official_date(self):
        e = self.by_id["aces:815157"]
        self.assertTrue(e["allDay"])
        self.assertEqual(e["start"], "2026-05-14T00:00:00-07:00")

    def test_off_season_is_zero_events_not_an_error(self):
        self.assertEqual(aces.parse({"totalGames": 0, "dates": []}), [])

    def test_fetch_asks_for_the_window_and_rejects_reshaped_bodies(self):
        ctx = Context(la(2026, 10, 5), la(2026, 10, 13))
        seen = []
        with mock.patch.object(net, "get_json", lambda url, **kw: seen.append(url) or {"dates": []}):
            self.assertEqual(aces.fetch(ctx), [])
        self.assertIn("startDate=2026-10-05&endDate=2026-10-12", seen[0])
        with mock.patch.object(net, "get_json", lambda url, **kw: {"message": "oops"}):
            with self.assertRaises(SourceError):
                aces.fetch(ctx)

    def test_real_recording_parses(self):
        if not os.path.exists(fixture_path("real/aces.json")):
            self.skipTest("no real recording yet")
        events = aces.parse(fixture_json("real/aces.json"))
        self.assertTrue(events)
        self.assertTrue(all(e["title"].startswith("Reno Aces vs ") for e in events))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run them to make sure they fail**

Run: `python3 -m unittest discover -s tests -v`
Expected: `ImportError: cannot import name 'aces'`

- [ ] **Step 4: Implement** `collector/sources/aces.py`, and add `aces` to `ALL`

```python
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
```

- [ ] **Step 5: Run the tests to make sure they pass**

Run: `python3 -m unittest discover -s tests -v`
Expected: all OK

- [ ] **Step 6: Record a real in-season week, and try it live**

```bash
curl -sS -A "reno-today/1.0 (+https://github.com/natanforestree/reno-today)" \
  "https://statsapi.mlb.com/api/v1/schedule?sportId=11&teamId=2310&startDate=2026-05-12&endDate=2026-05-19" \
  -o tests/fixtures/real/aces.json
python3 -m unittest discover -s tests -p test_aces.py -v
python3 dev/try_source.py aces
```
Expected:
- The recording test passes.
- Live, there are 0 events in October (off-season), and that's fine.

- [ ] **Step 7: Commit**

```bash
git add collector/sources/aces.py collector/sources/__init__.py tests/test_aces.py tests/fixtures/aces.json tests/fixtures/real/aces.json
git commit -m "Reno Aces home games from the MLB Stats API"
```

---

### Task 10: Ticketmaster (Discovery API)

**Files:**
- Create: `collector/sources/ticketmaster.py`, `tests/test_ticketmaster.py`, `tests/fixtures/ticketmaster.json`
- Modify: `collector/sources/__init__.py` (Ticketmaster goes **first** in `ALL`)

**Interfaces:**
- Consumes: `net.get_json(url, label=...)`, `model.make_event / venue / price_range`, `SourceError`
- Produces: `ticketmaster.parse(items) -> list[event]`, `NAME = "ticketmaster"`, ids `tm:<id>`, link source `"tm"`, `_kind = "ticketing"`

The endpoint is `https://app.ticketmaster.com/discovery/v2/events.json?apikey=…&latlong=39.5296,-119.8138&radius=60&unit=miles&locale=*&startDateTime=…Z&endDateTime=…Z&size=200&page=N&sort=date,asc`.
- **Response:** `{"_embedded": {"events": [...]}, "page": {"size", "totalElements", "totalPages", "number"}}`. With no matches, `_embedded` is **absent**.
- **Paging:** deep paging stops at `size * page < 1000`.
- **Limits:** 5,000 calls a day and 5 a second.
- **The key:** it's in the query string. `label="ticketmaster"` keeps it out of errors.
- **Not set up yet:** until Nathan adds the `TICKETMASTER_KEY` secret (Task 21), this source reports "not set up yet", and that's expected.
- **The real recording:** this fixture is hand-made from the documented shape. A real response is recorded in Task 21, once the key exists.

- [ ] **Step 1: Write the fixture** `tests/fixtures/ticketmaster.json`

```json
{
  "_embedded": {"events": [
    {"name": "Brandi Carlile", "id": "G5vYZ9A1", "url": "https://www.ticketmaster.com/event/G5vYZ9A1",
     "dates": {"start": {"localDate": "2026-10-10", "localTime": "19:30:00", "dateTime": "2026-10-11T02:30:00Z", "timeTBA": false, "noSpecificTime": false},
               "status": {"code": "onsale"}},
     "classifications": [{"primary": true, "segment": {"name": "Music"}, "genre": {"name": "Rock"}, "subGenre": {"name": "Pop"}, "family": false}],
     "priceRanges": [{"type": "standard", "currency": "USD", "min": 45.5, "max": 129.0}],
     "ageRestrictions": {"legalAgeEnforced": false},
     "_embedded": {"venues": [{"name": "Grand Sierra Resort and Casino", "city": {"name": "Reno"}, "state": {"stateCode": "NV"},
                               "address": {"line1": "2500 E 2nd St"}, "location": {"longitude": "-119.7762", "latitude": "39.5232"}}]}},
    {"name": "Disney Junior Live On Tour", "id": "G5vYZ9A2", "url": "https://www.ticketmaster.com/event/G5vYZ9A2",
     "dates": {"start": {"localDate": "2026-10-11", "localTime": "14:00:00", "dateTime": "2026-10-11T21:00:00Z"}, "status": {"code": "onsale"}},
     "classifications": [{"primary": true, "segment": {"name": "Arts & Theatre"}, "genre": {"name": "Children's Theatre"}, "subGenre": {"name": "Undefined"}, "family": true}],
     "priceRanges": [{"type": "standard", "currency": "USD", "min": 30.0, "max": 30.0}],
     "_embedded": {"venues": [{"name": "Pioneer Center for the Performing Arts", "city": {"name": "Reno"}, "state": {"stateCode": "NV"},
                               "address": {"line1": "100 S Virginia St"}}]}},
    {"name": "Late Night Comedy", "id": "G5vYZ9A3", "url": "https://www.ticketmaster.com/event/G5vYZ9A3",
     "dates": {"start": {"localDate": "2026-10-10", "dateTime": "2026-10-11T05:00:00Z"}, "status": {"code": "onsale"}},
     "classifications": [{"primary": true, "segment": {"name": "Arts & Theatre"}, "genre": {"name": "Comedy"}}],
     "ageRestrictions": {"legalAgeEnforced": true},
     "_embedded": {"venues": [{"name": "Silver Legacy Resort Casino", "city": {"name": "Reno"}, "state": {"stateCode": "NV"}}]}},
    {"name": "PARKING: Brandi Carlile", "id": "G5vYZ9A4", "url": "https://www.ticketmaster.com/event/G5vYZ9A4",
     "dates": {"start": {"localDate": "2026-10-10", "dateTime": "2026-10-11T02:30:00Z"}, "status": {"code": "onsale"}},
     "_embedded": {"venues": [{"name": "Grand Sierra Resort and Casino", "city": {"name": "Reno"}}]}},
    {"name": "Cancelled Show", "id": "G5vYZ9A5", "url": "https://www.ticketmaster.com/event/G5vYZ9A5",
     "dates": {"start": {"localDate": "2026-10-12", "dateTime": "2026-10-13T03:00:00Z"}, "status": {"code": "cancelled"}},
     "_embedded": {"venues": [{"name": "Reno Events Center", "city": {"name": "Reno"}}]}},
    {"name": "Lake Tahoe Autumn Food & Wine", "id": "G5vYZ9A6", "url": "https://www.ticketmaster.com/event/G5vYZ9A6",
     "dates": {"start": {"localDate": "2026-10-12", "timeTBA": true, "noSpecificTime": true}, "status": {"code": "onsale"}},
     "classifications": [{"primary": true, "segment": {"name": "Miscellaneous"}, "genre": {"name": "Food & Drink"}}],
     "_embedded": {"venues": [{"name": "Tahoe Blue Event Center", "city": {"name": "Stateline"}, "state": {"stateCode": "NV"},
                               "address": {"line1": "55 US-50"}, "location": {"longitude": "-119.9412", "latitude": "38.9623"}}]}}
  ]},
  "page": {"size": 200, "totalElements": 6, "totalPages": 1, "number": 0}
}
```

- [ ] **Step 2: Write the failing tests** `tests/test_ticketmaster.py`

```python
import os
import unittest
from unittest import mock

from helpers import fixture_json, fixture_path, la
import net
from sources import ticketmaster
from sources.base import Context, SourceError

CTX = Context(la(2026, 10, 5), la(2026, 10, 13), {"TICKETMASTER_KEY": "k123"})


class ParseTest(unittest.TestCase):
    def setUp(self):
        self.by_id = {e["id"]: e for e in ticketmaster.parse(fixture_json("ticketmaster.json")["_embedded"]["events"])}

    def test_drops_parking_and_cancelled(self):
        self.assertEqual(sorted(self.by_id), ["tm:G5vYZ9A1", "tm:G5vYZ9A2", "tm:G5vYZ9A3", "tm:G5vYZ9A6"])

    def test_concert(self):
        e = self.by_id["tm:G5vYZ9A1"]
        self.assertEqual(e["start"], "2026-10-10T19:30:00-07:00")
        self.assertEqual(e["price"], {"min": 45.5, "max": 129.0})
        self.assertEqual(e["venue"], {"name": "Grand Sierra Resort and Casino", "address": "2500 E 2nd St, Reno, NV",
                                      "lat": 39.5232, "lon": -119.7762})
        self.assertEqual(e["links"], [{"source": "tm", "url": "https://www.ticketmaster.com/event/G5vYZ9A1"}])
        self.assertEqual(e["_kind"], "ticketing")
        self.assertEqual(e["_tags"], ["music", "pop", "rock"])

    def test_family_and_adult_flags(self):
        self.assertTrue(self.by_id["tm:G5vYZ9A2"]["_family"])
        self.assertIn("children's theatre", self.by_id["tm:G5vYZ9A2"]["_tags"])
        self.assertTrue(self.by_id["tm:G5vYZ9A3"]["_adult"])

    def test_time_tba_is_all_day_and_tahoe(self):
        e = self.by_id["tm:G5vYZ9A6"]
        self.assertTrue(e["allDay"])
        self.assertEqual(e["start"], "2026-10-12T00:00:00-07:00")
        self.assertEqual(e["area"], "tahoe")
        self.assertIsNone(e["price"])


class FetchTest(unittest.TestCase):
    def test_not_set_up_yet(self):
        with self.assertRaises(SourceError) as cm:
            ticketmaster.fetch(Context(la(2026, 10, 5), la(2026, 10, 13), {}))
        self.assertIn("not set up", str(cm.exception))

    def test_window_in_utc_and_paging(self):
        calls = []

        def fake(url, **kw):
            calls.append((url, kw))
            page = int(url.split("&page=")[1].split("&")[0])
            body = fixture_json("ticketmaster.json")
            body["page"] = {"size": 200, "totalElements": 400, "totalPages": 2, "number": page}
            return body

        with mock.patch.object(net, "get_json", fake):
            got = ticketmaster.fetch(CTX)
        self.assertEqual(len(calls), 2)
        self.assertIn("startDateTime=2026-10-05T07:00:00Z", calls[0][0])
        self.assertIn("endDateTime=2026-10-13T07:00:00Z", calls[0][0])
        self.assertEqual(calls[0][1].get("label"), "ticketmaster")
        self.assertEqual(len(got), 8)

    def test_no_matches_is_zero_events(self):
        with mock.patch.object(net, "get_json", lambda url, **kw: {"page": {"size": 200, "totalElements": 0,
                                                                            "totalPages": 0, "number": 0}}):
            self.assertEqual(ticketmaster.fetch(CTX), [])

    def test_reshaped_body_is_a_source_error(self):
        with mock.patch.object(net, "get_json", lambda url, **kw: {"fault": {"faultstring": "Invalid ApiKey"}}):
            with self.assertRaises(SourceError):
                ticketmaster.fetch(CTX)

    def test_real_recording_parses(self):
        if not os.path.exists(fixture_path("real/ticketmaster.json")):
            self.skipTest("recorded in Task 21, once the key exists")
        data = fixture_json("real/ticketmaster.json")
        self.assertNotIn("apikey", str(data).lower())
        events = ticketmaster.parse((data.get("_embedded") or {}).get("events") or [])
        self.assertTrue(events)
        self.assertTrue(all(e["id"].startswith("tm:") for e in events))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run them to make sure they fail**

Run: `python3 -m unittest discover -s tests -v`
Expected: `ImportError: cannot import name 'ticketmaster'`

- [ ] **Step 4: Implement** `collector/sources/ticketmaster.py`, and put it first in `ALL`

```python
"""Ticketmaster Discovery API: concerts, shows, family shows and sports
within ~60 miles of Reno. Needs the TICKETMASTER_KEY secret."""

import re
from datetime import date, datetime

import net
from model import make_event, price_range, utc, venue
from sources.base import SourceError

NAME = "ticketmaster"
LABEL = "Ticketmaster"
URL = ("https://app.ticketmaster.com/discovery/v2/events.json?apikey={key}"
       "&latlong=39.5296,-119.8138&radius=60&unit=miles&locale=*"
       "&startDateTime={start}&endDateTime={end}&size=200&page={page}&sort=date,asc")
MAX_PAGES = 5            # the API refuses size * page beyond 1,000
JUNK = re.compile(r"\b(parking|season tickets?|gift cards?|vip packages?|upgrades?|suite rentals?)\b", re.I)
SKIP_STATUS = {"cancelled", "canceled", "postponed"}
FAMILY = {"family", "children's theatre"}


def fetch(ctx):
    key = ctx.env.get("TICKETMASTER_KEY")
    if not key:
        raise SourceError("not set up yet (TICKETMASTER_KEY missing)")
    items = []
    for page in range(MAX_PAGES):
        data = net.get_json(URL.format(key=key, start=utc(ctx.start), end=utc(ctx.end), page=page),
                            label="ticketmaster")
        if not isinstance(data, dict) or not isinstance(data.get("page"), dict):
            raise SourceError("unexpected response (no page info)")
        items += (data.get("_embedded") or {}).get("events") or []
        info = data["page"]
        if (info.get("number") or 0) + 1 >= (info.get("totalPages") or 0):
            break
    return parse(items)


def _start(dates):
    s = dates.get("start") or {}
    if s.get("dateTime") and not (s.get("timeTBA") or s.get("noSpecificTime")):
        return datetime.fromisoformat(s["dateTime"].replace("Z", "+00:00")), False
    if s.get("localDate") and not (s.get("dateTBD") or s.get("dateTBA")):
        return date.fromisoformat(s["localDate"]), True
    raise ValueError("no usable start")


def parse(items):
    events = []
    for ev in items:
        name = (ev.get("name") or "").strip()
        dates = ev.get("dates") or {}
        if not name or JUNK.search(name):
            continue
        if ((dates.get("status") or {}).get("code") or "").lower() in SKIP_STATUS:
            continue
        try:
            start, all_day = _start(dates)
            end_text = (dates.get("end") or {}).get("dateTime")
            end = datetime.fromisoformat(end_text.replace("Z", "+00:00")) if end_text and not all_day else None
        except ValueError:
            continue
        v = (((ev.get("_embedded") or {}).get("venues")) or [{}])[0]
        city = (v.get("city") or {}).get("name")
        address = ", ".join(p for p in [(v.get("address") or {}).get("line1"), city,
                                        (v.get("state") or {}).get("stateCode")] if p) or None
        loc = v.get("location") or {}
        classes = ev.get("classifications") or []
        cls = next((c for c in classes if c.get("primary")), classes[0] if classes else {})
        tags = [(cls.get(k) or {}).get("name") for k in ("segment", "genre", "subGenre")]
        tags = [t for t in tags if t and t != "Undefined"]
        prices = [p for p in ev.get("priceRanges") or [] if isinstance(p.get("min"), (int, float))]
        price = (price_range(min(p["min"] for p in prices), max(p.get("max", p["min"]) for p in prices))
                 if prices else None)
        events.append(make_event(
            "tm", ev.get("id") or name, name, start, end=end, all_day=all_day,
            venue=venue(v.get("name"), address, loc.get("latitude"), loc.get("longitude")),
            city=city, price=price, url=ev.get("url"),
            text=" ".join(filter(None, [ev.get("info"), ev.get("pleaseNote")])),
            tags=tags, family=bool(cls.get("family")) or bool({t.lower() for t in tags} & FAMILY),
            adult=bool((ev.get("ageRestrictions") or {}).get("legalAgeEnforced")), kind="ticketing"))
    return events
```

In `collector/sources/__init__.py`: `from sources import aces, ticketmaster, unr, wolfpack` and `ALL = [ticketmaster, unr, wolfpack, aces]`.

- [ ] **Step 5: Run the tests to make sure they pass**

Run: `python3 -m unittest discover -s tests -v`
Expected: all OK (the recording test is skipped)

- [ ] **Step 6: Commit**

```bash
git add collector/sources/ticketmaster.py collector/sources/__init__.py tests/test_ticketmaster.py tests/fixtures/ticketmaster.json
git commit -m "Ticketmaster Discovery API source"
```

---

### Task 11: Weather (Open-Meteo)

**Files:**
- Create: `collector/weather.py`, `tests/test_weather.py`

**Interfaces:**
- Consumes: `net.get_json`, `net.FetchError`, `model.utc`
- Produces:
  - `weather.fetch(now) -> dict` (written as `docs/data/weather.json`)
  - `weather.parse(payload, now)`, `weather.nice_windows(hours)`, `weather.describe(code) -> (summary, emoji)`
  - The output shape:
    ```
    {"generatedAt", "days": [{"date", "high", "low", "summary", "emoji", "code", "rain",
      "sunrise": "HH:MM", "sunset": "HH:MM", "nice": [{"from": "HH:00", "to": "HH:00"}],
      "hours": [{"h", "t", "rain"}]}]}
    ```

The request asks for `daily=temperature_2m_max,temperature_2m_min,weather_code,precipitation_probability_max,sunrise,sunset`, `hourly=temperature_2m,precipitation_probability,weather_code,is_day`, Fahrenheit, `timezone=America/Los_Angeles` and `forecast_days=8`.
- Hourly `time` values look like `"2026-10-05T14:00"` (local).
- Daily `sunrise` looks like `"2026-10-05T06:59"`.
- Hourly values can be `null`.

- [ ] **Step 1: Write the failing tests** `tests/test_weather.py`

```python
import unittest
from unittest import mock

from helpers import la
import net
import weather


def payload(temps, rains, days=("2026-10-05",)):
    """A minimal Open-Meteo response: one temps/rains list (24 values) per day."""
    hourly = {"time": [], "temperature_2m": [], "precipitation_probability": [], "weather_code": [], "is_day": []}
    for d, t_list, r_list in zip(days, temps, rains):
        for h in range(24):
            hourly["time"].append(f"{d}T{h:02d}:00")
            hourly["temperature_2m"].append(t_list[h])
            hourly["precipitation_probability"].append(r_list[h])
            hourly["weather_code"].append(0)
            hourly["is_day"].append(1 if 7 <= h <= 18 else 0)
    n = len(days)
    daily = {"time": list(days), "temperature_2m_max": [78.4] * n, "temperature_2m_min": [51.6] * n,
             "weather_code": [61] * n, "precipitation_probability_max": [40] * n,
             "sunrise": [f"{d}T06:59" for d in days], "sunset": [f"{d}T18:35" for d in days]}
    return {"hourly": hourly, "daily": daily}


WARM = [50, 50, 50, 50, 50, 50, 52, 54, 56, 60, 64, 68, 72, 76, 78, 80, 84, 86, 82, 70, 60, 55, 52, 50]
DRY = [0] * 24


class WeatherTest(unittest.TestCase):
    def test_nice_window_needs_daylight_temperature_and_dry(self):
        day = weather.parse(payload([WARM], [DRY]), la(2026, 10, 5, 7))["days"][0]
        # 08:00 (56°) through 16:00 (84°); 17:00 is 86° (too hot); 18:00 is 82° but a lone hour.
        self.assertEqual(day["nice"], [{"from": "08:00", "to": "17:00"}])

    def test_rain_breaks_the_window(self):
        rain = list(DRY)
        rain[12] = rain[13] = 60
        day = weather.parse(payload([WARM], [rain]), la(2026, 10, 5, 7))["days"][0]
        self.assertEqual(day["nice"], [{"from": "08:00", "to": "12:00"}, {"from": "14:00", "to": "17:00"}])

    def test_missing_values_are_not_nice(self):
        temps = list(WARM)
        temps[10] = None
        rains = list(DRY)
        rains[14] = None
        day = weather.parse(payload([temps], [rains]), la(2026, 10, 5, 7))["days"][0]
        self.assertEqual(day["nice"], [{"from": "08:00", "to": "10:00"}, {"from": "11:00", "to": "14:00"},
                                       {"from": "15:00", "to": "17:00"}])

    def test_daily_fields(self):
        out = weather.parse(payload([WARM], [DRY]), la(2026, 10, 5, 7))
        self.assertEqual(out["generatedAt"], "2026-10-05T14:00:00Z")
        day = out["days"][0]
        self.assertEqual((day["date"], day["high"], day["low"]), ("2026-10-05", 78, 52))
        self.assertEqual((day["summary"], day["emoji"], day["rain"]), ("Rain", "🌧️", 40))
        self.assertEqual((day["sunrise"], day["sunset"]), ("06:59", "18:35"))
        self.assertEqual(day["hours"][14], {"h": 14, "t": 78, "rain": 0})

    def test_describe(self):
        self.assertEqual(weather.describe(0), ("Clear", "☀️"))
        self.assertEqual(weather.describe(2), ("Partly cloudy", "⛅"))
        self.assertEqual(weather.describe(75), ("Snow", "🌨️"))
        self.assertEqual(weather.describe(95), ("Thunderstorms", "⛈️"))
        self.assertEqual(weather.describe(None), ("Unknown", "🌡️"))

    def test_reshaped_response_is_a_fetch_error(self):
        with mock.patch.object(net, "get_json", lambda url, **kw: {"error": True, "reason": "nope"}):
            with self.assertRaises(net.FetchError):
                weather.fetch(la(2026, 10, 5, 7))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run them to make sure they fail**

Run: `python3 -m unittest discover -s tests -v`
Expected: `ModuleNotFoundError: No module named 'weather'`

- [ ] **Step 3: Implement** `collector/weather.py`

```python
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
```

- [ ] **Step 4: Run the tests to make sure they pass**

Run: `python3 -m unittest discover -s tests -v`
Expected: all OK

- [ ] **Step 5: Commit**

```bash
git add collector/weather.py tests/test_weather.py
git commit -m "Weather: Open-Meteo days, hours and nice-outside windows"
```

---

### Task 12: Loving Reno guide card

**Files:**
- Create: `collector/guide.py`, `tests/test_guide.py`, `tests/fixtures/lovingreno.xml`

**Interfaces:**
- Consumes: `net.get_text`, `net.FetchError`
- Produces:
  - `guide.fetch() -> {"title", "shortTitle", "url", "published"} | None`, written as `docs/data/guide.json`
  - `guide.parse(xml_text)`, `guide.short_title(title)`
  - Phase 3 (Task 28) adds `guide.badges(...)`

The source is Loving Reno's Blogger feed `https://www.lovingreno.com/feeds/posts/summary?max-results=10` (Atom, about 18 KB). It is small, so we never read the full-content feed here. Their `robots.txt` is empty, which allows everything. Titles are long, e.g. "2026 Ultimate Reno Halloween & Fall Guide: Haunted Houses, …", so `shortTitle` cuts at the first colon. We store only the title, URL and date.

- [ ] **Step 1: Write the fixture** `tests/fixtures/lovingreno.xml`

```xml
<?xml version='1.0' encoding='UTF-8'?>
<feed xmlns='http://www.w3.org/2005/Atom'>
  <title>Loving Reno</title>
  <entry>
    <published>2026-08-23T10:00:00.000-07:00</published>
    <title type='text'>Hawk Fire: Reno Evacuations, Maps, Shelters &amp; Emergency Resources</title>
    <link rel='alternate' type='text/html' href='https://www.lovingreno.com/2026/08/hawk-fire-reno-evacuations-maps.html'/>
  </entry>
  <entry>
    <published>2026-09-24T09:00:00.000-07:00</published>
    <title type='text'>2026 Ultimate Reno Halloween &amp; Fall Guide: Haunted Houses, Fall Foliage, Workshops</title>
    <link rel='replies' type='text/html' href='https://www.lovingreno.com/2026/09/x.html#comment-form'/>
    <link rel='alternate' type='text/html' href='https://www.lovingreno.com/2026/09/2026-reno-halloween-fall-guide-haunted.html'/>
  </entry>
  <entry>
    <published>2026-06-23T09:00:00.000-07:00</published>
    <title type='text'>The Ultimate Reno Summer Guide 2026: Local Events, Things to Do</title>
    <link rel='alternate' type='text/html' href='https://www.lovingreno.com/2026/06/the-ultimate-reno-summer-guide-2026.html'/>
  </entry>
</feed>
```

- [ ] **Step 2: Write the failing tests** `tests/test_guide.py`

```python
import unittest

from helpers import fixture_text
import guide
import net


class GuideTest(unittest.TestCase):
    def test_newest_guide_wins(self):
        g = guide.parse(fixture_text("lovingreno.xml"))
        self.assertEqual(g, {
            "title": "2026 Ultimate Reno Halloween & Fall Guide: Haunted Houses, Fall Foliage, Workshops",
            "shortTitle": "2026 Ultimate Reno Halloween & Fall Guide",
            "url": "https://www.lovingreno.com/2026/09/2026-reno-halloween-fall-guide-haunted.html",
            "published": "2026-09-24",
        })

    def test_newest_post_when_no_guide(self):
        xml = fixture_text("lovingreno.xml").replace("Guide", "Roundup")
        self.assertEqual(guide.parse(xml)["published"], "2026-09-24")

    def test_empty_feed(self):
        self.assertIsNone(guide.parse("<feed xmlns='http://www.w3.org/2005/Atom'></feed>"))

    def test_broken_xml_is_a_fetch_error(self):
        with self.assertRaises(net.FetchError):
            guide.parse("<html>oops")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run them to make sure they fail**

Run: `python3 -m unittest discover -s tests -v`
Expected: `ModuleNotFoundError: No module named 'guide'`

- [ ] **Step 4: Implement** `collector/guide.py`

```python
"""Loving Reno (lovingreno.com): their current seasonal guide, linked and never
copied. We keep only its title, URL and date."""

import xml.etree.ElementTree as ET

import net

FEED = "https://www.lovingreno.com/feeds/posts/summary?max-results=10"
ATOM = "{http://www.w3.org/2005/Atom}"


def short_title(title):
    return title.split(":")[0].strip()[:90]


def parse(xml_text):
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as err:
        raise net.FetchError("lovingreno feed", f"bad XML: {err}") from None
    posts = []
    for entry in root.findall(f"{ATOM}entry"):
        title = " ".join((entry.findtext(f"{ATOM}title") or "").split())
        url = next((link.get("href") for link in entry.findall(f"{ATOM}link")
                    if link.get("rel") == "alternate"), None)
        if title and url and url.startswith("https://"):
            posts.append({"title": title, "shortTitle": short_title(title), "url": url,
                          "published": (entry.findtext(f"{ATOM}published") or "")[:10]})
    posts.sort(key=lambda p: p["published"], reverse=True)
    guides = [p for p in posts if "guide" in p["title"].lower()]
    return (guides or posts or [None])[0]


def fetch():
    return parse(net.get_text(FEED))
```

- [ ] **Step 5: Run the tests to make sure they pass**

Run: `python3 -m unittest discover -s tests -v`
Expected: all OK

- [ ] **Step 6: Commit**

```bash
git add collector/guide.py tests/test_guide.py tests/fixtures/lovingreno.xml
git commit -m "Loving Reno guide card from their feed (title and link only)"
```

---

### Task 13: `store.py` (files, run state, last-good per source)

**Files:**
- Create: `collector/store.py`, `tests/test_store.py`

**Interfaces:**
- Consumes: `model.utc`
- Produces:
  - `store.Store(root)` with:
    - `.read(rel, default=None)` and `.write(rel, obj)` (atomic, UTF-8, `indent=1`, trailing newline)
    - `.last_refresh() -> datetime|None` and `.set_last_refresh(now)`
    - `.digest_date() -> str|None` and `.set_digest_date(day)`
    - `.remember(name, events, now)`
    - `.last_good(name, now) -> (events, at|None)`: events are `[]` when older than 24 h
  - `store.parse_time(s)`
  - `store.KEEP_LAST_GOOD = timedelta(hours=24)`

- [ ] **Step 1: Write the failing tests** `tests/test_store.py`

```python
import json
import os
import tempfile
import unittest
from datetime import timedelta

from helpers import la
import store


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.s = store.Store(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_write_is_atomic_json_with_a_trailing_newline(self):
        self.s.write("docs/data/x.json", {"é": 1})
        path = os.path.join(self.tmp.name, "docs/data/x.json")
        with open(path, encoding="utf-8") as f:
            text = f.read()
        self.assertTrue(text.endswith("\n"))
        self.assertIn("é", text)
        self.assertFalse(os.path.exists(path + ".tmp"))
        self.assertEqual(self.s.read("docs/data/x.json"), {"é": 1})

    def test_missing_or_broken_files_read_as_default(self):
        self.assertEqual(self.s.read("nope.json", []), [])
        os.makedirs(os.path.join(self.tmp.name, "state"))
        with open(os.path.join(self.tmp.name, "state/refresh.json"), "w") as f:
            f.write("{broken")
        self.assertIsNone(self.s.last_refresh())

    def test_run_state(self):
        now = la(2026, 10, 10, 7, 31)
        self.assertIsNone(self.s.last_refresh())
        self.s.set_last_refresh(now)
        self.assertEqual(self.s.last_refresh(), now)
        self.assertEqual(self.s.read("state/refresh.json"), {"at": "2026-10-10T14:31:00Z"})
        self.assertIsNone(self.s.digest_date())
        self.s.set_digest_date("2026-10-10")
        self.assertEqual(self.s.digest_date(), "2026-10-10")

    def test_last_good_expires_after_24_hours(self):
        now = la(2026, 10, 10, 7, 31)
        self.s.remember("unr", [{"id": "unr:1"}], now)
        self.assertEqual(self.s.last_good("unr", now + timedelta(hours=23)), ([{"id": "unr:1"}], now))
        events, at = self.s.last_good("unr", now + timedelta(hours=25))
        self.assertEqual((events, at), ([], now))
        self.assertEqual(self.s.last_good("never", now), ([], None))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run them to make sure they fail**

Run: `python3 -m unittest discover -s tests -v`
Expected: `ModuleNotFoundError: No module named 'store'`

- [ ] **Step 3: Implement** `collector/store.py`

```python
"""The repo's JSON files: docs/data/ for the page, state/ for the collector's
memory between runs (last refresh, digest date, last good events per source)."""

import json
import os
from datetime import datetime, timedelta

from model import utc

KEEP_LAST_GOOD = timedelta(hours=24)


def parse_time(value):
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None


class Store:
    def __init__(self, root):
        self.root = root

    def path(self, rel):
        return os.path.join(self.root, rel)

    def read(self, rel, default=None):
        try:
            with open(self.path(rel), encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, ValueError):
            return default

    def write(self, rel, obj):
        path = self.path(rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path + ".tmp", "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=1)
            f.write("\n")
        os.replace(path + ".tmp", path)

    def last_refresh(self):
        return parse_time((self.read("state/refresh.json") or {}).get("at"))

    def set_last_refresh(self, now):
        self.write("state/refresh.json", {"at": utc(now)})

    def digest_date(self):
        return (self.read("state/digest.json") or {}).get("date")

    def set_digest_date(self, day):
        self.write("state/digest.json", {"date": day})

    def remember(self, name, events, now):
        self.write(f"state/sources/{name}.json", {"at": utc(now), "events": events})

    def last_good(self, name, now):
        """(events, saved_at). Events are [] once they're older than KEEP_LAST_GOOD."""
        saved = self.read(f"state/sources/{name}.json") or {}
        at = parse_time(saved.get("at"))
        if at is None or now - at > KEEP_LAST_GOOD:
            return [], at
        return saved.get("events") or [], at
```

- [ ] **Step 4: Run the tests to make sure they pass**

Run: `python3 -m unittest discover -s tests -v`
Expected: all OK

- [ ] **Step 5: Commit**

```bash
git add collector/store.py tests/test_store.py
git commit -m "Store: JSON files, run state and last-good events"
```

---

### Task 14: Places and the Discord digest

**Files:**
- Create: `collector/places.py`, `collector/digest.py`, `tests/test_places.py`, `tests/test_digest.py`

**Interfaces:**
- Consumes: `net.post_json`, `net.FetchError`, `model.LOCAL_AREAS`, finalized event dicts (no `_` fields), weather day dicts (Task 11), the guide dict (Task 12), and place dicts (Task 22's shape).
- Produces:
  - `places.WEEKDAYS`
  - `places.hours_on(place, day) -> str | None`
  - `places.open_on(places, day) -> [(place, hours)]`
  - `places.short_hours(hours) -> str`
  - `digest.build(day, events, wx_day, places, guide, page_url=PAGE_URL) -> str` (≤ 2,000 chars)
  - `digest.post(webhook_url, text) -> bool`
  - `digest.on_day(event, day) -> bool`, `digest.fmt_time(event)`, `digest.PAGE_URL`, `digest.LIMIT`

**Place shape** (`places.json`, filled in Task 22):
```
{"name", "area", "goodFor", "setting": "indoor|outdoor|both",
 "hours": {"mon": "10:00-17:00" | "dawn-dusk" | null, … "sun"},
 "months": [5,6,…] | null, "free": bool, "url", "address", "notes"}
```

- [ ] **Step 1: Write the failing tests** `tests/test_places.py`

```python
import unittest

import helpers  # noqa: F401
import places

DISCOVERY = {"name": "The Discovery", "hours": {"mon": None, "tue": "10:00-17:00", "wed": "10:00-20:00",
                                                "sat": "09:30-16:00", "sun": "12:00-17:00"}}
SPLASH = {"name": "Splash Pad", "months": [6, 7, 8], "hours": {d: "11:00-19:00" for d in places.WEEKDAYS}}
PARK = {"name": "Idlewild Park", "hours": {d: "dawn-dusk" for d in places.WEEKDAYS}}


class PlacesTest(unittest.TestCase):
    def test_hours_on_weekday(self):
        self.assertIsNone(places.hours_on(DISCOVERY, "2026-10-05"))           # Monday: closed
        self.assertEqual(places.hours_on(DISCOVERY, "2026-10-06"), "10:00-17:00")
        self.assertIsNone(places.hours_on(DISCOVERY, "2026-10-08"))           # Thursday: not listed

    def test_out_of_season(self):
        self.assertIsNone(places.hours_on(SPLASH, "2026-10-06"))
        self.assertEqual(places.hours_on(SPLASH, "2026-07-07"), "11:00-19:00")

    def test_open_on(self):
        self.assertEqual([p["name"] for p, _ in places.open_on([DISCOVERY, SPLASH, PARK], "2026-10-06")],
                         ["The Discovery", "Idlewild Park"])

    def test_short_hours(self):
        self.assertEqual(places.short_hours("10:00-17:00"), "10–5")
        self.assertEqual(places.short_hours("09:30-16:00"), "9:30–4")
        self.assertEqual(places.short_hours("12:00-17:00"), "12–5")
        self.assertEqual(places.short_hours("dawn-dusk"), "dawn–dusk")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Write the failing tests** `tests/test_digest.py`

```python
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from helpers import la
import classify
import digest
import model
import net

DAY = "2026-10-10"   # a Saturday


def ev(title, hh, mm=0, area_city="Reno", venue_name="Somewhere", free=False, day=10, **kw):
    e = model.make_event("x", f"{title}{hh}", title, la(2026, 10, day, hh, mm), city=area_city,
                         venue=model.venue(venue_name, "addr"), price=model.FREE if free else None, **kw)
    return model.finalize(classify.classify(e))


WX = {"date": DAY, "high": 78.4, "low": 63.6, "summary": "Clear", "emoji": "☀️"}
GUIDE = {"title": "2026 Ultimate Reno Halloween & Fall Guide: Haunted Houses", "shortTitle": "2026 Ultimate Reno Halloween & Fall Guide",
         "url": "https://www.lovingreno.com/x.html", "published": "2026-09-24"}
PLACES = [{"name": "The Discovery", "hours": {"sat": "10:00-17:00"}},
          {"name": "Idlewild Park", "hours": {"sat": "dawn-dusk"}},
          {"name": "Closed Place", "hours": {"sat": None}}]


class FormatTest(unittest.TestCase):
    def test_fmt_time(self):
        self.assertEqual(digest.fmt_time(ev("A", 10, 30)), "10:30am")
        self.assertEqual(digest.fmt_time(ev("A", 13, 5)), "1:05pm")
        self.assertEqual(digest.fmt_time(ev("A", 19)), "7pm")
        self.assertEqual(digest.fmt_time(ev("A", 0, 15)), "12:15am")
        self.assertEqual(digest.fmt_time(ev("A", 12)), "12pm")


class BuildTest(unittest.TestCase):
    def test_full_example(self):
        events = [
            ev("Baby & Toddler Storytime", 10, 30, venue_name="Downtown Reno Library", free=True),
            ev("Reno Aces vs Sacramento", 13, 5, venue_name="Greater Nevada Field"),
            ev("Lake Tahoe Oktoberfest", 11, area_city="Tahoe City", venue_name="Commons Beach"),
            ev("Tomorrow's Thing", 9, day=11),
        ]
        text = digest.build(DAY, events, WX, PLACES, GUIDE)
        self.assertEqual(text, "\n".join([
            "☀️ Saturday, Oct 10 · 64° → 78°, clear",
            "👶 For little ones",
            "• 10:30am Baby & Toddler Storytime · Downtown Reno Library · free",
            "🎟️ Also today",
            "• 1:05pm Reno Aces vs Sacramento · Greater Nevada Field",
            "🚗 Worth the drive",
            "• 11am Lake Tahoe Oktoberfest (Lake Tahoe, ~55 min)",
            "🏠 Always an option: The Discovery 10–5 · Idlewild Park",
            "📖 Loving Reno: 2026 Ultimate Reno Halloween & Fall Guide",
            "Full list → https://natanforestree.github.io/reno-today/",
        ]))

    def test_empty_sections_are_skipped_and_always_an_option_hides_with_3_little(self):
        little = [ev(f"Storytime {i}", 9 + i) for i in range(3)]
        text = digest.build(DAY, little, None, PLACES, None)
        self.assertTrue(text.startswith("📅 Saturday, Oct 10\n👶 For little ones\n"))
        self.assertNotIn("Also today", text)
        self.assertNotIn("Worth the drive", text)
        self.assertNotIn("Always an option", text)
        self.assertNotIn("Loving Reno", text)

    def test_nothing_today(self):
        text = digest.build(DAY, [], WX, [], None)
        self.assertIn("Nothing listed for today yet.", text)

    def test_also_today_prefers_free_all_ages_daytime_and_puts_21_plus_last(self):
        events = [ev("Club Night", 22, text="21+ only"), ev("Evening Concert", 19), ev("Free Day Fair", 11, free=True),
                  ev("Ballgame", 13, all_ages=True)]
        lines = digest.build(DAY, events, None, [], None).splitlines()
        also = [l for l in lines if l.startswith("•")]
        self.assertEqual([l.split(" ", 2)[2].split(" ·")[0] for l in also],
                         ["Free Day Fair", "Ballgame", "Evening Concert", "Club Night"])

    def test_at_most_five_per_section(self):
        events = [ev(f"Show {i}", 12 + (i % 8), i) for i in range(12)]
        text = digest.build(DAY, events, None, [], None)
        self.assertEqual(sum(1 for l in text.splitlines() if l.startswith("•")), 5)

    def test_trimmed_to_2000_characters(self):
        long = "Very " * 60
        events = ([ev(f"{long}{i}", 9 + i % 10, i) for i in range(15)]
                  + [ev(f"Storytime {long}{i}", 8, i) for i in range(15)]
                  + [ev(f"Tahoe {long}{i}", 9 + i % 10, i, area_city="Truckee") for i in range(15)])
        text = digest.build(DAY, events, WX, PLACES, GUIDE)
        self.assertLessEqual(len(text), digest.LIMIT)
        self.assertLess(sum(1 for l in text.splitlines() if l.startswith("•")), 15, "sections were cut")
        self.assertTrue(text.endswith(digest.PAGE_URL), "the link survives trimming")

    def test_a_weekend_festival_is_in_each_days_digest_but_a_late_show_is_not(self):
        fest = model.finalize(classify.classify(model.make_event(
            "x", "f", "Great Italian Festival", la(2026, 10, 9).date(), end=la(2026, 10, 11).date(),
            all_day=True, city="Reno")))
        self.assertIn("Great Italian Festival", digest.build(DAY, [fest], None, [], None))
        late = ev("Late Show", 21)
        late["end"] = "2026-10-11T01:00:00-07:00"
        self.assertNotIn("Late Show", digest.build("2026-10-11", [late], None, [], None))

    def test_ongoing_events_are_left_out(self):
        exhibit = ev("Exhibit", 10)
        exhibit["ongoing"] = True
        self.assertNotIn("Exhibit", digest.build(DAY, [exhibit], None, [], None))


class Hook(BaseHTTPRequestHandler):
    status = 200
    received = None
    query = None

    def log_message(self, *a):
        pass

    def do_POST(self):
        Hook.query = self.path.split("?", 1)[1] if "?" in self.path else ""
        Hook.received = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        body = b"{}"
        self.send_response(Hook.status)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class PostTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Hook)
        cls.url = f"http://127.0.0.1:{cls.server.server_port}/api/webhooks/1/token"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        net.RETRY_PAUSE = 0

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_posts_plain_content_without_pings(self):
        Hook.status = 200
        self.assertTrue(digest.post(self.url, "hello @everyone"))
        self.assertEqual(Hook.received["content"], "hello @everyone")
        self.assertEqual(Hook.received["allowed_mentions"], {"parse": []})
        self.assertEqual(Hook.received["flags"], 4)
        self.assertEqual(Hook.query, "wait=true")

    def test_deleted_or_rate_limited_webhook_returns_false(self):
        for status in (404, 429):
            Hook.status = status
            self.assertFalse(digest.post(self.url, "hi"))

    def test_no_webhook(self):
        self.assertFalse(digest.post("", "hi"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run them to make sure they fail**

Run: `python3 -m unittest discover -s tests -v`
Expected: `ModuleNotFoundError: No module named 'places'` (and `'digest'`)

- [ ] **Step 4: Implement** `collector/places.py`

```python
"""The "Always an option" list: which standing places are open on a given day."""

from datetime import date

WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def hours_on(place, day):
    """That day's hours ('10:00-17:00' or 'dawn-dusk'), or None when closed or out of season."""
    d = date.fromisoformat(day)
    months = place.get("months")
    if months and d.month not in months:
        return None
    return (place.get("hours") or {}).get(WEEKDAYS[d.weekday()])


def open_on(places, day):
    return [(p, h) for p in places if (h := hours_on(p, day))]


def _clock(hhmm):
    h, m = (int(x) for x in hhmm.split(":"))
    return f"{h % 12 or 12}" if m == 0 else f"{h % 12 or 12}:{m:02d}"


def short_hours(hours):
    """'10:00-17:00' -> '10–5', '09:30-16:00' -> '9:30–4', 'dawn-dusk' -> 'dawn–dusk'."""
    start, _, end = hours.partition("-")
    if ":" not in start or ":" not in end:
        return hours.replace("-", "–")
    return f"{_clock(start)}–{_clock(end)}"
```

- [ ] **Step 5: Implement** `collector/digest.py`

```python
"""The 07:xx Discord message (spec: "Discord digest"): today's picks as plain
text, at most 2,000 characters, then a link to the full page."""

from datetime import date, datetime, timedelta

import net
from model import LOCAL_AREAS
from places import open_on, short_hours

PAGE_URL = "https://natanforestree.github.io/reno-today/"
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


def build(day, events, wx, places, guide, page_url=PAGE_URL):
    todays = [e for e in events if on_day(e, day) and not e["ongoing"]]
    local = [e for e in todays if e["area"] in LOCAL_AREAS]
    little = sorted((e for e in local if e["tier"] == "little"), key=lambda e: e["start"])
    also = sorted((e for e in local if e["tier"] != "little"), key=_also_rank)
    drive = sorted((e for e in todays if e["area"] not in LOCAL_AREAS),
                   key=lambda e: (e["tier"] != "little", e["start"]))
    options = open_on(places or [], day) if len(little) < 3 else []
    text = ""
    for cap in range(PER_SECTION, 0, -1):
        text = _render(day, wx, little, also, drive, options, guide, page_url, cap)
        if len(text) <= LIMIT:
            return text
    footer = f"\nFull list → {page_url}"
    return text[:LIMIT - len(footer) - 1] + "…" + footer


def _render(day, wx, little, also, drive, options, guide, page_url, cap):
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
    lines.append(f"Full list → {page_url}")
    return "\n".join(lines)


def post(webhook_url, text):
    """Send the message. True when Discord accepted it."""
    if not webhook_url:
        return False
    sep = "&" if "?" in webhook_url else "?"
    try:
        status = net.post_json(f"{webhook_url}{sep}wait=true",
                               {"content": text, "allowed_mentions": {"parse": []}, "flags": 4},
                               label="discord webhook")
    except net.FetchError as err:
        print(f"digest: {err}")
        return False
    return 200 <= status < 300
```

`flags: 4` is Discord's SUPPRESS_EMBEDS, so the page link doesn't add a big preview card. `allowed_mentions: {"parse": []}` stops an event title like "@everyone" from pinging anyone.

- [ ] **Step 6: Run the tests to make sure they pass**

Run: `python3 -m unittest discover -s tests -v`
Expected: all OK. If `test_full_example` differs, compare it line by line with the spec's example. The intended differences are only the am/pm times and the bulleted "Worth the drive" with a start time and the area name instead of the town (see "Deliberate differences" #2 and #3). Fix the code, not the expected text, unless the difference is one of those.

- [ ] **Step 7: Commit**

```bash
git add collector/places.py collector/digest.py tests/test_places.py tests/test_digest.py
git commit -m "Discord digest and the places-open helper"
```

---

### Task 15: `collect.py` (the run)

**Files:**
- Create: `collector/collect.py`, `tests/test_collect.py`

**Interfaces:**
- Consumes everything above:
  - `schedule.decide`
  - `model.window / in_window / finalize / utc / LA`
  - `dedupe.dedupe`
  - `classify.classify / load_overrides / apply_overrides`
  - `weather.fetch(now)`
  - `guide.fetch()`
  - `digest.build / post`
  - `store.Store`
  - `sources.ALL`
  - `sources.base.Context / SourceError`
  - `net.FetchError`
- Produces:
  - `collect.run(root, now, env, srcs=None, post=None) -> schedule.Decision`
  - `collect.collect_sources(srcs, ctx, store, now, previous) -> (raw_events, status)`
  - `collect.build_events(raw, ctx, overrides) -> list[finalized event]`
  - `collect.main()`
  - Files written:
    - `docs/data/events.json`: `{generatedAt, timezone, events}`
    - `docs/data/status.json`: `{generatedAt, sources: {name: {label, ok, count, lastSuccess, error}}}`
    - `docs/data/weather.json`, `docs/data/guide.json`, `docs/data/places.json`
    - `state/*`

**Rules** (spec: "Architecture", "Errors"):
- **Each source is independent.** A failure keeps that source's last-good events for up to 24 h and marks it in `status`.
- **A crash in one source's parser** is caught, printed and reported as a failure. It never stops the others.
- **If every source failed and nothing is left,** keep the previous `events.json`.
- **Weather and guide failures** keep the previous files.
- **`EVERY`:** a source with `EVERY` whose saved result is younger than that is not fetched. Its saved events are reused, and it shows as ok.
- **Digest:** sent after the files are written. The date is recorded only when `post` returns True.
- **`FORCE_DIGEST=true`** in the environment (the workflow's manual input) sends the digest right away.

- [ ] **Step 1: Write the failing tests** `tests/test_collect.py`

```python
import json
import os
import tempfile
import unittest
from datetime import timedelta
from types import SimpleNamespace
from unittest import mock

from helpers import la
import collect
import guide
import model
import net
import weather
from sources.base import SourceError

NOW = la(2026, 10, 10, 7, 31)     # Saturday, digest time


def fake_source(name, events=None, error=None, every=None):
    def fetch(ctx):
        if error:
            raise error
        return [dict(e) for e in events or []]
    src = SimpleNamespace(NAME=name, LABEL=name.title(), fetch=mock.Mock(side_effect=fetch))
    if every:
        src.EVERY = every
    return src


def storytime(day=10):
    return model.make_event("lib", f"st{day}", "Baby Storytime", la(2026, 10, day, 10, 30), city="Reno",
                            venue=model.venue("Sparks Library", "1125 12th St"), price=model.FREE,
                            url="https://example.org/st", text="For babies and caregivers")


def concert():
    return model.make_event("tm", "c1", "Big Concert", la(2026, 10, 10, 20), city="Reno",
                            venue=model.venue("GSR", "2500 E 2nd St"), kind="ticketing")


WX = {"generatedAt": "x", "days": [{"date": "2026-10-10", "high": 70, "low": 50, "summary": "Clear", "emoji": "☀️",
                                    "nice": [], "hours": []}]}
GUIDE = {"title": "Fall Guide", "shortTitle": "Fall Guide", "url": "https://www.lovingreno.com/g.html",
         "published": "2026-09-24"}


class CollectTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.sent = []
        self.patches = [mock.patch.object(weather, "fetch", lambda now: WX),
                        mock.patch.object(guide, "fetch", lambda: GUIDE)]
        for p in self.patches:
            p.start()
        with open(os.path.join(self.root, "places.json"), "w") as f:
            json.dump([{"name": "Idlewild Park", "hours": {"sat": "dawn-dusk"}}], f)

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def read(self, rel):
        with open(os.path.join(self.root, rel), encoding="utf-8") as f:
            return json.load(f)

    def post_ok(self, url, text):
        self.sent.append(text)
        return True

    def test_refresh_writes_every_file_and_sends_the_digest(self):
        env = {"DISCORD_WEBHOOK_URL": "https://discord.example/hook"}
        d = collect.run(self.root, NOW, env, srcs=[fake_source("lib", [storytime()]), fake_source("tm", [concert()])],
                        post=self.post_ok)
        self.assertTrue(d.refresh and d.digest)
        events = self.read("docs/data/events.json")
        self.assertEqual(events["generatedAt"], "2026-10-10T14:31:00Z")
        self.assertEqual([e["title"] for e in events["events"]], ["Baby Storytime", "Big Concert"])
        self.assertEqual(events["events"][0]["tier"], "little")
        self.assertFalse([k for e in events["events"] for k in e if k.startswith("_")], "no private fields")
        self.assertNotIn("For babies and caregivers", json.dumps(events), "no write-ups")
        status = self.read("docs/data/status.json")["sources"]
        self.assertEqual(status["lib"], {"label": "Lib", "ok": True, "count": 1,
                                         "lastSuccess": "2026-10-10T14:31:00Z", "error": None})
        self.assertTrue(status["weather"]["ok"] and status["lovingreno"]["ok"])
        self.assertEqual(self.read("docs/data/weather.json"), WX)
        self.assertEqual(self.read("docs/data/guide.json"), GUIDE)
        self.assertEqual(self.read("docs/data/places.json")[0]["name"], "Idlewild Park")
        self.assertEqual(self.read("state/digest.json"), {"date": "2026-10-10"})
        self.assertEqual(len(self.sent), 1)
        self.assertIn("Baby Storytime", self.sent[0])

    def test_next_hour_does_nothing(self):
        env = {"DISCORD_WEBHOOK_URL": "https://discord.example/hook"}
        src = fake_source("lib", [storytime()])
        collect.run(self.root, NOW, env, srcs=[src], post=self.post_ok)
        d = collect.run(self.root, NOW + timedelta(hours=1), env, srcs=[src], post=self.post_ok)
        self.assertFalse(d.refresh or d.digest)
        self.assertEqual(src.fetch.call_count, 1)
        self.assertEqual(len(self.sent), 1)

    def test_failed_post_keeps_data_and_retries_next_hour(self):
        env = {"DISCORD_WEBHOOK_URL": "https://discord.example/hook"}
        collect.run(self.root, NOW, env, srcs=[fake_source("lib", [storytime()])], post=lambda u, t: False)
        self.assertTrue(os.path.exists(os.path.join(self.root, "docs/data/events.json")))
        self.assertFalse(os.path.exists(os.path.join(self.root, "state/digest.json")))
        d = collect.run(self.root, NOW + timedelta(hours=1), env, srcs=[fake_source("lib", [storytime()])],
                        post=self.post_ok)
        self.assertTrue(d.digest)
        self.assertEqual(self.read("state/digest.json"), {"date": "2026-10-10"})

    def test_failing_source_keeps_its_last_good_events(self):
        collect.run(self.root, NOW, {}, srcs=[fake_source("lib", [storytime()])])
        later = NOW + timedelta(hours=3)
        collect.run(self.root, later, {}, srcs=[fake_source("lib", error=net.FetchError("lib", "HTTP 503", 503))])
        self.assertEqual([e["title"] for e in self.read("docs/data/events.json")["events"]], ["Baby Storytime"])
        status = self.read("docs/data/status.json")["sources"]["lib"]
        self.assertEqual((status["ok"], status["count"], status["error"]), (False, 1, "HTTP 503 (lib)"))
        self.assertEqual(status["lastSuccess"], "2026-10-10T14:31:00Z")

    def test_parser_crash_is_contained(self):
        collect.run(self.root, NOW, {}, srcs=[fake_source("bad", error=KeyError("boom")),
                                               fake_source("lib", [storytime()])])
        status = self.read("docs/data/status.json")["sources"]
        self.assertEqual(status["bad"]["error"], "collector error: KeyError")
        self.assertTrue(status["lib"]["ok"])

    def test_every_source_failing_keeps_the_previous_events_file(self):
        collect.run(self.root, NOW, {}, srcs=[fake_source("lib", [storytime()])])
        before = self.read("docs/data/events.json")
        much_later = NOW + timedelta(days=2)
        collect.run(self.root, much_later, {}, srcs=[fake_source("lib", error=SourceError("down"))])
        self.assertEqual(self.read("docs/data/events.json"), before)
        self.assertFalse(self.read("docs/data/status.json")["sources"]["lib"]["ok"])

    def test_weather_failure_keeps_the_previous_file(self):
        collect.run(self.root, NOW, {}, srcs=[])
        with mock.patch.object(weather, "fetch", mock.Mock(side_effect=net.FetchError("open-meteo", "HTTP 500", 500))):
            collect.run(self.root, NOW + timedelta(hours=3), {}, srcs=[])
        self.assertEqual(self.read("docs/data/weather.json"), WX)
        w = self.read("docs/data/status.json")["sources"]["weather"]
        self.assertEqual((w["ok"], w["lastSuccess"]), (False, "2026-10-10T14:31:00Z"))

    def test_window_filter_and_dedupe_and_overrides(self):
        with open(os.path.join(self.root, "overrides.json"), "w") as f:
            json.dump([{"match": "concert", "hide": True}], f)
        old = model.make_event("x", "old", "Last Week", la(2026, 10, 3, 10), city="Reno")
        dup = model.make_event("tm", "st", "Baby Storytime!", la(2026, 10, 10, 10, 30), city="Reno",
                               venue=model.venue("Sparks Library", "x"), kind="ticketing",
                               url="https://tm.example/st")
        collect.run(self.root, NOW, {}, srcs=[fake_source("lib", [storytime(), old]), fake_source("tm", [dup, concert()])])
        [e] = self.read("docs/data/events.json")["events"]
        self.assertEqual(e["id"], "lib:st10")
        self.assertEqual(len(e["links"]), 2)

    def test_every_reuses_a_fresh_result_without_fetching(self):
        src = fake_source("library", [storytime()], every=timedelta(hours=12))
        collect.run(self.root, NOW, {}, srcs=[src])
        collect.run(self.root, NOW + timedelta(hours=3), {}, srcs=[src])
        self.assertEqual(src.fetch.call_count, 1)
        self.assertTrue(self.read("docs/data/status.json")["sources"]["library"]["ok"])
        collect.run(self.root, NOW + timedelta(hours=13), {}, srcs=[src])
        self.assertEqual(src.fetch.call_count, 2)

    def test_last_good_keeps_keyword_cues_not_descriptions(self):
        sing = model.make_event("lib", "sing1", "Sing-Along", la(2026, 10, 10, 10, 30), city="Reno",
                                url="https://example.org/sing", text="Songs for toddlers and their grown-ups")
        collect.run(self.root, NOW, {}, srcs=[fake_source("lib", [sing])])
        with open(os.path.join(self.root, "state/sources/lib.json"), encoding="utf-8") as f:
            saved = f.read()
        self.assertNotIn("grown-ups", saved)
        self.assertIn("toddlers", saved)
        later = NOW + timedelta(hours=3)
        collect.run(self.root, later, {}, srcs=[fake_source("lib", error=net.FetchError("lib", "HTTP 503", 503))])
        self.assertEqual(self.read("docs/data/events.json")["events"][0]["tier"], "little")

    def test_force_digest(self):
        env = {"DISCORD_WEBHOOK_URL": "https://discord.example/hook", "FORCE_DIGEST": "true"}
        afternoon = la(2026, 10, 10, 15, 0)
        d = collect.run(self.root, afternoon, env, srcs=[fake_source("lib", [storytime()])], post=self.post_ok)
        self.assertTrue(d.digest)
        self.assertEqual(len(self.sent), 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run them to make sure they fail**

Run: `python3 -m unittest discover -s tests -v`
Expected: `ModuleNotFoundError: No module named 'collect'`

- [ ] **Step 3: Implement** `collector/collect.py`

```python
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
```

- [ ] **Step 4: Run the tests to make sure they pass**

Run: `python3 -m unittest discover -s tests -v`
Expected: all OK

- [ ] **Step 5: Run it for real once, locally**

```bash
python3 collector/collect.py
python3 -c "import json; d=json.load(open('docs/data/events.json')); print(len(d['events']), 'events'); print(json.load(open('docs/data/status.json'))['sources'])"
```
Expected:
- It prints a summary line.
- `docs/data/` and `state/` now exist.
- Ticketmaster shows `ok: false` with "not set up yet (TICKETMASTER_KEY missing)", and the other sources are ok.

Then **remove** the generated files, so the first committed data comes from GitHub Actions (`rm -rf docs/data state`).

- [ ] **Step 6: Commit**

```bash
git add collector/collect.py tests/test_collect.py
git commit -m "Collector run: sources, merge, classify, write, digest"
```

---

### Task 16: GitHub repo, workflows and the first live run

**Files:**
- Create: `.github/workflows/collect.yml`, `.github/workflows/test.yml`
- Modify: `README.md` (how it runs)

**Interfaces:**
- Consumes: `collector/collect.py` (Task 15).
- Produces:
  - the public repo `natanforestree/reno-today`
  - the `collect.yml` workflow (`workflow_dispatch` with a `force_digest` boolean input; the Worker in Task 20 dispatches it by file name `collect.yml`)
  - Pages from `main` `/docs`
  - committed `docs/data/*` and `state/*`

- [ ] **Step 1: Write** `.github/workflows/collect.yml`

```yaml
name: collect

on:
  schedule:
    # The Cloudflare Worker in natanforestree/finals-radar (worker/) dispatches
    # this hourly at :30. GitHub's own schedule is unreliable, so it's a backup.
    - cron: "47 * * * *"
  workflow_dispatch:
    inputs:
      force_digest:
        description: "Send the Discord digest now (for testing)"
        type: boolean
        default: false

permissions:
  contents: write

concurrency:
  group: collect
  cancel-in-progress: false

jobs:
  collect:
    runs-on: ubuntu-latest
    timeout-minutes: 8
    steps:
      - uses: actions/checkout@v7
        with:
          ref: main   # a run queued behind another starts from the latest state, so the digest can't go twice

      - name: Collect
        env:
          TICKETMASTER_KEY: ${{ secrets.TICKETMASTER_KEY }}
          DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
          FORCE_DIGEST: ${{ inputs.force_digest }}
        run: python3 collector/collect.py

      - name: Commit data
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add docs/data state
          if git diff --cached --quiet; then echo "nothing new"; exit 0; fi
          git commit -q -m "data: $(date -u +%Y-%m-%dT%H:%MZ)"
          for i in 1 2 3; do
            git push && exit 0
            git pull --rebase -q
          done
          exit 1
```

- [ ] **Step 2: Write** `.github/workflows/test.yml`

```yaml
name: test

on:
  push:
    paths: ["collector/**", "tests/**", "docs/*.js", "package.json", ".github/workflows/test.yml"]
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v7
      - name: Collector tests
        run: python3 -m unittest discover -s tests -v
      - uses: actions/setup-node@v5
        if: hashFiles('tests/page/*.test.js') != ''
        with:
          node-version: 22
      - name: Page logic tests
        if: hashFiles('tests/page/*.test.js') != ''
        run: npm test
```

The page-logic step skips itself until `tests/page/` exists (Task 18). `actions/setup-node@v5` was the current major version when this plan was written. Check it with `gh api repos/actions/setup-node/releases/latest -q .tag_name` and use whatever major that shows.

- [ ] **Step 3: Extend the README** with a "How it runs" section

```markdown
## How it runs

- Every hour the Cloudflare Worker `ruby-radar` (repo `natanforestree/finals-radar`,
  `worker/`) asks GitHub to run `collect.yml` (at :30). GitHub's own schedule
  (:47) is a backup.
- Each run refreshes if the last refresh was 2 h 50 min ago or more; from 07:00
  Reno time it also sends the Discord digest once a day (retrying hourly until
  10:59 if Discord fails).
- Secrets (repo settings → Secrets → Actions): `TICKETMASTER_KEY`,
  `DISCORD_WEBHOOK_URL`. Both are optional: without them Ticketmaster shows as
  "not set up yet" and no digest is sent.
- To test the digest any time: Actions → collect → Run workflow → tick
  "Send the Discord digest now".
- `overrides.json` corrects events by id (`"id:tm:…"`) or title regex:
  `{"match": "trivia night", "addHint": "21+"}`, `{"match": "…", "tier": "little"}`,
  `{"match": "…", "hide": true}`.
```

- [ ] **Step 4: Commit, create the public repo, push**

Run `gh auth status` first to confirm the active account is `natanforestree`. Creating the public repo is part of the approved design ("New public repo `natanforestree/reno-today`").

```bash
git add .github README.md
git commit -m "Workflows: hourly collect and tests"
gh repo create natanforestree/reno-today --public --source . --remote origin --push \
  --description "Everything happening in Reno today, little-ones picks first"
```
Expected: the repo is created and `main` is pushed.

- [ ] **Step 5: Turn on Pages from `main` `/docs` and run the collector once**

```bash
gh api repos/natanforestree/reno-today/pages -X POST -f build_type=legacy \
  -f 'source[branch]=main' -f 'source[path]=/docs'
gh workflow run collect.yml --repo natanforestree/reno-today
sleep 5; gh run watch --repo natanforestree/reno-today "$(gh run list --repo natanforestree/reno-today --workflow collect.yml --limit 1 --json databaseId -q '.[0].databaseId')"
git pull -q
python3 -c "import json; s=json.load(open('docs/data/status.json'))['sources']; print({k:(v['ok'], v['count'], v['error']) for k,v in s.items()})"
```
Expected:
- The run succeeds and a `data: …` commit appears.
- Status shows `ticketmaster` as `(False, 0, 'not set up yet …')` and the others as ok.
- `docs/` has no page yet. The `https://natanforestree.github.io/reno-today/data/events.json` URL starts working within a few minutes.

If the Pages API call says Pages already exists, skip it. If GitHub runners are having an outage ("job was not acquired by Runner"), wait and re-run. It isn't a code problem.

---
### Task 17: Pixel art (the Reno Arch header and the favicon)

**Files:**
- Create: `art/lib.lua` (copied from Ruby Radar and adapted), `art/arch.lua`, `art/favicon.lua`
- Outputs (commit these too): `art/arch.aseprite`, `art/favicon.aseprite`, `docs/art/arch.png`, `docs/art/favicon.png`

**Interfaces:**
- Consumes: Ruby Radar's helper library at `~/Documents/code/finals-radar/art/lib.lua`. Its functions:
  - `L.buffer`, `L.copy`
  - `L.set` / `L.get` (they floor coordinates)
  - `L.fillRect(b, x0, y0, x1, y1, c)` (inclusive)
  - `L.disc`
  - `L.outline(b, c, eight, skip)` (only around fully opaque pixels)
  - `L.blit(dst, src, ox, oy)` (alpha-blends)
  - `L.mix`
  - `L.saveStill(b, name)`, `L.saveStrip(frames, name, ms)` (they write `art/<name>.aseprite` and `docs/art/<name>.png`)
- Produces:
  - `docs/art/arch.png`: a **1408×96 strip of 8 frames, 176×96 each, 120 ms**. The page animates it with `steps(8)`.
  - `docs/art/favicon.png`: 32×32.

Aseprite is at `/Applications/Aseprite.app/Contents/MacOS/aseprite`; it isn't on `PATH`.

**The arch** (from Nathan's photo):
- neon **RENO** in pink and red, with a gentle flicker
- the red banner "THE BIGGEST LITTLE CITY IN THE WORLD"
- chasing bulbs
- a starburst on top
- steel pillars

This task gives you a working first version. **Look at the result and refine it**; Nathan gave creative freedom ("i like style"). Keep the frame size, frame count and timing fixed, because the page depends on them.

- [ ] **Step 1: Copy the helper library and give it the Reno palette**

```bash
mkdir -p art docs/art
cp ~/Documents/code/finals-radar/art/lib.lua art/lib.lua
```
Then edit `art/lib.lua`:
- Change the header comment's first line to "Shared helpers for Reno Today's sprite scripts".
- **Replace the whole `M.P = { … }` table** with:

```lua
-- The Reno Today palette (docs/style.css uses the same colours).
M.P = {
  outline = "#1b1420", night = "#1d1720", ink = "#f6ecd9", muted = "#bba99b",
  steelLight = "#d9dce6", steel = "#a3a9bb", steelDark = "#666c82", silver = "#c9ccd6",
  gold = "#ffd36b", goldLight = "#fff1c2", goldDark = "#c7902e",
  bulb = "#ffe08a", bulbOff = "#6e5634",
  neon = "#ff5fa2", neonCore = "#ffd6ea", neonDim = "#a8466f", neonDimCore = "#d77fa6",
  glow = "#ff3b5566",                       -- translucent neon halo
  red = "#d42a3a", redLight = "#ec5562", redDark = "#8f1b2b",
  sage = "#93b58c", sunset = "#ff9d57", sierra = "#6d9de0", pink = "#ff6fb5",
}
```
- **Delete the `M.gem` function** (from its comment block, "A side-on brilliant-cut gem", through its closing `end`). It uses Ruby Radar colours that no longer exist.

- [ ] **Step 2: Write** `art/arch.lua`

```lua
-- arch.png: the page header, the Reno Arch at dusk. 8 frames of 176x96, 120 ms each.
-- Bulbs chase along the pillars and over the arch (every fourth bulb is dark and the
-- dark ones step forward a bulb each frame), RENO glows in pink neon with a flicker on
-- frame 6, and the red banner reads THE BIGGEST LITTLE CITY IN THE WORLD in a 3x5 font.
-- Run from the repo root:
--   /Applications/Aseprite.app/Contents/MacOS/aseprite -b --script art/arch.lua
-- Writes art/arch.aseprite and docs/art/arch.png (a 1408x96 strip).
local L = dofile(debug.getinfo(1, "S").source:sub(2):match("^(.-)[^/]+$") .. "lib.lua")
local P = L.P
local W, H, FRAMES, MS = 176, 96, 8, 120

-- The arch band is the top half of the ring between two ellipses centred on (ACX, ACY).
local ACX, ACY = 87.5, 58
local OUT_RX, OUT_RY, IN_RX, IN_RY = 80, 40, 72, 32
local function inside(x, y, rx, ry)
  local dx, dy = (x + 0.5 - ACX) / rx, (y + 0.5 - ACY) / ry
  return dx * dx + dy * dy <= 1
end

-- 5x7 letters for RENO; a 3x5 font for the banner ("#" is lit).
local BIG = {
  R = { "####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#" },
  E = { "#####", "#....", "#....", "####.", "#....", "#....", "#####" },
  N = { "#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#" },
  O = { ".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###." },
}
local SMALL = {
  T = { "###", ".#.", ".#.", ".#.", ".#." }, H = { "#.#", "#.#", "###", "#.#", "#.#" },
  E = { "###", "#..", "##.", "#..", "###" }, B = { "##.", "#.#", "##.", "#.#", "##." },
  I = { "###", ".#.", ".#.", ".#.", "###" }, G = { ".##", "#..", "#.#", "#.#", ".##" },
  S = { ".##", "#..", ".#.", "..#", "##." }, L = { "#..", "#..", "#..", "#..", "###" },
  C = { ".##", "#..", "#..", "#..", ".##" }, Y = { "#.#", "#.#", ".#.", ".#.", ".#." },
  N = { "#.#", "###", "###", "#.#", "#.#" }, W = { "#.#", "#.#", "#.#", "###", "#.#" },
  O = { ".#.", "#.#", "#.#", "#.#", ".#." }, R = { "##.", "#.#", "##.", "#.#", "#.#" },
  D = { "##.", "#.#", "#.#", "#.#", "##." },
}
local BANNER = "THE BIGGEST LITTLE CITY IN THE WORLD"   -- 129 px wide in this font

-- Everything that stays the same between frames. The left half is drawn and then
-- mirrored, so the arch is exactly symmetric.
local function structure()
  local b = L.buffer(W, H)
  -- starburst crown: 16 rays round a gold hub (the band covers the lower rays)
  for k = 0, 15 do
    local a = math.rad(k * 22.5)
    local len = (k % 2 == 0) and 11 or 6
    for s = 0, len * 2 do
      local r = s / 2
      L.set(b, ACX + r * math.cos(a), 12 - r * math.sin(a),
        (k % 2 == 0 and r > len - 2) and P.gold or P.silver)
    end
  end
  L.disc(b, ACX, 12, 4, P.gold)
  L.set(b, 85, 10, P.goldLight); L.set(b, 86, 10, P.goldLight); L.set(b, 85, 11, P.goldLight)
  -- the band: lit along the outer edge, shaded along the inner edge
  for y = 0, ACY do
    for x = 0, W - 1 do
      if inside(x, y, OUT_RX, OUT_RY) and not inside(x, y, IN_RX, IN_RY) then
        local c = P.steel
        if not (inside(x, y - 1, OUT_RX, OUT_RY) and inside(x - 1, y, OUT_RX, OUT_RY)
            and inside(x + 1, y, OUT_RX, OUT_RY)) then
          c = P.steelLight
        elseif inside(x, y + 1, IN_RX, IN_RY) or inside(x - 1, y, IN_RX, IN_RY)
            or inside(x + 1, y, IN_RX, IN_RY) then
          c = P.steelDark
        end
        L.set(b, x, y, c)
      end
    end
  end
  -- pillars, with a wider capital and base
  for y = 50, H - 1 do
    local wide = y <= 52 or y >= H - 4
    for x = wide and 6 or 8, wide and 17 or 15 do
      L.set(b, x, y, (x <= 8) and P.steelLight or (x >= 15) and P.steelDark or P.steel)
    end
  end
  for y = 0, H - 1 do
    for x = 0, W / 2 - 1 do b[y][W - 1 - x] = b[y][x] end
  end
  -- the banner across the opening, with its lettering
  L.fillRect(b, 18, 53, 157, 61, P.red)
  L.fillRect(b, 18, 54, 157, 54, P.redLight)
  L.fillRect(b, 18, 53, 157, 53, P.redDark)
  L.fillRect(b, 18, 61, 157, 61, P.redDark)
  local x = 23
  for i = 1, #BANNER do
    local ch = BANNER:sub(i, i)
    if ch == " " then
      x = x + 2
    else
      local g = SMALL[ch]
      for gy = 1, 5 do
        for gx = 1, 3 do
          if g[gy]:sub(gx, gx) == "#" then L.set(b, x + gx - 1, 54 + gy, P.ink) end
        end
      end
      x = x + 4
    end
  end
  return b
end

-- The chase path: up the left pillar, over the arch, down the right pillar.
local PATH, half = {}, {}
for i = 0, 21 do
  local t = math.rad(170 - i * (78 / 21))           -- 170 degrees to 92
  half[#half + 1] = { math.floor(ACX + 76 * math.cos(t)), math.floor(ACY - 36 * math.sin(t)) }
end
for y = 92, 56, -6 do PATH[#PATH + 1] = { 11, y } end
for _, p in ipairs(half) do PATH[#PATH + 1] = p end
for i = #half, 1, -1 do PATH[#PATH + 1] = { W - 1 - half[i][1], half[i][2] } end
for y = 56, 92, 6 do PATH[#PATH + 1] = { W - 1 - 11, y } end

local function bulb(b, x, y, lit)
  if not lit then L.set(b, x, y, P.bulbOff); return end
  for _, d in ipairs({ { 1, 0 }, { -1, 0 }, { 0, 1 }, { 0, -1 } }) do
    local under = L.get(b, x + d[1], y + d[2])
    if under then L.set(b, x + d[1], y + d[2], L.mix(under, P.bulb, 0.45)) end
  end
  L.set(b, x, y, P.bulb)
end

-- RENO in neon tubes: 3x3 blocks per font pixel, with a pale core line along each stroke.
local function neon(f)
  local b = L.buffer(W, H)
  local x0, y0 = 52, 31                              -- 4 letters x 15 px + 3 gaps x 4 px = 72 px
  for li, ch in ipairs({ "R", "E", "N", "O" }) do
    local g = BIG[ch]
    local dim = (f == 6 and ch == "N")
    local tube, core = dim and P.neonDim or P.neon, dim and P.neonDimCore or P.neonCore
    local lx = x0 + (li - 1) * 19
    local function lit(gx, gy)
      return gy >= 0 and gy < 7 and gx >= 0 and gx < 5 and g[gy + 1]:sub(gx + 1, gx + 1) == "#"
    end
    for gy = 0, 6 do
      for gx = 0, 4 do
        if lit(gx, gy) then L.fillRect(b, lx + gx * 3, y0 + gy * 3, lx + gx * 3 + 2, y0 + gy * 3 + 2, tube) end
      end
    end
    for gy = 0, 6 do
      for gx = 0, 4 do
        if lit(gx, gy) then
          local cx, cy = lx + gx * 3 + 1, y0 + gy * 3 + 1
          L.set(b, cx, cy, core)
          if lit(gx + 1, gy) then L.set(b, cx + 1, cy, core); L.set(b, cx + 2, cy, core) end
          if lit(gx, gy + 1) then L.set(b, cx, cy + 1, core); L.set(b, cx, cy + 2, core) end
        end
      end
    end
  end
  L.outline(b, P.glow, true, { [P.neonDim] = true, [P.neonDimCore] = true })
  return b
end

local base = structure()
local frames = {}
for f = 1, FRAMES do
  local b = L.copy(base)
  for i, p in ipairs(PATH) do bulb(b, p[1], p[2], (i - f) % 4 ~= 0) end
  L.outline(b, P.outline)
  L.blit(b, neon(f), 0, 0)
  frames[f] = b
end
L.saveStrip(frames, "arch", MS)
```

- [ ] **Step 3: Write** `art/favicon.lua`

```lua
-- favicon.png: a neon pink R on a dark tile, 32x32.
-- Run: /Applications/Aseprite.app/Contents/MacOS/aseprite -b --script art/favicon.lua
local L = dofile(debug.getinfo(1, "S").source:sub(2):match("^(.-)[^/]+$") .. "lib.lua")
local P = L.P
local N, S, X0, Y0 = 32, 4, 6, 2
local R = { "####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#" }
local function lit(gx, gy)
  return gy >= 0 and gy < 7 and gx >= 0 and gx < 5 and R[gy + 1]:sub(gx + 1, gx + 1) == "#"
end

local b = L.buffer(N, N)
L.fillRect(b, 1, 0, N - 2, N - 1, P.night)           -- a tile with clipped corners
L.fillRect(b, 0, 1, N - 1, N - 2, P.night)
for gy = 0, 6 do
  for gx = 0, 4 do
    if lit(gx, gy) then L.fillRect(b, X0 + gx * S, Y0 + gy * S, X0 + gx * S + S - 1, Y0 + gy * S + S - 1, P.neon) end
  end
end
for gy = 0, 6 do
  for gx = 0, 4 do
    if lit(gx, gy) then
      local cx, cy = X0 + gx * S + 1, Y0 + gy * S + 1
      L.fillRect(b, cx, cy, cx + 1, cy + 1, P.neonCore)
      if lit(gx + 1, gy) then L.fillRect(b, cx + 2, cy, cx + S + 1, cy + 1, P.neonCore) end
      if lit(gx, gy + 1) then L.fillRect(b, cx, cy + 2, cx + 1, cy + S + 1, P.neonCore) end
    end
  end
end
L.saveStill(b, "favicon")
```

- [ ] **Step 4: Render both and check the sizes**

```bash
A=/Applications/Aseprite.app/Contents/MacOS/aseprite
$A -b --script art/arch.lua && $A -b --script art/favicon.lua
python3 -c "
import struct
for f in ('docs/art/arch.png', 'docs/art/favicon.png'):
    print(f, struct.unpack('>II', open(f, 'rb').read(24)[16:24]))"
```
Expected: `docs/art/arch.png (1408, 96)` and `docs/art/favicon.png (32, 32)`.

- [ ] **Step 5: Look at it and refine**

Make a 4× preview of frame 1 and frame 6, and view them with the Read tool:
```bash
python3 - <<'EOF'
import subprocess
subprocess.run(["sips", "-c", "96", "176", "--cropOffset", "0", "0", "docs/art/arch.png", "--out", "/tmp/arch-f1.png"], check=True)
subprocess.run(["sips", "-z", "384", "704", "/tmp/arch-f1.png", "--out", "/tmp/arch-f1-4x.png"], check=True)
EOF
```
(If `sips` cropping is awkward, write the preview with a small Aseprite Lua snippet, or just view `docs/art/arch.png` directly.)

Checklist:
- RENO is legible and centred under the crown.
- The banner text reads cleanly and stays inside the red.
- The bulbs are visible on the band.
- No stray pixels from the mirroring.

Fix anything ugly by editing the script and re-running. Keep 176×96, 8 frames and 120 ms.

- [ ] **Step 6: Commit**

```bash
git add art docs/art
git commit -m "Pixel art: animated Reno Arch header and favicon"
```

---

### Task 18: Page logic (`docs/lib.js`) with tests

**Files:**
- Create: `docs/lib.js`, `tests/page/lib.test.js`

**Interfaces:**
- Consumes: the JSON shapes from Tasks 2, 11, 12, 15 and 22 (events, weather days, guide, status, places).
- Produces (ES module exports, used by `docs/app.js` in Task 19):
  - Constants: `TZ`, `LOCAL_AREAS`, `AREA_LABEL`, `SOURCE_LABEL`, `PARTS`, `STALE_HOURS`
  - Dates: `renoDate(ms) -> 'YYYY-MM-DD'`, `addDays(day, n)`, `weekday(day) -> 'mon'…'sun'`, `dayTabs(today, n=8) -> [{date, label}]`
  - Grouping: `isLocal(e)`, `lastDay(e)`, `eventsOn(events, day)`, `partOfDay(e)`, `onNow(e, nowMs)`, `passes(e, filters)`, `dayView(events, day, filters) -> {little, parts, ongoing, drive, total, littleCount}`
  - Formatting: `fmtTime(e)`, `fmtClock('HH:MM')`, `fmtPrice(price)`
  - Places and weather: `hoursOn(place, day)`, `shortHours(h)`, `placesOpen(places, day) -> [[place, hours]]`, `niceNote(wxDay)`
  - Safety: `esc(s)`, `safeUrl(u) -> string|null`, `mapsUrl(venue) -> string|null`
  - Freshness: `ago(iso, nowMs)`, `isStale(iso, nowMs)`

- [ ] **Step 1: Write the failing tests** `tests/page/lib.test.js`

```js
// Runs in a far-away time zone on purpose: everything must follow Reno's clock.
process.env.TZ = 'Asia/Tokyo';

import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as L from '../../docs/lib.js';

const ev = (o = {}) => ({
  id: 'x:1', title: 'T', start: '2026-10-10T10:00:00-07:00', end: null, allDay: false, ongoing: false,
  venue: null, area: 'reno', drive: null, price: null, tier: 'general', hints: [], links: [], lovingReno: null, ...o,
});

test('renoDate follows Reno, not the device', () => {
  assert.equal(L.renoDate(Date.UTC(2026, 9, 11, 6, 30)), '2026-10-10');   // 23:30 PDT
  assert.equal(L.renoDate(Date.UTC(2026, 9, 11, 7, 30)), '2026-10-11');   // 00:30 PDT
  assert.equal(L.renoDate(Date.UTC(2026, 10, 1, 8, 30)), '2026-11-01');   // 01:30 PDT on the fall-back day
  assert.equal(L.renoDate(Date.UTC(2026, 10, 2, 7, 30)), '2026-11-01');   // 23:30 PST that evening
});

test('day tabs', () => {
  const tabs = L.dayTabs('2026-10-10');
  assert.equal(tabs.length, 8);
  assert.deepEqual(tabs.slice(0, 3).map((t) => t.label), ['Today', 'Tomorrow', 'Mon 12']);
  assert.equal(tabs[7].date, '2026-10-17');
  assert.equal(L.addDays('2026-10-30', 3), '2026-11-02');
  assert.equal(L.weekday('2026-10-10'), 'sat');
});

test('eventsOn: one-off events on their day; ongoing, all-day and long ones across their run', () => {
  const once = ev({ id: 'a' });
  const exhibit = ev({ id: 'b', ongoing: true, start: '2026-10-01T10:00:00-07:00', end: '2026-10-20T17:00:00-07:00' });
  assert.deepEqual(L.eventsOn([once, exhibit], '2026-10-10').map((e) => e.id), ['a', 'b']);
  assert.deepEqual(L.eventsOn([once, exhibit], '2026-10-11').map((e) => e.id), ['b']);
  assert.deepEqual(L.eventsOn([once, exhibit], '2026-10-21').map((e) => e.id), []);
  const fest = ev({ id: 'c', allDay: true, start: '2026-10-09T00:00:00-07:00', end: '2026-10-11T00:00:00-07:00' });
  const late = ev({ id: 'd', start: '2026-10-10T21:00:00-07:00', end: '2026-10-11T01:00:00-07:00' });
  assert.deepEqual(L.eventsOn([fest, late], '2026-10-10').map((e) => e.id), ['c', 'd']);
  assert.deepEqual(L.eventsOn([fest, late], '2026-10-11').map((e) => e.id), ['c']);
});

test('part of day', () => {
  const at = (h) => ev({ start: `2026-10-10T${String(h).padStart(2, '0')}:00:00-07:00` });
  assert.deepEqual([9, 12, 16, 17, 20, 21, 23].map((h) => L.partOfDay(at(h))),
    ['morning', 'afternoon', 'afternoon', 'evening', 'evening', 'late', 'late']);
  assert.equal(L.partOfDay(ev({ allDay: true })), 'allday');
});

test('on now uses the end, or two hours when there is none', () => {
  const t = (iso) => Date.parse(iso);
  const e = ev({ start: '2026-10-10T10:00:00-07:00', end: '2026-10-10T10:45:00-07:00' });
  assert.equal(L.onNow(e, t('2026-10-10T10:30:00-07:00')), true);
  assert.equal(L.onNow(e, t('2026-10-10T10:46:00-07:00')), false);
  assert.equal(L.onNow(ev(), t('2026-10-10T11:59:00-07:00')), true);
  assert.equal(L.onNow(ev({ allDay: true }), t('2026-10-10T11:00:00-07:00')), false);
});

test('filters', () => {
  const free = ev({ price: { free: true }, hints: ['outdoors', 'daytime'] });
  const adult = ev({ hints: ['21+'] });
  const little = ev({ tier: 'little' });
  assert.equal(L.passes(free, { free: true, outdoors: true }), true);
  assert.equal(L.passes(adult, { free: true }), false);
  assert.equal(L.passes(adult, { hide21: true }), false);
  assert.equal(L.passes(little, { little: true }), true);
  assert.equal(L.passes(free, { little: true }), false);
});

test('dayView groups the day', () => {
  const events = [
    ev({ id: 'story', tier: 'little', start: '2026-10-10T10:30:00-07:00' }),
    ev({ id: 'show', start: '2026-10-10T19:30:00-07:00' }),
    ev({ id: 'fest', allDay: true, start: '2026-10-10T00:00:00-07:00' }),
    ev({ id: 'club', start: '2026-10-10T22:00:00-07:00', hints: ['21+'] }),
    ev({ id: 'tahoe', area: 'tahoe', tier: 'little', start: '2026-10-10T11:00:00-07:00' }),
    ev({ id: 'exhibit', ongoing: true, start: '2026-10-01T10:00:00-07:00', end: '2026-10-30T17:00:00-07:00' }),
    ev({ id: 'tomorrow', start: '2026-10-11T09:00:00-07:00' }),
  ];
  const v = L.dayView(events, '2026-10-10', {});
  assert.deepEqual(v.little.map((e) => e.id), ['story']);
  assert.deepEqual(v.parts.allday.map((e) => e.id), ['fest']);
  assert.deepEqual(v.parts.evening.map((e) => e.id), ['show']);
  assert.deepEqual(v.parts.late.map((e) => e.id), ['club']);
  assert.deepEqual(v.drive.map((e) => e.id), ['tahoe']);
  assert.deepEqual(v.ongoing.map((e) => e.id), ['exhibit']);
  assert.equal(v.littleCount, 1);
  assert.equal(v.total, 6);
  const filtered = L.dayView(events, '2026-10-10', { hide21: true, little: true });
  assert.equal(filtered.parts.late.length, 0);
  assert.equal(filtered.littleCount, 1, 'counted before filters');
});

test('times and prices', () => {
  const at = (hm) => ev({ start: `2026-10-10T${hm}:00-07:00` });
  assert.deepEqual(['10:30', '13:05', '19:00', '12:00', '00:15'].map((hm) => L.fmtTime(at(hm))),
    ['10:30am', '1:05pm', '7pm', '12pm', '12:15am']);
  assert.equal(L.fmtTime(ev({ allDay: true })), 'All day');
  assert.equal(L.fmtClock('17:00'), '5pm');
  assert.equal(L.fmtClock('09:30'), '9:30am');
  assert.equal(L.fmtPrice({ free: true }), 'Free');
  assert.equal(L.fmtPrice({ min: 25, max: 25 }), '$25');
  assert.equal(L.fmtPrice({ min: 25, max: 60.5 }), '$25–60.50');
  assert.equal(L.fmtPrice(null), '');
});

test('places and weather notes', () => {
  const discovery = { hours: { mon: null, sat: '10:00-17:00' } };
  const splash = { months: [6, 7, 8], hours: { sat: '11:00-19:00' } };
  assert.equal(L.hoursOn(discovery, '2026-10-10'), '10:00-17:00');
  assert.equal(L.hoursOn(discovery, '2026-10-12'), null);
  assert.equal(L.hoursOn(splash, '2026-10-10'), null);
  assert.equal(L.shortHours('09:30-16:00'), '9:30–4');
  assert.equal(L.shortHours('dawn-dusk'), 'dawn–dusk');
  assert.deepEqual(L.placesOpen([discovery, splash], '2026-10-10').map(([, h]) => h), ['10:00-17:00']);
  assert.equal(L.niceNote({ nice: [{ from: '10:00', to: '17:00' }] }), 'Nice outside 10am–5pm');
  assert.equal(L.niceNote({ nice: [] }), '');
  assert.equal(L.niceNote(null), '');
});

test('escaping and links', () => {
  assert.equal(L.esc('<img src=x onerror="alert(1)">&\''), '&lt;img src=x onerror=&quot;alert(1)&quot;&gt;&amp;&#39;');
  assert.equal(L.esc(null), '');
  assert.equal(L.safeUrl('javascript:alert(1)'), null);
  assert.equal(L.safeUrl('data:text/html,hi'), null);
  assert.equal(L.safeUrl('//evil.example'), null);
  assert.equal(L.safeUrl('not a url'), null);
  assert.equal(L.safeUrl('https://a.example/b?c=1'), 'https://a.example/b?c=1');
  assert.equal(L.mapsUrl({ name: 'The Discovery', address: '490 S Center St' }),
    'https://www.google.com/maps/search/?api=1&query=The%20Discovery%2C%20490%20S%20Center%20St');
  assert.equal(L.mapsUrl(null), null);
});

test('freshness', () => {
  const now = Date.parse('2026-10-10T15:00:00Z');
  assert.equal(L.ago('2026-10-10T14:30:00Z', now), '30 min ago');
  assert.equal(L.ago('2026-10-10T12:00:00Z', now), '3 hours ago');
  assert.equal(L.isStale('2026-10-10T12:00:00Z', now), false);
  assert.equal(L.isStale('2026-10-10T08:00:00Z', now), true);
  assert.equal(L.isStale(null, now), true);
});
```

- [ ] **Step 2: Run them to make sure they fail**

Run: `npm test`
Expected: failure, with "Cannot find module …/docs/lib.js"

- [ ] **Step 3: Implement** `docs/lib.js`

```js
// Pure helpers for the Reno Today page: Reno's dates, grouping, filters, formatting
// and escaping. No DOM here, so `npm test` covers it (tests/page/lib.test.js).

export const TZ = 'America/Los_Angeles';
export const LOCAL_AREAS = ['reno', 'sparks'];
export const AREA_LABEL = {
  reno: 'Reno', sparks: 'Sparks', tahoe: 'Lake Tahoe', carson: 'Carson City',
  'virginia-city': 'Virginia City', other: 'Nearby',
};
export const SOURCE_LABEL = {
  tm: 'Ticketmaster', unr: 'UNR', wolfpack: 'Wolf Pack', aces: 'Aces', library: 'Library',
  discovery: 'The Discovery', reno: 'City of Reno', sparks: 'City of Sparks', wcparks: 'Washoe Parks',
  carson: 'Visit Carson City', southtahoe: 'Visit Lake Tahoe', vcity: 'Virginia City', standing: 'Info',
};
export const PARTS = [
  ['allday', 'All day'], ['morning', 'Morning'], ['afternoon', 'Afternoon'], ['evening', 'Evening'], ['late', 'Late'],
];
export const STALE_HOURS = 6;
const WEEKDAYS = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'];
const noon = (day) => new Date(`${day}T12:00:00Z`);
const two = (n) => String(n).padStart(2, '0');

export function renoDate(ms) {
  const p = Object.fromEntries(new Intl.DateTimeFormat('en-US', {
    timeZone: TZ, year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(new Date(ms)).map((x) => [x.type, x.value]));
  return `${p.year}-${p.month}-${p.day}`;
}

export function addDays(day, n) {
  const d = noon(day);
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}

export const weekday = (day) => WEEKDAYS[noon(day).getUTCDay()];

export function dayTabs(today, n = 8) {
  return Array.from({ length: n }, (_, i) => {
    const date = addDays(today, i);
    const short = noon(date).toLocaleDateString('en-US', { weekday: 'short', timeZone: 'UTC' });
    return { date, label: i === 0 ? 'Today' : i === 1 ? 'Tomorrow' : `${short} ${Number(date.slice(8))}` };
  });
}

export const isLocal = (e) => LOCAL_AREAS.includes(e.area);

const MULTI_DAY_MS = 20 * 3600e3;

/** The last date an event shows on: all-day, ongoing and 20 h+ events cover their whole run. */
export function lastDay(e) {
  if (e.end && (e.allDay || e.ongoing || Date.parse(e.end) - Date.parse(e.start) >= MULTI_DAY_MS)) {
    return e.end.slice(0, 10);
  }
  return e.start.slice(0, 10);
}

export function eventsOn(events, day) {
  return events.filter((e) => e.start.slice(0, 10) <= day && day <= lastDay(e));
}

export function partOfDay(e) {
  if (e.allDay) return 'allday';
  const h = Number(e.start.slice(11, 13));
  return h < 12 ? 'morning' : h < 17 ? 'afternoon' : h < 21 ? 'evening' : 'late';
}

export function onNow(e, nowMs) {
  if (e.allDay || e.ongoing) return false;
  const start = Date.parse(e.start);
  const end = e.end ? Date.parse(e.end) : start + 2 * 3600e3;
  return start <= nowMs && nowMs < end;
}

export function passes(e, f) {
  return (!f.free || Boolean(e.price?.free))
    && (!f.outdoors || e.hints.includes('outdoors'))
    && (!f.little || e.tier === 'little')
    && (!f.hide21 || !e.hints.includes('21+'));
}

const byStart = (a, b) => a.start.localeCompare(b.start) || a.title.localeCompare(b.title);

/** Everything one day shows, filtered and sorted. littleCount ignores the filters. */
export function dayView(events, day, filters) {
  const all = eventsOn(events, day).sort(byStart);
  const parts = Object.fromEntries(PARTS.map(([key]) => [key, []]));
  const view = {
    little: [], parts, ongoing: [], drive: [], total: 0,
    littleCount: all.filter((e) => isLocal(e) && !e.ongoing && e.tier === 'little').length,
  };
  for (const e of all.filter((x) => passes(x, filters))) {
    view.total += 1;
    if (!isLocal(e)) view.drive.push(e);
    else if (e.ongoing) view.ongoing.push(e);
    else if (e.tier === 'little') view.little.push(e);
    else parts[partOfDay(e)].push(e);
  }
  return view;
}

function clock(h, m) {
  return `${h % 12 || 12}${m ? `:${two(m)}` : ''}${h < 12 ? 'am' : 'pm'}`;
}

export function fmtTime(e) {
  if (e.allDay) return 'All day';
  return clock(Number(e.start.slice(11, 13)), Number(e.start.slice(14, 16)));
}

export function fmtClock(hhmm) {
  const [h, m] = hhmm.split(':').map(Number);
  return clock(h, m);
}

export function fmtPrice(p) {
  if (!p) return '';
  if (p.free) return 'Free';
  const money = (n) => (Number.isInteger(n) ? `${n}` : n.toFixed(2));
  return p.min === p.max ? `$${money(p.min)}` : `$${money(p.min)}–${money(p.max)}`;
}

export function hoursOn(place, day) {
  if (place.months && !place.months.includes(Number(day.slice(5, 7)))) return null;
  return place.hours?.[weekday(day)] ?? null;
}

export function shortHours(h) {
  const [a, b] = String(h).split('-');
  if (!a?.includes(':') || !b?.includes(':')) return String(h).replace('-', '–');
  const c = (s) => { const [hh, mm] = s.split(':').map(Number); return `${hh % 12 || 12}${mm ? `:${two(mm)}` : ''}`; };
  return `${c(a)}–${c(b)}`;
}

export const placesOpen = (places, day) =>
  places.map((p) => [p, hoursOn(p, day)]).filter(([, h]) => h);

export function niceNote(wxDay) {
  if (!wxDay?.nice?.length) return '';
  return `Nice outside ${wxDay.nice.map((w) => `${fmtClock(w.from)}–${fmtClock(w.to)}`).join(', ')}`;
}

const ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
export const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ESC[c]);

export function safeUrl(u) {
  try {
    const url = new URL(u);
    return url.protocol === 'https:' || url.protocol === 'http:' ? url.href : null;
  } catch {
    return null;
  }
}

export function mapsUrl(venue) {
  const q = [venue?.name, venue?.address].filter(Boolean).join(', ');
  return q ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(q)}` : null;
}

export function ago(iso, nowMs) {
  const min = Math.round((nowMs - Date.parse(iso)) / 60000);
  if (!Number.isFinite(min)) return '';
  if (min < 2) return 'just now';
  if (min < 90) return `${min} min ago`;
  const h = Math.round(min / 60);
  return h < 36 ? `${h} hours ago` : `${Math.round(h / 24)} days ago`;
}

export const isStale = (iso, nowMs) => !iso || !(nowMs - Date.parse(iso) <= STALE_HOURS * 3600e3);
```

- [ ] **Step 4: Run them to make sure they pass**

Run: `npm test`
Expected: 11 tests pass. If `safeUrl('https://a.example/b?c=1')` comes back normalised differently, that's the URL standard's normal form; keep the assertion on `new URL(...).href`.

- [ ] **Step 5: Commit**

```bash
git add docs/lib.js tests/page/lib.test.js
git commit -m "Page logic: Reno dates, grouping, filters, formatting, escaping"
```

---

### Task 19: The page (`index.html`, `style.css`, `app.js`), fixtures and browser checks

**Files:**
- Create: `docs/index.html`, `docs/style.css`, `docs/app.js`, `dev/make_fixture.py`
- Modify: `README.md` (how to preview the page)

**Interfaces:**
- Consumes:
  - `docs/lib.js` (Task 18)
  - `docs/art/arch.png` and `favicon.png` (Task 17)
  - the data files (Task 15)
  - `collector/model.py` and `classify.py` (used by the fixture generator)
- Produces:
  - the live page at `https://natanforestree.github.io/reno-today/`
  - URL parameters for checks: `?data=<relative folder>/` (fixtures, same origin only) and `?now=<ISO>` (pretend time)

The spec's section order is: day switcher, weather, filter chips, little ones, everything else (Morning / Afternoon / Evening / Late), Ongoing (collapsed), Worth the drive, Always an option (open when fewer than 3 little-ones events), the Loving Reno card, then the footer.

- [ ] **Step 1: Write** `docs/index.html`

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Reno Today</title>
<meta name="description" content="Everything happening in Reno today, with things you can bring a toddler to first.">
<meta name="theme-color" content="#1d1720">
<link rel="icon" href="art/favicon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Pixelify+Sans:wght@400;600&family=VT323&display=swap">
<link rel="stylesheet" href="style.css">
<script type="module" src="app.js"></script>
</head>
<body>
<header class="sky">
  <div class="arch" role="img" aria-label="The Reno Arch: The Biggest Little City in the World"></div>
  <h1>Reno Today</h1>
  <p class="tagline" id="tagline">What's on in the Biggest Little City</p>
</header>
<main>
  <div id="notice" class="notice" aria-live="polite"></div>
  <nav class="days" id="days" aria-label="Pick a day"></nav>
  <section class="weather" id="weather" aria-label="Weather"></section>
  <div class="chips" id="chips" role="group" aria-label="Filters"></div>
  <section id="little" class="block"></section>
  <section id="rest" class="block"></section>
  <details id="ongoing" class="block" hidden></details>
  <section id="drive" class="block" hidden></section>
  <details id="always" class="block" hidden></details>
  <section id="guide" class="block" hidden></section>
</main>
<footer id="footer"></footer>
</body>
</html>
```

- [ ] **Step 2: Write** `docs/style.css`

```css
/* Reno Today: cozy pixel style. Reno at dusk: sage, sunset orange, Sierra blue and
   the Arch's neon on a warm dark background. art/lib.lua uses the same colours. */
:root {
  --bg: #1d1720; --panel: #2a2130; --panel-2: #33283a; --line: #4a3a4f; --shadow: #0f0b12;
  --ink: #f6ecd9; --muted: #bba99b; --sage: #93b58c; --sunset: #ff9d57;
  --sierra: #8db4ef; --neon: #ff3b55; --pink: #ff6fb5; --gold: #ffd36b;
  --pixel: 'Pixelify Sans', ui-sans-serif, system-ui, sans-serif;
  --body: 'VT323', ui-monospace, monospace;
  color-scheme: dark;
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body { margin: 0; background: var(--bg); color: var(--ink); font: 22px/1.25 var(--body); }
a { color: var(--sierra); }
a:focus-visible, button:focus-visible, summary:focus-visible { outline: 3px solid var(--gold); outline-offset: 2px; }
[hidden] { display: none !important; }

/* Header: the Arch against banded dusk */
.sky {
  padding: 18px 16px 14px; text-align: center; border-bottom: 4px solid var(--shadow);
  background: linear-gradient(#21183a 0 22%, #352049 22% 42%, #5a2a55 42% 60%,
                              #8c3b58 60% 74%, #c95a4e 74% 86%, #f0974f 86% 100%);
}
.arch {
  width: min(100%, 352px); aspect-ratio: 176 / 96; margin: 0 auto;
  background: url(art/arch.png) 0 0 / 800% 100% no-repeat;
  image-rendering: pixelated;
  animation: chase 960ms steps(8) infinite;
}
/* 8 frames: background-position 0% … 114.2857% (8/7) lands on frames 0–7 */
@keyframes chase { to { background-position: 114.2857% 0; } }
@media (min-width: 720px) { .arch { width: 528px; } }
@media (prefers-reduced-motion: reduce) { .arch { animation: none; } .now { animation: none; } }
h1 { font: 600 34px/1 var(--pixel); margin: 10px 0 2px; letter-spacing: 1px; text-shadow: 3px 3px 0 var(--shadow); }
.tagline { margin: 0; color: #ffe3c4; }

main { max-width: 760px; margin: 0 auto; padding: 0 16px 24px; }
.notice p { background: #4a2330; border: 2px solid var(--neon); padding: 8px 10px; margin: 12px 0 0; }

/* Day switcher and filter chips */
.days { display: flex; gap: 6px; overflow-x: auto; padding: 14px 2px 10px; scrollbar-width: none; }
.days::-webkit-scrollbar { display: none; }
.days button, .chip {
  font: 400 18px/1 var(--pixel); color: var(--ink); background: var(--panel); border: 2px solid var(--line);
  border-radius: 0; padding: 8px 10px; white-space: nowrap; cursor: pointer; box-shadow: 2px 2px 0 var(--shadow);
}
.days button[aria-pressed="true"] { background: var(--sunset); color: var(--bg); border-color: #ffd2a8; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; margin: 12px 0; }
.chip[aria-pressed="true"] { background: var(--sage); color: #14201a; border-color: #cfe5c9; }

/* Weather strip */
.weather {
  display: flex; flex-wrap: wrap; gap: 2px 12px; align-items: baseline; background: var(--panel);
  border: 2px solid var(--line); padding: 10px 12px; box-shadow: 3px 3px 0 var(--shadow);
}
.wx-emoji { font-size: 26px; }
.wx-temp { font: 600 22px var(--pixel); }
.wx-nice { color: var(--sage); }

/* Sections and cards */
.block { margin: 18px 0; }
h2 { font: 600 22px/1.2 var(--pixel); margin: 0 0 8px; color: var(--gold); }
.part { font: 400 16px var(--pixel); color: var(--muted); margin: 14px 0 6px; text-transform: uppercase; letter-spacing: 1px; }
.card {
  display: grid; grid-template-columns: 78px minmax(0, 1fr); gap: 10px; margin: 0 0 8px; padding: 10px;
  background: var(--panel); border: 2px solid var(--line); box-shadow: 3px 3px 0 var(--shadow);
}
.card.is-little { border-color: var(--sage); }
.card.is-now { border-color: var(--pink); }
.when { font: 600 17px/1.2 var(--pixel); color: var(--sunset); overflow-wrap: anywhere; }
.now { display: block; margin-top: 4px; color: var(--pink); font-size: 14px; animation: blink 1.2s steps(1) infinite; }
@keyframes blink { 50% { opacity: 0.35; } }
.what h3 { font: 400 25px/1.05 var(--body); margin: 0; overflow-wrap: anywhere; }
.where, .note { margin: 2px 0 0; color: var(--muted); overflow-wrap: anywhere; }
.badges { margin: 6px 0 0; display: flex; flex-wrap: wrap; gap: 4px; }
.b {
  font: 400 13px/1 var(--pixel); padding: 4px 6px; background: var(--panel-2);
  border: 1px solid var(--line); color: var(--ink); text-decoration: none;
}
.b-free { background: #2f4a33; border-color: var(--sage); }
.b-adult { background: #4a2330; border-color: var(--neon); }
.b-lr { background: #4a2240; border-color: var(--pink); color: #ffd6ea; }
.links { margin: 6px 0 0; font-size: 20px; }
.empty, .muted { color: var(--muted); }
.small { font-size: 18px; }

/* Collapsible sections */
details > summary { cursor: pointer; list-style: none; }
details > summary::-webkit-details-marker { display: none; }
details > summary h2 { display: inline; }
details > summary h2::before { content: '▸ '; }
details[open] > summary h2::before { content: '▾ '; }
details[open] > summary { margin-bottom: 8px; }

.guide-card {
  display: block; background: var(--panel); border: 2px solid var(--pink); padding: 12px;
  text-decoration: none; color: var(--ink); box-shadow: 3px 3px 0 var(--shadow);
}
.guide-title { display: block; font: 600 20px/1.2 var(--pixel); margin-bottom: 4px; }

footer { max-width: 760px; margin: 0 auto; padding: 8px 16px 32px; border-top: 2px dashed var(--line); color: var(--muted); }
footer p { margin: 6px 0; }
.warn { color: #ffd2a8; }
```

- [ ] **Step 3: Write** `docs/app.js`

```js
// Reno Today page: loads docs/data/*.json and renders the chosen day.
// Every piece of text from the data goes through L.esc, and every link through L.safeUrl.
import * as L from './lib.js';

const RAW = 'https://raw.githubusercontent.com/natanforestree/reno-today/main/docs/data/';
const FILTERS_KEY = 'reno-today:filters';
const FILTERS = [['free', 'Free'], ['outdoors', 'Outdoors'], ['little', 'Little ones only'], ['hide21', 'Hide 21+']];
const HINT_LABEL = { 'all-ages': 'all ages', outdoors: 'outdoors', '21+': '21+' };
const params = new URLSearchParams(location.search);
const fakeNow = Date.parse(params.get('now') ?? '');
const now = () => (Number.isFinite(fakeNow) ? fakeNow : Date.now());
const $ = (id) => document.getElementById(id);
const state = { data: null, day: null, filters: loadFilters() };

function loadFilters() {
  try {
    const saved = JSON.parse(localStorage.getItem(FILTERS_KEY) || '{}');
    return Object.fromEntries(FILTERS.map(([k]) => [k, saved[k] === true]));
  } catch {
    return {};
  }
}

function saveFilters() {
  try { localStorage.setItem(FILTERS_KEY, JSON.stringify(state.filters)); } catch { /* storage off */ }
}

// ?data=<relative folder>/ reads fixtures (same origin only). On the live site the
// repo's raw files come first: they update within minutes of each data commit, even
// when a GitHub Pages deploy is stuck. The copy Pages published is the fallback.
function dataBases() {
  const d = params.get('data');
  if (d && /^[\w./-]+\/$/.test(d) && !d.startsWith('//')) return [d];
  return location.hostname.endsWith('github.io') ? [RAW, 'data/'] : ['data/'];
}

async function loadJson(name, fallback) {
  for (const base of dataBases()) {
    try {
      const res = await fetch(base + name, { cache: 'no-cache' });
      if (res.ok) return await res.json();
    } catch { /* try the next place */ }
  }
  return fallback;
}

const link = (url, label) => `<a href="${L.esc(url)}" target="_blank" rel="noopener">${L.esc(label)}</a>`;

function card(e, nowMs) {
  const live = state.day === L.renoDate(nowMs) && L.onNow(e, nowMs);
  const where = [e.venue?.name, e.area !== 'reno' ? L.AREA_LABEL[e.area] : null].filter(Boolean).join(' · ');
  const badges = [];
  const price = L.fmtPrice(e.price);
  if (price) badges.push(`<span class="b${e.price?.free ? ' b-free' : ''}">${L.esc(price)}</span>`);
  for (const h of e.hints) {
    if (HINT_LABEL[h]) badges.push(`<span class="b${h === '21+' ? ' b-adult' : ''}">${HINT_LABEL[h]}</span>`);
  }
  if (e.drive) badges.push(`<span class="b">🚗 ${L.esc(e.drive)}</span>`);
  const lr = e.lovingReno && L.safeUrl(e.lovingReno.url);
  if (lr) badges.push(`<a class="b b-lr" href="${L.esc(lr)}" target="_blank" rel="noopener">Loving Reno pick</a>`);
  const links = (e.links || []).map((l) => [L.safeUrl(l.url), L.SOURCE_LABEL[l.source] || l.source]).filter(([u]) => u);
  const maps = L.mapsUrl(e.venue);
  if (maps) links.push([maps, 'Directions']);
  const time = e.ongoing && e.end && !e.allDay
    ? `${L.fmtTime(e)}–${L.fmtTime({ allDay: false, start: e.end })}` : L.fmtTime(e);
  return `<article class="card${e.tier === 'little' ? ' is-little' : ''}${live ? ' is-now' : ''}">
    <div class="when">${L.esc(time)}${live ? '<span class="now">on now</span>' : ''}</div>
    <div class="what">
      <h3>${L.esc(e.title)}</h3>
      ${where ? `<p class="where">${L.esc(where)}</p>` : ''}
      ${badges.length ? `<p class="badges">${badges.join('')}</p>` : ''}
      ${links.length ? `<p class="links">${links.map(([u, label]) => link(u, label)).join(' · ')}</p>` : ''}
    </div>
  </article>`;
}

function placeCard(p, hours) {
  const url = L.safeUrl(p.url);
  const maps = L.mapsUrl({ name: p.name, address: p.address });
  const sub = [p.goodFor, p.area !== 'reno' ? L.AREA_LABEL[p.area] : null, p.setting].filter(Boolean).join(' · ');
  const links = [url && link(url, 'Check hours'), maps && link(maps, 'Directions')].filter(Boolean);
  return `<article class="card place">
    <div class="when">${L.esc(L.shortHours(hours))}</div>
    <div class="what">
      <h3>${L.esc(p.name)}</h3>
      ${sub ? `<p class="where">${L.esc(sub)}</p>` : ''}
      ${p.notes ? `<p class="note small">${L.esc(p.notes)}</p>` : ''}
      ${links.length ? `<p class="links">${links.join(' · ')}</p>` : ''}
    </div>
  </article>`;
}

function renderNotice() {
  const gen = state.data.generatedAt;
  $('notice').innerHTML = L.isStale(gen, now())
    ? `<p>⚠️ ${gen ? `Last updated ${L.esc(L.ago(gen, now()))}` : 'No data yet'}, so this list may be out of date.</p>`
    : '';
}

function renderDays() {
  $('days').innerHTML = L.dayTabs(L.renoDate(now())).map((t) =>
    `<button type="button" data-day="${t.date}" aria-pressed="${t.date === state.day}">${L.esc(t.label)}</button>`).join('');
  $('tagline').textContent = new Date(`${state.day}T12:00:00Z`)
    .toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', timeZone: 'UTC' });
}

function renderWeather() {
  const day = state.data.weather?.days?.find((d) => d.date === state.day);
  if (!day) {
    $('weather').innerHTML = '<span class="muted">Weather unavailable for this day.</span>';
    return;
  }
  const nice = L.niceNote(day);
  $('weather').innerHTML = `<span class="wx-emoji" aria-hidden="true">${L.esc(day.emoji)}</span>
    <span class="wx-temp">${L.esc(day.low)}° → ${L.esc(day.high)}°</span>
    <span>${L.esc(day.summary)}${day.rain ? ` · ${L.esc(day.rain)}% rain` : ''}</span>
    ${nice ? `<span class="wx-nice">🌿 ${L.esc(nice)}</span>` : ''}`;
}

function renderChips() {
  $('chips').innerHTML = FILTERS.map(([key, label]) =>
    `<button type="button" class="chip" data-filter="${key}" aria-pressed="${Boolean(state.filters[key])}">${label}</button>`).join('');
}

function renderLists() {
  const nowMs = now();
  const v = L.dayView(state.data.events, state.day, state.filters);
  const list = (items) => items.map((e) => card(e, nowMs)).join('');
  const filtered = Object.values(state.filters).some(Boolean) ? ' with these filters' : '';

  $('little').innerHTML = '<h2>👶 Great for little ones</h2>'
    + (v.little.length ? list(v.little) : `<p class="empty">Nothing made for little ones${filtered} on this day.</p>`);

  const groups = L.PARTS.filter(([k]) => v.parts[k].length)
    .map(([k, label]) => `<h3 class="part">${label}</h3>${list(v.parts[k])}`).join('');
  const rest = $('rest');
  rest.hidden = Boolean(state.filters.little);
  rest.innerHTML = '<h2>Everything else</h2>' + (groups || `<p class="empty">Nothing else listed${filtered}.</p>`);

  const ongoing = $('ongoing');
  ongoing.hidden = !v.ongoing.length;
  ongoing.innerHTML = `<summary><h2>Ongoing · ${v.ongoing.length}</h2></summary>${list(v.ongoing)}`;

  const drive = $('drive');
  drive.hidden = !v.drive.length;
  drive.innerHTML = `<h2>🚗 Worth the drive</h2>${list(v.drive)}`;

  const open = L.placesOpen(state.data.places, state.day);
  const always = $('always');
  always.hidden = !open.length;
  if (always.dataset.day !== state.day) {     // only reset open/closed when the day changes
    always.open = v.littleCount < 3;
    always.dataset.day = state.day;
  }
  always.innerHTML = `<summary><h2>🏠 Always an option · ${open.length}</h2></summary>`
    + open.map(([p, h]) => placeCard(p, h)).join('')
    + '<p class="muted small">Hours change with the seasons; check before you go.</p>';
}

function renderGuide() {
  const g = state.data.guide;
  const url = g && L.safeUrl(g.url);
  const el = $('guide');
  el.hidden = !url;
  if (!url) return;
  el.innerHTML = `<h2>📖 From Loving Reno</h2>
    <a class="guide-card" href="${L.esc(url)}" target="_blank" rel="noopener">
      <span class="guide-title">${L.esc(g.shortTitle || g.title)}</span>
      <span class="muted">Their latest guide${g.published ? ` · ${L.esc(g.published)}` : ''} →</span>
    </a>`;
}

function renderFooter() {
  const nowMs = now();
  const sources = Object.values(state.data.status?.sources ?? {});
  const down = sources.filter((s) => !s.ok);
  const gen = state.data.generatedAt;
  $('footer').innerHTML = `
    ${down.map((s) => `<p class="warn small">${L.esc(s.label)} couldn't be reached on the last update`
      + `${s.error ? ` (${L.esc(s.error)})` : ''}${s.count ? '; showing its last good list' : ''}.</p>`).join('')}
    <p class="small">Updated ${gen ? L.esc(L.ago(gen, nowMs)) : 'never'} · Sources: ${sources.map((s) => L.esc(s.label)).join(', ') || 'none yet'}</p>
    <p class="small">Times, places and prices come from each source; check its link before you go.</p>
    <p class="small"><a href="https://natanforestree.github.io/arcadipelago/">← More on Arcadipelago</a></p>`;
}

function render() {
  renderNotice();
  renderDays();
  renderWeather();
  renderChips();
  renderLists();
  renderGuide();
  renderFooter();
}

async function main() {
  const [events, weather, status, guide, places] = await Promise.all([
    loadJson('events.json', null), loadJson('weather.json', null), loadJson('status.json', null),
    loadJson('guide.json', null), loadJson('places.json', []),
  ]);
  state.data = {
    events: Array.isArray(events?.events) ? events.events : [],
    generatedAt: events?.generatedAt ?? null,
    weather, status, guide,
    places: Array.isArray(places) ? places : [],
  };
  state.day = L.renoDate(now());
  render();
}

$('days').addEventListener('click', (ev) => {
  const b = ev.target.closest('button[data-day]');
  if (b && state.data) { state.day = b.dataset.day; render(); }
});
$('chips').addEventListener('click', (ev) => {
  const b = ev.target.closest('button[data-filter]');
  if (!b || !state.data) return;
  state.filters[b.dataset.filter] = !state.filters[b.dataset.filter];
  saveFilters();
  render();
});
main().catch((err) => {
  console.error(err);
  $('notice').innerHTML = '<p>Something went wrong loading the list. Try reloading.</p>';
});
```

- [ ] **Step 4: Write** `dev/make_fixture.py`

```python
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
```

- [ ] **Step 5: Generate fixtures and check in a real browser**

```bash
python3 dev/make_fixture.py --today 2026-10-10
python3 -m http.server 8000 >/dev/null 2>&1 &     # from the repo root; stop it when done
```

Use the Playwright browser tools (`browser_navigate`, `browser_resize`, `browser_take_screenshot`, `browser_evaluate`, `browser_click`, `browser_console_messages`). Check each item and **fix what fails**.

1. **Full, at 390×844:** `http://localhost:8000/docs/?data=../dev/fixture/full/&now=2026-10-10T10:45:00-07:00`
   - The arch animates and fits.
   - There's no horizontal scroll: `document.documentElement.scrollWidth <= 390`.
   - "Great for little ones" lists the Fall Festival, the storytime and Small Wonder Wednesday.
   - Small Wonder Wednesday shows **on now**. So do the 9:30 storytime and the 10:00 Carson hayride, because events with no end time count as on for 2 hours.
   - "Everything else" has Morning / Afternoon / Evening / Late headings. (An "All day" heading appears only when there is a general, local all-day event; this fixture day has none, so its absence is correct.)
   - The `<img …> Totally Safe Show` title shows as **literal text**, and no dialog appears.
   - "Ongoing · 1" is collapsed.
   - "Worth the drive" shows the Tahoe and Carson events with 🚗 drive badges.
   - "Always an option" is **collapsed** (there are 3 little-ones events).
   - The Loving Reno card is there, and Brandi Carlile has the "Loving Reno pick" badge.
   - The footer lists the sources.
   - The console has no errors.
2. **Filters:**
   - Tap "Hide 21+": Late Night Comedy disappears.
   - Reload: the chip is still on (localStorage).
   - Tap "Little ones only": "Everything else" hides.
   - Turn both off again.
3. **Tomorrow:** tap "Tomorrow". "On now" is gone, the weather changes and Toddler Time is listed.
4. **Empty:** `?data=../dev/fixture/empty/&now=2026-10-10T10:45:00-07:00` shows "Nothing made for little ones on this day.", and "Always an option" is **expanded**.
5. **Partial:** `?data=../dev/fixture/partial/&now=…` shows "Weather unavailable for this day." and a footer note "Ticketmaster couldn't be reached on the last update (HTTP 503 (ticketmaster))".
6. **Failing:** `?data=../dev/fixture/failing/` shows the ⚠️ "Last updated 9 hours ago" notice at the top. Leave out `&now=` here, because the 9 hours are measured from the real clock.
7. **Full at 1280×800:** the content is centred at max 760 px, the arch is at 3× (528 px wide), and nothing is stretched.

Save screenshots of 1 (390 px) and 7 (1280 px) in the scratchpad, to share with Nathan.

- [ ] **Step 6: Add the preview instructions to the README**

```markdown
## Previewing the page

    python3 dev/make_fixture.py --today 2026-10-10
    python3 -m http.server 8000
    open "http://localhost:8000/docs/?data=../dev/fixture/full/&now=2026-10-10T10:45:00-07:00"

Variants: `full`, `empty`, `partial`, `failing`. Without `?data=` the page reads
`docs/data/` (the live data once the collector has run).
```

- [ ] **Step 7: Commit, push and check the live page**

```bash
npm test && python3 -m unittest discover -s tests
git add docs/index.html docs/style.css docs/app.js dev/make_fixture.py README.md
git commit -m "The page: cozy pixel Reno Today with day switcher, filters and sections"
git pull --rebase -q && git push
```
Wait for Pages (`gh api repos/natanforestree/reno-today/pages/builds/latest -q .status` shows `built`). Then open `https://natanforestree.github.io/reno-today/` at 390×844 in Playwright and confirm that real data renders.

---

### Task 20: Worker dispatches Reno Today hourly (in `finals-radar`)

**Files** (all in `~/Documents/code/finals-radar/worker/`):
- Modify: `src/index.js` (the scheduled handler and the dispatch function)
- Modify: `test/worker.test.js` (new cron tests)
- Modify: `wrangler.toml` (two vars)
- Modify: `README.md` (one paragraph)

**Interfaces:**
- Consumes:
  - the existing Worker `ruby-radar`, deployed at `https://ruby-radar.nathanforestlee.workers.dev`
  - the Worker secret `GITHUB_TOKEN` (fine-grained PAT, currently `finals-radar` only, Actions read/write)
- Produces:
  - On every `*/10` tick, it dispatches `finals-radar`'s `collect.yml` (unchanged).
  - On the tick whose UTC minute is **30**, it also dispatches `natanforestree/reno-today`'s `collect.yml` (vars `RENO_TODAY_REPO` and `RENO_TODAY_WORKFLOW`).

The finals-radar repo gets data commits from GitHub Actions every 10 minutes, so pull with rebase before pushing.

- [ ] **Step 1: Write the failing tests.** Append inside the existing `describe('cron', …)` block in `worker/test/worker.test.js`, before its closing `});`.

```js
  const RENO = { RENO_TODAY_REPO: 'natanforestree/reno-today', RENO_TODAY_WORKFLOW: 'collect.yml' };
  const tick = (minute) => ({ cron: '*/10 * * * *', scheduledTime: Date.UTC(2026, 9, 5, 21, minute) });
  const RUBY_URL = 'https://api.github.com/repos/natanforestree/finals-radar/actions/workflows/collect.yml/dispatches';
  const RENO_URL = 'https://api.github.com/repos/natanforestree/reno-today/actions/workflows/collect.yml/dispatches';

  test('also runs Reno Today on the :30 tick', async () => {
    const fetchMock = mock.method(globalThis, 'fetch', async () => new Response(null, { status: 204 }));
    const ctx = makeCtx();
    await worker.scheduled(tick(30), makeEnv({ GITHUB_TOKEN: 't', ...RENO }), ctx);
    assert.equal(ctx.pending.length, 1);
    await Promise.all(ctx.pending);
    assert.deepEqual(fetchMock.mock.calls.map((c) => c.arguments[0]).sort(), [RUBY_URL, RENO_URL]);
  });

  test('leaves Reno Today alone on the other ticks', async () => {
    const fetchMock = mock.method(globalThis, 'fetch', async () => new Response(null, { status: 204 }));
    for (const minute of [0, 10, 20, 40, 50]) {
      const ctx = makeCtx();
      await worker.scheduled(tick(minute), makeEnv({ GITHUB_TOKEN: 't', ...RENO }), ctx);
      await Promise.all(ctx.pending);
    }
    assert.deepEqual([...new Set(fetchMock.mock.calls.map((c) => c.arguments[0]))], [RUBY_URL]);
  });

  test('skips Reno Today when its repo var is missing', async () => {
    const fetchMock = mock.method(globalThis, 'fetch', async () => new Response(null, { status: 204 }));
    const ctx = makeCtx();
    await worker.scheduled(tick(30), makeEnv({ GITHUB_TOKEN: 't' }), ctx);
    await Promise.all(ctx.pending);
    assert.deepEqual(fetchMock.mock.calls.map((c) => c.arguments[0]), [RUBY_URL]);
  });

  test('a Reno Today failure is logged with its repo and does not stop Ruby Radar', async () => {
    const fetchMock = mock.method(globalThis, 'fetch', async (url) =>
      url === RENO_URL ? new Response('{"message":"Not Found"}', { status: 404 }) : new Response(null, { status: 204 }));
    const errors = mock.method(console, 'error', () => {});
    const ctx = makeCtx();
    await worker.scheduled(tick(30), makeEnv({ GITHUB_TOKEN: 't', ...RENO }), ctx);
    await Promise.all(ctx.pending);
    assert.equal(fetchMock.mock.callCount(), 2);
    assert.equal(errors.mock.callCount(), 1);
    assert.match(errors.mock.calls[0].arguments.join(' '), /reno-today.*404/);
  });
```

The existing cron tests use `scheduledTime: START * 1000`, which is minute 28, so they keep dispatching only Ruby Radar.

- [ ] **Step 2: Run them to make sure they fail**

Run: `cd ~/Documents/code/finals-radar/worker && npm test`
Expected: the first and last new tests fail (one fetch instead of two). The others pass.

- [ ] **Step 3: Implement.** In `worker/src/index.js`:

Update the header comment's point 2:
```js
// 2. A cron trigger that asks GitHub to run the collect workflow every
//    10 minutes, because GitHub's own schedule drifts and drops runs. On the
//    :30 tick it also runs Reno Today's collector (natanforestree/reno-today).
```

Replace the `scheduled` handler:
```js
  async scheduled(event, env, ctx) {
    ctx.waitUntil(runScheduled(event, env));
  },
```

Replace the whole `// ---- Cron: run the collect workflow` section with:
```js
// ---- Cron: run the collect workflows ---------------------------------------

// Reno Today (RENO_TODAY_REPO) refreshes hourly, so it goes on one tick an hour.
const RENO_TODAY_MINUTE = 30;

async function runScheduled(event, env) {
  const jobs = [dispatchWorkflow(env, env.GITHUB_REPO, env.GITHUB_WORKFLOW)];
  if (env.RENO_TODAY_REPO && new Date(event.scheduledTime).getUTCMinutes() === RENO_TODAY_MINUTE) {
    jobs.push(dispatchWorkflow(env, env.RENO_TODAY_REPO, env.RENO_TODAY_WORKFLOW || 'collect.yml'));
  }
  await Promise.all(jobs);
}

async function dispatchWorkflow(env, repo, workflow) {
  if (!env.GITHUB_TOKEN) return;
  const url = `https://api.github.com/repos/${repo}/actions/workflows/${workflow}/dispatches`;
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${env.GITHUB_TOKEN}`,
        Accept: 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': 'ruby-radar-worker',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ ref: 'main' }),
    });
    if (!res.ok) {
      const detail = (await res.text().catch(() => '')).replace(/\s+/g, ' ').slice(0, 300);
      console.error(`dispatch ${repo} failed: HTTP ${res.status} ${detail}`);
    }
  } catch (err) {
    console.error(`dispatch ${repo} failed: ${err}`);
  }
}
```

In `worker/wrangler.toml`, under `[vars]`:
```toml
RENO_TODAY_REPO = "natanforestree/reno-today"
RENO_TODAY_WORKFLOW = "collect.yml"
```
And change the secrets comment's `GITHUB_TOKEN` line to: `#   GITHUB_TOKEN  fine-grained PAT: finals-radar + reno-today, Actions: read and write`.

In `worker/README.md`, after the GitHub token step, add:
```markdown
   The same token also runs Reno Today (`natanforestree/reno-today`): on the
   :30 tick the Worker dispatches that repo's `collect.yml` too
   (`RENO_TODAY_REPO` / `RENO_TODAY_WORKFLOW` in wrangler.toml). The token
   needs both repos under "Repository access".
```
In the "Checking the timer" section of the same README, change `collect dispatch failed: HTTP <status> <GitHub's message>` to `dispatch <repo> failed: HTTP <status> <GitHub's message>` (the new log text).

- [ ] **Step 4: Run all Worker tests**

Run: `cd ~/Documents/code/finals-radar/worker && npm test`
Expected: all pass (82 existing + 4 new = 86)

- [ ] **Step 5: Commit, deploy, push**

```bash
cd ~/Documents/code/finals-radar
git add worker/src/index.js worker/test/worker.test.js worker/wrangler.toml worker/README.md
git commit -m "Worker: also dispatch Reno Today's collector hourly at :30"
cd worker && npx wrangler whoami && npx wrangler deploy && cd ..
git pull --rebase --autostash -q && git push
```
If `wrangler whoami` says you're not logged in:
1. Run `npx wrangler login --browser=false` in the background.
2. Open the printed URL with the Chrome tools.
3. Let Nathan approve. Ask before clicking Allow; it's an OAuth grant.

- [ ] **Step 6: Nathan adds `reno-today` to the token (he does this himself)**

Tell Nathan exactly:

> GitHub → your picture → Settings → Developer settings → Personal access tokens → **Fine-grained tokens** → the Ruby Radar timer token → **Edit** → Repository access: add **natanforestree/reno-today** → **Update**. The permissions (Actions: read and write) already apply to every selected repo. You don't need a new token, so nothing needs re-entering in Cloudflare.

Once he says it's done, wait for the next `:30` UTC tick and verify:
```bash
gh run list --repo natanforestree/reno-today --workflow collect.yml --limit 3 --json event,createdAt,conclusion
```
Expected: a `workflow_dispatch` run created at about `HH:30`. If it's missing, check `npx wrangler tail` around the tick for `dispatch natanforestree/reno-today failed: HTTP 404` (the token doesn't cover the repo yet) or `HTTP 403`.

- [ ] **Step 7: Update the Ruby Radar memory note**

Add one line to `/Users/nathan/.claude/projects/-Users-nathan-Documents-code/memory/finals-radar-ruby-radar.md`:
- The Worker also dispatches `natanforestree/reno-today` hourly at `:30`.
- The PAT now covers both repos.

---

### Task 21: Secrets: Ticketmaster key and Discord webhook

**Files:**
- Create: `tests/fixtures/real/ticketmaster.json` (recorded with the real key; the key must not be in it)
- Modify: `collector/sources/ticketmaster.py` and its tests, only if the real response differs from the documented shape

**Interfaces:**
- Consumes: Task 10's parser, Task 15's run, Task 16's workflow (`force_digest` input).
- Produces: repo secrets `TICKETMASTER_KEY` and `DISCORD_WEBHOOK_URL`, a real Ticketmaster recording, and a first Discord digest.

Rules from the Ruby Radar setup:
- Nathan creates accounts and credentials himself.
- Claude never types a secret into a page and never shows it in chat.
- Values move by clipboard: Nathan copies the value and says "copied". Claude checks its shape, uses it, then clears the clipboard.
- **Never** ask Nathan to paste a command containing `pbpaste`, because copying the command overwrites the copied secret.

- [ ] **Step 1: Ticketmaster key (Nathan)**

Tell Nathan:

> Go to https://developer.ticketmaster.com → **Get your API key** and sign up (free). Then **My Apps** → your default app → copy the **Consumer Key**. Tell me "copied" when it's on your clipboard.

- [ ] **Step 2: Check it, record a real response, store the secret, clear the clipboard**

```bash
cd ~/Documents/code/reno-today
pbpaste | tr -d '[:space:]' | python3 -c "import sys,re; k=sys.stdin.read(); print('ok' if re.fullmatch(r'[A-Za-z0-9]{20,64}', k) else f'unexpected ({len(k)} chars)')"
TICKETMASTER_KEY="$(pbpaste | tr -d '[:space:]')" python3 - <<'EOF'
import json, os, sys
from datetime import datetime
sys.path.insert(0, "collector")
import model, net
from sources import ticketmaster as tm
key = os.environ["TICKETMASTER_KEY"]
start, end = model.window(datetime.now(model.LA))
data = net.get_json(tm.URL.format(key=key, start=model.utc(start), end=model.utc(end), page=0), label="ticketmaster")
def strip(o):
    if isinstance(o, dict):
        return {k: strip(v) for k, v in o.items()
                if k not in ("_links", "images", "seatmap", "products", "sales", "promoter", "promoters",
                             "outlets", "accessibility", "ticketLimit", "ada", "boxOfficeInfo", "generalInfo")}
    if isinstance(o, list):
        return [strip(v) for v in o]
    return o
data = strip(data)
if "_embedded" in data:
    data["_embedded"]["events"] = data["_embedded"]["events"][:40]
text = json.dumps(data, indent=1)
assert key not in text, "the key leaked into the recording"
open("tests/fixtures/real/ticketmaster.json", "w").write(text)
print(data["page"], "->", len(tm.parse(data.get("_embedded", {}).get("events", []))), "events parsed")
EOF
pbpaste | tr -d '[:space:]' | gh secret set TICKETMASTER_KEY --repo natanforestree/reno-today
pbcopy < /dev/null
python3 -m unittest discover -s tests -v 2>&1 | tail -5
```
Expected:
- `ok`, then a page summary and roughly 50–200 events parsed.
- The secret is set and all tests pass, including `test_real_recording_parses` for Ticketmaster.

If the real data shows a shape the parser misses (a field name, junk listings such as "Premium Seating"), fix `ticketmaster.py` and add that case to `tests/fixtures/ticketmaster.json` with a test. Either way, commit the recording (plus any parser fixes):
```bash
git add tests/fixtures/real/ticketmaster.json collector/sources/ticketmaster.py tests/test_ticketmaster.py tests/fixtures/ticketmaster.json
git commit -m "Ticketmaster: real recording (and parser fixes from it)"
git pull --rebase -q && git push
```

- [ ] **Step 3: Discord webhook (Nathan)**

Tell Nathan:

> In Discord, open the channel you both want the morning message in → ⚙️ **Edit Channel** → **Integrations** → **Webhooks** → **New Webhook** → name it "Reno Today" → **Copy Webhook URL**. Tell me "copied". Treat the URL like a password: anyone with it can post in that channel. If it ever leaks, delete the webhook and make a new one.

- [ ] **Step 4: Check it, store it, clear the clipboard**

```bash
pbpaste | tr -d '[:space:]' | python3 -c "import sys,re; u=sys.stdin.read(); print('ok' if re.fullmatch(r'https://(discord|discordapp)\.com/api/webhooks/\d+/[\w-]+', u) else 'unexpected shape')"
pbpaste | tr -d '[:space:]' | gh secret set DISCORD_WEBHOOK_URL --repo natanforestree/reno-today
pbcopy < /dev/null
```
Expected: `ok`, and the secret is set.

- [ ] **Step 5: Send the first digest (tell Nathan a test message is coming)**

```bash
gh workflow run collect.yml --repo natanforestree/reno-today -f force_digest=true
sleep 5; gh run watch --repo natanforestree/reno-today "$(gh run list --repo natanforestree/reno-today --workflow collect.yml --limit 1 --json databaseId -q '.[0].databaseId')"
gh run view --repo natanforestree/reno-today --log "$(gh run list --repo natanforestree/reno-today --workflow collect.yml --limit 1 --json databaseId -q '.[0].databaseId')" | grep -E "digest|events;"
```
Expected: the log shows `digest sent`, and Nathan confirms the message arrived and looks right. Also make sure the webhook URL does not appear anywhere in the log; GitHub masks secrets as `***`.

The real 07:xx digest starts tomorrow morning. Tell Nathan to expect it between about 7:30 and 7:50.

---
# Phase 2: Family sources and "Always an option"

Phase 2 source research was done on 2026-10-05; the findings are summarised in each task. Sources that were checked and **skipped**:
- **North Lake Tahoe** (laketahoetravel.com): its `robots.txt` disallows every URL with a query string.
- **Wilbur D. May Center**: it has no calendar of its own; its programs appear on the county parks calendar (Task 26).
- **Artown**: no feed, and it runs in July only. Revisit in June 2027.
- **Nevada Museum of Art**: its only family program, "Hands ON! Second Saturday", is a standing monthly event (Task 27). Its other events are adult and would need an HTML scrape.

### Task 22: "Always an option" places (`places.json`)

**Files:**
- Modify: `places.json` (it's `[]` since Task 1)
- Create: `tests/test_places_data.py`

**Interfaces:**
- Consumes: `places.WEEKDAYS` and `places.open_on` (Task 14). The page and the digest already read `docs/data/places.json`, which `collect.py` copies from `places.json` on every refresh.
- Produces: 15 hand-checked places in the Task 14 place shape, plus a `checked` date.

The list was researched on 2026-10-05 from each place's official site. Points to keep in mind:
- **Seasonal park hours** (Washoe County: 8–5 from the November time change; City of Reno: 6–7 in winter) are written in `notes`. The `hours` field holds today's schedule. **Re-check the county park hours on 2026-11-01** and update `hours` to `08:00-17:00` for Rancho San Rafael and Galena Creek.
- **The Discovery** also opens on Mondays during school breaks and in summer; that's in `notes`.
- **Truckee River Walk & Wingfield Park** is medium confidence: the city map still showed Wingfield as closed after its June 2026 reopening.
- **Left out on purpose:**
  - Sierra Safari Zoo (closed in 2024)
  - the Carson children's museum (its site is down)
  - Lazy 5 splash park (closed for 2026)
  - Bartley Ranch and Hidden Valley (to keep the list near 15)

- [ ] **Step 1: Write the failing test** `tests/test_places_data.py`

```python
import json
import os
import re
import unittest
from datetime import date, timedelta

from helpers import ROOT
import places

AREAS = {"reno", "sparks", "tahoe", "carson", "virginia-city", "other"}
HOURS = re.compile(r"^(\d\d:\d\d-\d\d:\d\d|dawn-dusk)$")


class PlacesDataTest(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(ROOT, "places.json"), encoding="utf-8") as f:
            self.places = json.load(f)

    def test_shape(self):
        self.assertGreaterEqual(len(self.places), 12)
        names = set()
        for p in self.places:
            with self.subTest(place=p.get("name")):
                self.assertTrue(p["name"])
                self.assertNotIn(p["name"], names)
                names.add(p["name"])
                self.assertIn(p["area"], AREAS)
                self.assertIn(p["setting"], ("indoor", "outdoor", "both"))
                self.assertLessEqual(len(p["goodFor"]), 40)
                self.assertEqual(set(p["hours"]), set(places.WEEKDAYS))
                for h in p["hours"].values():
                    self.assertTrue(h is None or HOURS.match(h), h)
                self.assertTrue(p["months"] is None or all(1 <= m <= 12 for m in p["months"]))
                self.assertTrue(p["url"].startswith("https://"))
                self.assertIsInstance(p["free"], bool)
                self.assertRegex(p["checked"], r"^\d{4}-\d\d-\d\d$")

    def test_something_is_open_every_day_of_the_year(self):
        day = date(2026, 1, 1)
        while day.year == 2026:
            self.assertTrue(places.open_on(self.places, day.isoformat()), day)
            day += timedelta(days=1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to make sure it fails**

Run: `python3 -m unittest discover -s tests -v`
Expected: `test_shape` fails (`0 not greater than or equal to 12`), and so does `test_something_is_open_every_day_of_the_year`

- [ ] **Step 3: Write** `places.json`

```json
[
  {"name": "The Discovery", "area": "reno", "goodFor": "Little Discoveries area for ages 0–5", "setting": "indoor", "hours": {"mon": null, "tue": "10:00-17:00", "wed": "10:00-20:00", "thu": "10:00-17:00", "fri": "10:00-17:00", "sat": "10:00-17:00", "sun": "10:00-17:00"}, "months": null, "free": false, "url": "https://nvdm.org/", "address": "490 S Center St, Reno, NV 89501", "notes": "Also open Mondays Memorial Day–Labor Day, on holidays and during WCSD school breaks. Free under age 1; $13.95 ages 1–5.", "checked": "2026-10-05"},
  {"name": "Wilbur D. May Museum", "area": "reno", "goodFor": "indoor garden with koi ponds", "setting": "indoor", "hours": {"mon": null, "tue": null, "wed": "10:00-16:00", "thu": "10:00-16:00", "fri": "10:00-16:00", "sat": "10:00-16:00", "sun": "12:00-16:00"}, "months": null, "free": false, "url": "https://www.washoecounty.gov/parks/maycenterhome/museum/index.php", "address": "1595 N Sierra St, Reno, NV 89503", "notes": "Inside Rancho San Rafael Park. Kids under 3 free. Special exhibition (higher price) runs January–May.", "checked": "2026-10-05"},
  {"name": "Rancho San Rafael Park & May Arboretum", "area": "reno", "goodFor": "chickens, dino playground, arboretum", "setting": "outdoor", "hours": {"mon": "08:00-19:00", "tue": "08:00-19:00", "wed": "08:00-19:00", "thu": "08:00-19:00", "fri": "08:00-19:00", "sat": "08:00-19:00", "sun": "08:00-19:00"}, "months": null, "free": true, "url": "https://www.washoecounty.gov/parks/parks/park_directory_pages/north_region/rancho_san_rafael_regional_park.php", "address": "1595 N Sierra St, Reno, NV 89503", "notes": "County posted hours change by season: 8–7 fall, 8–5 from the Nov time change, 8–7 spring, 8–9 Memorial Day–Labor Day. Nevada Farms and Families area has a turkey, chickens, a pond and playgrounds; its Discovery Room playroom opens summer Wed–Fri.", "checked": "2026-10-05"},
  {"name": "Idlewild Park", "area": "reno", "goodFor": "playground, duck pond, river paths", "setting": "outdoor", "hours": {"mon": "06:00-19:00", "tue": "06:00-19:00", "wed": "06:00-19:00", "thu": "06:00-19:00", "fri": "06:00-19:00", "sat": "06:00-19:00", "sun": "06:00-19:00"}, "months": null, "free": true, "url": "https://www.reno.gov/parks-and-recreation/parks-facilities/index.php", "address": "1905 Idlewild Dr, Reno, NV 89509", "notes": "City winter hours 6am–7pm (Oct 1–Mar 31); summer hours not published. Splash pad 11–7 daily and kids' train (Tue–Fri 11–3, Sat–Sun 11–4) run Memorial Day–Labor Day. Designated duck-feeding spot.", "checked": "2026-10-05"},
  {"name": "Virginia Lake Park", "area": "reno", "goodFor": "lake loop, duck feeding, playground", "setting": "outdoor", "hours": {"mon": "06:00-19:00", "tue": "06:00-19:00", "wed": "06:00-19:00", "thu": "06:00-19:00", "fri": "06:00-19:00", "sat": "06:00-19:00", "sun": "06:00-19:00"}, "months": null, "free": true, "url": "https://www.reno.gov/parks-and-recreation/parks-facilities/duck-feeding.php", "address": "1980 Lakeside Dr, Reno, NV 89509", "notes": "City winter hours 6am–7pm (Oct 1–Mar 31); summer hours not published. Designated duck-feeding spot (feed in the water, duck food only).", "checked": "2026-10-05"},
  {"name": "Truckee River Walk & Wingfield Park", "area": "reno", "goodFor": "riverside stroller path downtown", "setting": "outdoor", "hours": {"mon": "06:00-19:00", "tue": "06:00-19:00", "wed": "06:00-19:00", "thu": "06:00-19:00", "fri": "06:00-19:00", "sat": "06:00-19:00", "sun": "06:00-19:00"}, "months": null, "free": true, "url": "https://www.reno.gov/parks-and-recreation/parks-facilities/whitewater-park.php", "address": "2 S Arlington Ave, Reno, NV 89501", "notes": "Hours are City winter park hours (Oct 1–Mar 31) for Wingfield Park; the riverside sidewalks are public. Wingfield reopened June 2026 after the Arlington bridges rebuild.", "checked": "2026-10-05"},
  {"name": "Sparks Marina Park", "area": "sparks", "goodFor": "lake loop path, beaches, playgrounds", "setting": "outdoor", "hours": {"mon": "06:00-22:00", "tue": "06:00-22:00", "wed": "06:00-22:00", "thu": "06:00-22:00", "fri": "06:00-22:00", "sat": "06:00-22:00", "sun": "06:00-22:00"}, "months": null, "free": true, "url": "https://www.sparksnv.gov/recreation/parks_facilities/find_a_park_or_facility.php?rz=catalogueDetails&id=172", "address": "300 Howard Dr, Sparks, NV 89434", "notes": "2-mile walking path, 2 beaches, 2 playgrounds, restrooms. Lifeguarded swim area in summer only.", "checked": "2026-10-05"},
  {"name": "Scheels (Reno-Sparks)", "area": "sparks", "goodFor": "16,000-gal aquarium + wildlife mountain", "setting": "indoor", "hours": {"mon": "09:30-21:00", "tue": "09:30-21:00", "wed": "09:30-21:00", "thu": "09:30-21:00", "fri": "09:30-21:00", "sat": "09:00-21:00", "sun": "10:00-18:00"}, "months": null, "free": true, "url": "https://www.scheels.com/store/reno-sparks/074", "address": "1200 Scheels Dr, Sparks, NV 89434", "notes": "Ferris wheel is $1 but riders must be 36 in. tall, so most 1-year-olds can't ride.", "checked": "2026-10-05"},
  {"name": "Sparks Library", "area": "sparks", "goodFor": "Young People's library + courtyard", "setting": "indoor", "hours": {"mon": "10:00-18:00", "tue": "10:00-18:00", "wed": "10:00-19:00", "thu": "10:00-18:00", "fri": "10:00-18:00", "sat": "10:00-16:00", "sun": "10:00-16:00"}, "months": null, "free": true, "url": "https://www.washoecountylibrary.us/libraries/sparks.php", "address": "1125 12th St, Sparks, NV 89431", "notes": "All branches closed Oct 30, Nov 11, Nov 26–27, Dec 10, Dec 25, Jan 1; close at 4pm Nov 25, Dec 24, Dec 31.", "checked": "2026-10-05"},
  {"name": "Downtown Reno Library", "area": "reno", "goodFor": "indoor trees and a fountain pond", "setting": "indoor", "hours": {"mon": "09:00-17:00", "tue": "09:00-17:00", "wed": "09:00-17:00", "thu": "09:00-17:00", "fri": "09:00-17:00", "sat": null, "sun": null}, "months": null, "free": true, "url": "https://www.washoecountylibrary.us/libraries/downtown-reno.php", "address": "301 S Center St, Reno, NV 89501", "notes": "Weekdays only. Same system-wide holiday closures as other Washoe County libraries.", "checked": "2026-10-05"},
  {"name": "Wonder & Unwind", "area": "reno", "goodFor": "play studio just for ages 0–5", "setting": "indoor", "hours": {"mon": null, "tue": "09:00-17:00", "wed": "09:00-17:00", "thu": "09:00-17:00", "fri": "09:00-17:00", "sat": "09:00-14:00", "sun": null}, "months": null, "free": false, "url": "https://wonderandunwind.com/", "address": "890 E Patriot Blvd Suite A, Reno, NV 89511", "notes": "Site lists a 3:30pm daily cutoff Tue–Fri. Sundays are private parties. 2-hour pass $16, day pass $26.", "checked": "2026-10-05"},
  {"name": "Animal Ark Wildlife Sanctuary", "area": "reno", "goodFor": "rescued wild animals, playground", "setting": "outdoor", "hours": {"mon": null, "tue": "10:00-16:30", "wed": "10:00-16:30", "thu": "10:00-16:30", "fri": "10:00-16:30", "sat": "10:00-16:30", "sun": "10:00-16:30"}, "months": [3, 4, 5, 6, 7, 8, 9, 10, 11], "free": false, "url": "https://www.animalark.org/", "address": "1265 Deerlodge Rd, Reno, NV", "notes": "Closes for winter after Thanksgiving; spring opening depends on weather (call ahead). 1-mile dirt/DG trail; umbrella strollers roll poorly.", "checked": "2026-10-05"},
  {"name": "Galena Creek Regional Park", "area": "reno", "goodFor": "forest pond, easy trails, bird exhibit", "setting": "both", "hours": {"mon": "08:00-19:00", "tue": "08:00-19:00", "wed": "08:00-19:00", "thu": "08:00-19:00", "fri": "08:00-19:00", "sat": "08:00-19:00", "sun": "08:00-19:00"}, "months": null, "free": true, "url": "https://www.washoecounty.gov/parks/parks/park_directory_pages/south_region/galena_creek_regional_park.php", "address": "18250 Mt Rose Hwy, Reno, NV 89511", "notes": "Hours shown are park hours (county seasonal schedule; 8–5 in winter). Visitor center: Wed–Sun 9–5 May 1–Oct 14, Fri–Sun 9–4 Oct 15–Apr 30. No entry fee listed.", "checked": "2026-10-05"},
  {"name": "Virginia & Truckee Railroad", "area": "virginia-city", "goodFor": "35-min historic train ride", "setting": "both", "hours": {"mon": "10:30-16:35", "tue": "10:30-16:35", "wed": "10:30-16:35", "thu": "10:30-16:35", "fri": "10:30-16:35", "sat": "10:30-16:35", "sun": "10:30-16:35"}, "months": [5, 6, 7, 8, 9, 10], "free": false, "url": "https://www.virginiatruckee.com/", "address": "166 F St, Virginia City, NV 89440", "notes": "Runs daily May 23–Oct 31; 7 departures from 10:30am to 4:00pm. Kids 4 and under ride free.", "checked": "2026-10-05"},
  {"name": "Sand Harbor (Lake Tahoe Nevada State Park)", "area": "tahoe", "goodFor": "gently sloping sandy beach", "setting": "outdoor", "hours": {"mon": "dawn-dusk", "tue": "dawn-dusk", "wed": "dawn-dusk", "thu": "dawn-dusk", "fri": "dawn-dusk", "sat": "dawn-dusk", "sun": "dawn-dusk"}, "months": null, "free": false, "url": "https://parks.nv.gov/parks/lake-tahoe-nevada-state-park", "address": "2005 Highway 28, Incline Village, NV 89450", "notes": "Posted hours are 8am to 1 hour after sunset. $10 per NV vehicle. Day-use reservation required for early-morning entry May 15–Sep 30. Busy Memorial Day–Labor Day; may close when full.", "checked": "2026-10-05"}
]
```

- [ ] **Step 4: Run the tests to make sure they pass**

Run: `python3 -m unittest discover -s tests -v`
Expected: all OK

- [ ] **Step 5: Check it on the page with fixture data**

```bash
python3 dev/make_fixture.py --today 2026-10-05
cp places.json dev/fixture/empty/places.json
python3 -m http.server 8000 >/dev/null 2>&1 &     # stop it afterwards with: kill %1
```
Open `http://localhost:8000/docs/?data=../dev/fixture/empty/&now=2026-10-05T09:00:00-07:00` at 390 px and check:
- "Always an option" is expanded.
- The Discovery is **not** listed (Monday).
- Animal Ark is **not** listed (it's closed Mondays). Tap **Tomorrow** and it appears (October is in its season).
- Each card has "Check hours" and "Directions".

- [ ] **Step 6: Commit and push**

```bash
git add places.json tests/test_places_data.py
git commit -m "Always an option: 15 toddler-friendly places with checked hours"
git pull --rebase -q && git push
```

---

### Task 23: Washoe County Library (LibCal)

**Files:**
- Create: `collector/sources/library.py`, `tests/test_library.py`, `tests/fixtures/library.json`, `tests/fixtures/real/library.json` (recorded)
- Modify: `collector/sources/__init__.py`

**Interfaces:**
- Consumes: `net.get_json`, `model.make_event / venue / price_range / plain / FREE / LA`, `SourceError`, and the `EVERY` support in `collect.py` (Task 15)
- Produces: `library.parse(results) -> list[event]`, `NAME = "library"`, `EVERY = 12 h`, `BRANCHES`

What we know about LibCal (researched 2026-10-05):
- **Endpoint:** `https://events.washoecountylibrary.us/ajax/calendar/list?c=12809&date=YYYY-MM-DD&perpage=100&page=1&audience=&cats=&camps=&inc=0`. It's the public calendar's JSON (no key), and returns **one day per request**: `{"total_results", "perpage", "results": [...]}`.
- **Robots:** `robots.txt` allows `/ajax/` and asks for **`Crawl-delay: 10`**. That makes 8 requests with 10 s gaps (about 80 s), so `EVERY = 12 h`.
- **Fields:**
  - `startdt` / `enddt` are local naive `"2026-10-08 10:15:00"`.
  - All-day events run `00:00:00`–`23:59:59`.
  - `campus` is the branch name.
  - `audiences[].id`: 1785 Babies & Toddlers, 1784 Preschool, 1782 Kids, 1783 Teens, 1780 Adults.
  - Other fields: `categories_arr[].name`, `online_event`, `recurring_event`, `registration_cost`.
- **Volume:** about 25–30 events per weekday; about 18 baby/toddler events a week.
- **Quirks:**
  - "Baby Social" ends at 22:50 (a typo), so timed events longer than 6 h lose their end.
  - Multi-week all-day series (an escape room) repeat every day, so all-day + recurring counts as **ongoing**.
- **Branch addresses:** Downtown and Sparks were confirmed on the library site. **Verify the rest in Step 6.**

- [ ] **Step 1: Write the fixture** `tests/fixtures/library.json`

```json
{"total_results": 6, "perpage": 100, "status": 200, "results": [
  {"id": 1001, "title": "Baby Social", "startdt": "2026-10-05 10:30:00", "enddt": "2026-10-05 22:50:00", "all_day": false,
   "url": "https://events.washoecountylibrary.us/event/1001", "campus": "Incline Village Library", "location": "",
   "audiences": [{"id": 1785, "name": "Babies & Toddlers"}], "categories_arr": [{"cat_id": 49158, "name": "Story Time"}],
   "description": "<p>Songs &amp; play for babies.</p>", "online_event": false, "recurring_event": true, "registration_cost": ""},
  {"id": 1002, "title": "Family Story Time", "startdt": "2026-10-06 10:15:00", "enddt": "2026-10-06 10:45:00", "all_day": false,
   "url": "https://events.washoecountylibrary.us/event/1002", "campus": "Downtown Reno Library", "location": "Young People's Library",
   "audiences": [{"id": 1782, "name": "Kids"}, {"id": 1784, "name": "Preschool"}, {"id": 1785, "name": "Babies & Toddlers"}],
   "categories_arr": [{"cat_id": 49158, "name": "Story Time"}],
   "description": "", "online_event": false, "recurring_event": true, "registration_cost": ""},
  {"id": 1003, "title": "The Archivist's Warning: Digital Escape Room Experience", "startdt": "2026-10-05 00:00:00",
   "enddt": "2026-10-05 23:59:59", "all_day": true, "url": "https://events.washoecountylibrary.us/event/1003",
   "campus": "Downtown Reno Library", "audiences": [{"id": 1782, "name": "Kids"}, {"id": 1783, "name": "Teens"}],
   "categories_arr": [{"cat_id": 57057, "name": "Escape Room"}], "description": "", "online_event": false,
   "recurring_event": true, "registration_cost": ""},
  {"id": 1004, "title": "Online Book Club", "startdt": "2026-10-06 18:00:00", "enddt": "2026-10-06 19:00:00", "all_day": false,
   "url": "https://events.washoecountylibrary.us/event/1004", "campus": "Online Event", "audiences": [{"id": 1780, "name": "Adults"}],
   "categories_arr": [], "description": "", "online_event": true, "recurring_event": false, "registration_cost": ""},
  {"id": 1005, "title": "Lego Club", "startdt": "2026-10-07 16:00:00", "enddt": "2026-10-07 17:00:00", "all_day": false,
   "url": "https://events.washoecountylibrary.us/event/1005", "campus": "Mystery Branch Library", "audiences": [{"id": 1782, "name": "Kids"}],
   "categories_arr": [], "description": "", "online_event": false, "recurring_event": false, "registration_cost": ""},
  {"id": 1006, "title": "Adult Coloring", "startdt": "2026-10-07 14:00:00", "enddt": "2026-10-07 15:00:00", "all_day": false,
   "url": "https://events.washoecountylibrary.us/event/1006", "campus": "Sparks Library", "audiences": [{"id": 1780, "name": "Adults"}],
   "categories_arr": [], "description": "", "online_event": false, "recurring_event": false, "registration_cost": "$5.00"}
]}
```

- [ ] **Step 2: Write the failing tests** `tests/test_library.py`

```python
import os
import unittest
from unittest import mock

from helpers import fixture_json, fixture_path, la
import net
from sources import library
from sources.base import Context, SourceError

CTX = Context(la(2026, 10, 5), la(2026, 10, 13))


class LibraryParseTest(unittest.TestCase):
    def setUp(self):
        self.by_id = {e["id"]: e for e in library.parse(fixture_json("library.json")["results"])}

    def test_skips_online_events(self):
        self.assertEqual(sorted(self.by_id), ["library:1001", "library:1002", "library:1003", "library:1005", "library:1006"])

    def test_implausible_end_is_dropped_and_incline_is_tahoe(self):
        e = self.by_id["library:1001"]
        self.assertEqual(e["start"], "2026-10-05T10:30:00-07:00")
        self.assertIsNone(e["end"])
        self.assertEqual((e["area"], e["drive"]), ("tahoe", "~45 min"))
        self.assertTrue(e["_family"])
        self.assertIn("babies & toddlers", e["_tags"])
        self.assertEqual(e["price"], {"free": True})

    def test_branch_address(self):
        e = self.by_id["library:1002"]
        self.assertEqual(e["venue"]["name"], "Downtown Reno Library")
        self.assertEqual(e["venue"]["address"], "301 S Center St, Reno, NV 89501")
        self.assertEqual(e["end"], "2026-10-06T10:45:00-07:00")

    def test_all_day_series_is_ongoing(self):
        e = self.by_id["library:1003"]
        self.assertTrue(e["allDay"] and e["ongoing"])
        self.assertFalse(e["_family"])

    def test_unknown_branch_still_lists(self):
        e = self.by_id["library:1005"]
        self.assertEqual((e["venue"]["name"], e["area"]), ("Mystery Branch Library", "reno"))

    def test_registration_cost(self):
        self.assertEqual(self.by_id["library:1006"]["price"], {"min": 5.0, "max": 5.0})
        self.assertEqual(self.by_id["library:1006"]["area"], "sparks")


class LibraryFetchTest(unittest.TestCase):
    def test_one_request_per_day_with_the_crawl_delay(self):
        urls, sleeps = [], []
        with mock.patch.object(net, "get_json", lambda url, **kw: urls.append(url) or {"results": []}), \
                mock.patch.object(library.time, "sleep", sleeps.append):
            self.assertEqual(library.fetch(CTX), [])
        self.assertEqual([u.split("date=")[1][:10] for u in urls],
                         [f"2026-10-{d:02d}" for d in range(5, 13)])
        self.assertEqual(sleeps, [library.CRAWL_DELAY] * 7)

    def test_reshaped_body_is_a_source_error(self):
        with mock.patch.object(net, "get_json", lambda url, **kw: {"error": "x"}), \
                mock.patch.object(library.time, "sleep", lambda s: None):
            with self.assertRaises(SourceError):
                library.fetch(CTX)

    def test_real_recording_parses(self):
        if not os.path.exists(fixture_path("real/library.json")):
            self.skipTest("no real recording yet")
        events = library.parse(fixture_json("real/library.json")["results"])
        self.assertTrue(events)
        self.assertTrue(any(e["_family"] for e in events))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run them to make sure they fail**

Run: `python3 -m unittest discover -s tests -v`
Expected: `ImportError: cannot import name 'library'`

- [ ] **Step 4: Implement** `collector/sources/library.py`, and add `library` to `ALL` (after `aces`)

```python
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
    "South Valleys Library": ("15650A Wedge Pkwy, Reno, NV 89511", "Reno"),
    "North Valleys Library": ("1075 N Hills Blvd Ste 340, Reno, NV 89506", "Reno"),
    "Sparks Library": ("1125 12th St, Sparks, NV 89431", "Sparks"),
    "Spanish Springs Library": ("7100A Pyramid Lake Hwy, Sparks, NV 89436", "Sparks"),
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
```

- [ ] **Step 5: Run the tests to make sure they pass**

Run: `python3 -m unittest discover -s tests -v`
Expected: all OK

- [ ] **Step 6: Verify the branch table, record a real response, try it live**

Check each `BRANCHES` address against its page under `https://www.washoecountylibrary.us/libraries/`. Fix any that differ, and add any branch name a live run reports as unknown.

```bash
curl -sS -A "reno-today/1.0 (+https://github.com/natanforestree/reno-today)" \
  "https://events.washoecountylibrary.us/ajax/calendar/list?c=12809&date=$(date +%F)&perpage=100&page=1&audience=&cats=&camps=&inc=0" \
  | python3 -c "
import json, sys
d = json.load(sys.stdin)
sys.path.insert(0, 'collector')
import classify
for r in d['results']:
    r['description'] = ''
    r['shortdesc'] = classify.cues(r.get('shortdesc'))
json.dump(d, open('tests/fixtures/real/library.json', 'w'), indent=1)"
python3 -m unittest discover -s tests -p test_library.py -v
python3 dev/try_source.py library        # about 80 s because of the crawl delay
```
Expected:
- The recording test passes.
- `try_source` lists about 150–250 events with storytimes among them, and prints no "unknown branch" lines (or you've added those branches).

- [ ] **Step 7: Commit and push**

```bash
git add collector/sources/library.py collector/sources/__init__.py tests/test_library.py tests/fixtures/library.json tests/fixtures/real/library.json
git commit -m "Washoe County Library events (storytimes) from LibCal"
git pull --rebase -q && git push
```

---

### Task 24: The Events Calendar sites (The Discovery, Carson City, South Lake Tahoe, Virginia City)

**Files:**
- Create: `collector/sources/tribe.py`, `tests/test_tribe.py`, `tests/fixtures/tribe.json`, `tests/fixtures/real/nvdm.json` (recorded)
- Modify: `collector/sources/__init__.py`

**Interfaces:**
- Consumes: `net.get_json`, `model.make_event / venue / price_range / plain / FREE / LA`, `SourceError`
- Produces:
  - `tribe.TribeSource(name, label, base, *, city, place=None, family_all=False, family_categories=(), family_before=None, adult_categories=(), skip_categories=())`, with `.NAME`, `.LABEL`, `.fetch(ctx)` and `.parse(items)`
  - `tribe.price_from(cost)`
  - Four instances in `sources/__init__.py`

These are WordPress sites running The Events Calendar, which has a REST API. Research on 2026-10-05:
- **Endpoint:** `{base}/wp-json/tribe/events/v1/events?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD%2023:59:59&per_page=50&page=N`. It returns `{"events": [...], "total", "total_pages"}`.
- **Fields:**
  - `start_date` and `end_date` are **local naive** `"YYYY-MM-DD HH:MM:SS"`. Parse them as Reno time and ignore `timezone`, which is wrong on some sites.
  - `title` and category names contain HTML entities (`Kids &amp; Families`, `Casey&#039;s`).
  - `venue` is a dict, **or `[]` when missing** (Virginia City).
  - `cost` is free text.
- **Robots:** all four sites allow it.

| Site | Base | Notes |
| --- | --- | --- |
| The Discovery (children's museum) | `https://nvdm.org` | About 10 events in 8 days, and **everything is family**. Skip "Members-only" and "Fundraiser". "Adults-only" is 21+. "Small Wonder Wednesday" (ages 5 and under) is the baby event. |
| Visit Carson City | `https://visitcarsoncity.com` | About 4 events in 8 days, with geo. Its category "Family" is already a little-ones tag. |
| Visit Lake Tahoe (South Shore) | `https://visitlaketahoe.com` | About 77 events in 8 days (2 pages). "Kids & Families" is used loosely (9 pm live music has it), so it counts only before 17:00. |
| Virginia City | `https://visitvirginiacitynv.com` | About 8 events, adult-leaning, with no categories. It posts some events twice; same-source dedupe merges them. |

- [ ] **Step 1: Write the fixture** `tests/fixtures/tribe.json`

```json
{"events": [
  {"id": 11, "title": "Small Wonder Wednesday", "start_date": "2026-10-07 09:00:00", "end_date": "2026-10-07 10:00:00",
   "all_day": false, "url": "https://nvdm.org/event/small-wonder-wednesday/2026-10-07/", "cost": "",
   "categories": [{"name": "Special Hours"}], "tags": [],
   "venue": {"venue": "The Discovery", "address": "490 S. Center Street", "city": "Reno", "stateprovince": "NV", "zip": "89501"}},
  {"id": 12, "title": "Members&#8217; Night", "start_date": "2026-10-08 17:00:00", "end_date": "2026-10-08 19:00:00",
   "all_day": false, "url": "https://nvdm.org/event/members-night/", "cost": "", "categories": [{"name": "Members-only"}],
   "tags": [], "venue": {"venue": "The Discovery", "city": "Reno"}},
  {"id": 13, "title": "Discovery After Dark", "start_date": "2026-10-09 18:00:00", "end_date": "2026-10-09 21:00:00",
   "all_day": false, "url": "https://nvdm.org/event/after-dark/", "cost": "$25 &#8211; $35",
   "categories": [{"name": "Adults-only"}], "tags": [], "venue": {"venue": "The Discovery", "city": "Reno"}},
  {"id": 14, "title": "Live Music at Casey&#039;s", "start_date": "2026-10-05 21:00:00", "end_date": "2026-10-05 23:00:00",
   "all_day": false, "url": "https://visitlaketahoe.com/event/live-music-caseys/", "cost": "Free",
   "categories": [{"name": "Kids &amp; Families"}, {"name": "Music &amp; Dance"}], "tags": [],
   "venue": {"venue": "Casey's", "city": "Zephyr Cove", "geo_lat": 39.0055, "geo_lng": -119.9486}},
  {"id": 15, "title": "Meyers Mountain Fall Festival", "start_date": "2026-10-10 10:00:00", "end_date": "2026-10-10 16:00:00",
   "all_day": false, "url": "https://visitlaketahoe.com/event/meyers-fall-festival/", "cost": "",
   "categories": [{"name": "Kids &amp; Families"}], "tags": [{"name": "Festival"}],
   "venue": {"venue": "Meyers Community Center", "city": "South Lake Tahoe", "stateprovince": "CA"}},
  {"id": 16, "title": "Ghost Walk", "start_date": "2026-10-10 00:00:00", "end_date": "2026-10-11 23:59:59",
   "all_day": true, "url": "https://visitvirginiacitynv.com/event/ghost-walk/", "cost": "", "categories": [], "tags": [],
   "venue": []}
], "total": 6, "total_pages": 1}
```

- [ ] **Step 2: Write the failing tests** `tests/test_tribe.py`

```python
import os
import unittest
from unittest import mock

from helpers import fixture_json, fixture_path, la
import net
from sources.base import Context, SourceError
from sources.tribe import TribeSource, price_from

ITEMS = fixture_json("tribe.json")["events"]
DISCOVERY = TribeSource("discovery", "The Discovery", "https://nvdm.org", city="Reno",
                        place=("The Discovery", "490 S Center St, Reno, NV 89501"), family_all=True,
                        adult_categories={"adults-only"}, skip_categories={"members-only", "fundraiser"})
TAHOE = TribeSource("southtahoe", "Visit Lake Tahoe", "https://visitlaketahoe.com", city="South Lake Tahoe",
                    family_categories={"kids & families"}, family_before=17)


class TribeTest(unittest.TestCase):
    def test_skips_members_only(self):
        ids = [e["id"] for e in DISCOVERY.parse(ITEMS)]
        self.assertNotIn("discovery:12", ids)
        self.assertEqual(len(ids), 5)

    def test_discovery_events_are_family_and_adults_only_is_flagged(self):
        by_id = {e["id"]: e for e in DISCOVERY.parse(ITEMS)}
        e = by_id["discovery:11"]
        self.assertTrue(e["_family"])
        self.assertEqual(e["start"], "2026-10-07T09:00:00-07:00")
        self.assertEqual(e["venue"]["address"], "490 S. Center Street, Reno, NV, 89501")
        self.assertTrue(by_id["discovery:13"]["_adult"])
        self.assertEqual(by_id["discovery:13"]["price"], {"min": 25.0, "max": 35.0})

    def test_kids_category_counts_only_in_the_daytime(self):
        by_id = {e["id"]: e for e in TAHOE.parse(ITEMS)}
        self.assertFalse(by_id["southtahoe:14"]["_family"])          # 9 pm live music
        self.assertTrue(by_id["southtahoe:15"]["_family"])           # 10 am festival
        self.assertEqual(by_id["southtahoe:14"]["title"], "Live Music at Casey's")
        self.assertEqual(by_id["southtahoe:14"]["price"], {"free": True})
        self.assertEqual((by_id["southtahoe:14"]["area"], by_id["southtahoe:14"]["drive"]), ("tahoe", "~65 min"))
        self.assertIn("kids & families", by_id["southtahoe:15"]["_tags"])
        self.assertIn("festival", by_id["southtahoe:15"]["_tags"])

    def test_missing_venue_list_and_all_day_run(self):
        e = {e["id"]: e for e in TAHOE.parse(ITEMS)}["southtahoe:16"]
        self.assertIsNone(e["venue"])
        self.assertTrue(e["allDay"])
        self.assertEqual((e["start"], e["end"]), ("2026-10-10T00:00:00-07:00", "2026-10-11T00:00:00-07:00"))

    def test_price_from(self):
        self.assertIsNone(price_from(""))
        self.assertEqual(price_from("Free"), {"free": True})
        self.assertEqual(price_from("$10"), {"min": 10.0, "max": 10.0})
        self.assertEqual(price_from("$10 &#8211; $25.50"), {"min": 10.0, "max": 25.5})
        self.assertEqual(price_from("Free for kids, $5 adults"), {"min": 5.0, "max": 5.0})
        self.assertIsNone(price_from("Donations welcome"))

    def test_fetch_pages_and_shape_check(self):
        ctx = Context(la(2026, 10, 5), la(2026, 10, 13))
        urls = []

        def fake(url, **kw):
            urls.append(url)
            return {"events": ITEMS[:3] if "page=1" in url else ITEMS[3:], "total_pages": 2}

        with mock.patch.object(net, "get_json", fake):
            got = TAHOE.fetch(ctx)
        self.assertEqual(len(urls), 2)
        self.assertTrue(urls[0].startswith("https://visitlaketahoe.com/wp-json/tribe/events/v1/events?"))
        self.assertIn("start_date=2026-10-05&end_date=2026-10-12%2023:59:59", urls[0])
        self.assertEqual(len(got), 6)
        with mock.patch.object(net, "get_json", lambda url, **kw: {"code": "rest_no_route"}):
            with self.assertRaises(SourceError):
                TAHOE.fetch(ctx)

    def test_real_recording_parses(self):
        if not os.path.exists(fixture_path("real/nvdm.json")):
            self.skipTest("no real recording yet")
        events = DISCOVERY.parse(fixture_json("real/nvdm.json")["events"])
        self.assertTrue(events)
        self.assertTrue(all(e["area"] == "reno" for e in events))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run them to make sure they fail**

Run: `python3 -m unittest discover -s tests -v`
Expected: `ModuleNotFoundError: No module named 'sources.tribe'`

- [ ] **Step 4: Implement** `collector/sources/tribe.py`

```python
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
                 family_before=None, adult_categories=(), skip_categories=()):
        self.NAME, self.LABEL = name, label
        self.base, self.city, self.place = base.rstrip("/"), city, place
        self.family_all, self.family_categories = family_all, set(family_categories)
        self.family_before = family_before
        self.adult_categories, self.skip_categories = set(adult_categories), set(skip_categories)

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
            if cats & self.skip_categories:
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
                text=plain(e.get("description") or ""), tags=cats | tags,
                family=self.family_all or bool(cats & self.family_categories and daytime),
                adult=bool(cats & self.adult_categories), kind="organiser"))
        return events
```

Add the instances to `collector/sources/__init__.py`:
```python
from sources import aces, library, ticketmaster, unr, wolfpack
from sources.tribe import TribeSource

DISCOVERY = TribeSource("discovery", "The Discovery", "https://nvdm.org", city="Reno",
                        place=("The Discovery", "490 S Center St, Reno, NV 89501"), family_all=True,
                        adult_categories={"adults-only"}, skip_categories={"members-only", "fundraiser"})
CARSON = TribeSource("carson", "Visit Carson City", "https://visitcarsoncity.com", city="Carson City")
SOUTH_TAHOE = TribeSource("southtahoe", "Visit Lake Tahoe", "https://visitlaketahoe.com", city="South Lake Tahoe",
                          family_categories={"kids & families"}, family_before=17)
VIRGINIA_CITY = TribeSource("vcity", "Virginia City", "https://visitvirginiacitynv.com", city="Virginia City")

ALL = [ticketmaster, unr, wolfpack, aces, library, DISCOVERY, CARSON, SOUTH_TAHOE, VIRGINIA_CITY]
```

- [ ] **Step 5: Run the tests to make sure they pass**

Run: `python3 -m unittest discover -s tests -v`
Expected: all OK

- [ ] **Step 6: Record The Discovery and try all four live**

```bash
curl -sS -A "reno-today/1.0 (+https://github.com/natanforestree/reno-today)" \
  "https://nvdm.org/wp-json/tribe/events/v1/events?start_date=$(date +%F)&per_page=50" \
  | python3 -c "
import json, sys
d = json.load(sys.stdin)
for e in d['events']:
    e['description'] = ''
    e['excerpt'] = ''
json.dump(d, open('tests/fixtures/real/nvdm.json', 'w'), indent=1)"
for s in discovery carson southtahoe vcity; do python3 dev/try_source.py $s; done
```
Expected:
- Each prints events.
- Discovery's are all in `reno`, and South Lake Tahoe's are in `tahoe`.
- If a base URL redirects (for example to `www.`), use the final host in `__init__.py`.

- [ ] **Step 7: Commit and push**

```bash
git add collector/sources/tribe.py collector/sources/__init__.py tests/test_tribe.py tests/fixtures/tribe.json tests/fixtures/real/nvdm.json
git commit -m "The Discovery, Carson City, South Lake Tahoe and Virginia City calendars"
git pull --rebase -q && git push
```

---

### Task 25: City of Reno and City of Sparks (Revize calendars with recurrence)

**Files:**
- Create: `collector/rrule.py`, `collector/sources/revize.py`, `tests/test_rrule.py`, `tests/test_revize.py`, `tests/fixtures/revize.json`
- Modify: `collector/sources/__init__.py`

**Interfaces:**
- Consumes: `net.get_json`, `model.make_event / venue / plain / city_from_address / LA`, `SourceError`
- Produces:
  - `rrule.expand(spec, first, last) -> [naive datetime]` (occurrence starts whose date is in [first, last])
  - `rrule.parse(spec)`
  - `revize.RevizeSource(name, label, host, webspace, *, city, page_url, skip_calendars, kid_calendars=(), calendar_names=None)`, with `.fetch(ctx)`, `.parse(items, first, last)` and `.EVERY = 12 h`

Research on 2026-10-05:
- **The platform:** reno.gov and sparksnv.gov run Revize. Each city's calendar is **one JSON array of every event** (Reno: about 370 events, about 650 KB, no date parameters): `https://{host}/_assets_/plugins/revizeCalendar/calendar_data_handler.php?webspace={renonv|sparksnv}&relative_revize_url=//builder1.revize.com&protocol=https:`
- **Robots:** neither site has a `robots.txt` (404).
- **Fields:**
  - `start` and `end` are local naive ISO.
  - `allDay` is present only when true.
  - `duration` is `"HH:MM"`.
  - `location` is free text, and Sparks runs a URL into it.
  - `desc` is **percent-encoded** HTML.
  - `url` is often empty.
  - `calendar_displays` holds calendar ids:
    - Reno: 3 = meetings, 5 parks & rec, 6 aquatics, 7 athletics, **8 youth**, 9 special events, 4 events.
    - Sparks: 1 community, 2 meetings, 5 agency postings.
- **Recurrence:** `rrule` is a string such as `"DTSTART:20260901T143000\nRDATE:…\nRRULE:FREQ=WEEKLY;INTERVAL=1;BYDAY=TU,WE;UNTIL=20261113T000000\nEXDATE:20261017T130000"`. It needs:
  - DAILY, WEEKLY+BYDAY and MONTHLY+BYDAY+BYSETPOS (Sparks)
  - INTERVAL, COUNT and EXDATE
  - **UNTIL as an inclusive date**: the Great Italian Festival has `UNTIL=20261011T000000` but runs Sat–Sun Oct 10–11
- **Junk to drop:**
  - Seconds noise: `16:00:40`.
  - Titles starting "CANCELED"/"CANCELLED".
  - "… Closure" entries.
  - Meetings-only events.

- [ ] **Step 1: Write the failing tests** `tests/test_rrule.py`

```python
import unittest
from datetime import date, datetime

import helpers  # noqa: F401
import rrule

OCT_FIRST, OCT_LAST = date(2026, 10, 5), date(2026, 10, 12)


def starts(spec, first=OCT_FIRST, last=OCT_LAST):
    return [d.strftime("%a %m-%d %H:%M") for d in rrule.expand(spec, first, last)]


class RruleTest(unittest.TestCase):
    def test_weekly_on_several_days(self):
        spec = "DTSTART:20260901T143000\nRRULE:FREQ=WEEKLY;INTERVAL=1;BYDAY=TU,WE;UNTIL=20261111T000000"
        self.assertEqual(starts(spec), ["Tue 10-06 14:30", "Wed 10-07 14:30"])

    def test_daily_until_is_an_inclusive_date(self):
        spec = "DTSTART:20261010T100000\nRDATE:20261010T100000\nRRULE:FREQ=DAILY;INTERVAL=1;UNTIL=20261011T000000"
        self.assertEqual(starts(spec), ["Sat 10-10 10:00", "Sun 10-11 10:00"])

    def test_exdate_removes_an_occurrence(self):
        spec = ("DTSTART:20261003T130000\nRRULE:FREQ=WEEKLY;INTERVAL=1;BYDAY=SU,SA;UNTIL=20261102T000000\n"
                "EXDATE:20261010T130000")
        self.assertEqual(starts(spec), ["Sun 10-11 13:00"])

    def test_no_until_runs_on(self):
        spec = "DTSTART:20260727T160040\nRRULE:FREQ=WEEKLY;INTERVAL=1;BYDAY=WE"
        self.assertEqual(starts(spec), ["Wed 10-07 16:00"])

    def test_every_other_week(self):
        spec = "DTSTART:20260902T090000\nRRULE:FREQ=WEEKLY;INTERVAL=2;BYDAY=WE"     # Sep 2, 16, 30, Oct 14
        self.assertEqual(starts(spec, date(2026, 9, 28), date(2026, 10, 18)), ["Wed 09-30 09:00", "Wed 10-14 09:00"])

    def test_monthly_by_setpos_and_ordinal(self):
        fourth_monday = "DTSTART:20260727T140000\nRRULE:FREQ=MONTHLY;INTERVAL=1;BYSETPOS=4;BYDAY=MO"
        self.assertEqual(starts(fourth_monday, date(2026, 10, 1), date(2026, 10, 31)), ["Mon 10-26 14:00"])
        second_saturday = "DTSTART:20260110T100000\nRRULE:FREQ=MONTHLY;BYDAY=2SA"
        self.assertEqual(starts(second_saturday, date(2026, 10, 1), date(2026, 10, 31)), ["Sat 10-10 10:00"])
        last_friday = "DTSTART:20260130T180000\nRRULE:FREQ=MONTHLY;BYDAY=-1FR"
        self.assertEqual(starts(last_friday, date(2026, 10, 1), date(2026, 10, 31)), ["Fri 10-30 18:00"])

    def test_count(self):
        spec = "DTSTART:20261001T090000\nRRULE:FREQ=DAILY;COUNT=7"                  # Oct 1–7
        self.assertEqual(starts(spec), ["Mon 10-05 09:00", "Tue 10-06 09:00", "Wed 10-07 09:00"])

    def test_plain_dtstart_and_bad_input(self):
        self.assertEqual(starts("DTSTART:20261008T120000"), ["Thu 10-08 12:00"])
        self.assertEqual(rrule.expand("nonsense", OCT_FIRST, OCT_LAST), [])

    def test_parse(self):
        dtstart, rule, rdates, exdates = rrule.parse("DTSTART:20261003T130000\nRRULE:FREQ=WEEKLY;BYDAY=SA\nEXDATE:20261010T130000")
        self.assertEqual(dtstart, datetime(2026, 10, 3, 13, 0))
        self.assertEqual(rule, {"FREQ": "WEEKLY", "BYDAY": "SA"})
        self.assertEqual(exdates, [datetime(2026, 10, 10, 13, 0)])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run them to make sure they fail**

Run: `python3 -m unittest discover -s tests -v`
Expected: `ModuleNotFoundError: No module named 'rrule'`

- [ ] **Step 3: Implement** `collector/rrule.py`

```python
"""Just enough RFC 5545 recurrence for the City of Reno and Sparks calendars:
FREQ=DAILY/WEEKLY/MONTHLY, INTERVAL, BYDAY (with ordinals such as 2SA or -1FR
when monthly), one BYSETPOS, BYMONTHDAY, COUNT, RDATE and EXDATE. UNTIL is read
as an inclusive date, because these calendars write it as midnight at the start
of the last day. Times are naive local times; seconds are dropped."""

import re
from datetime import date, datetime, timedelta

DAYS = {"MO": 0, "TU": 1, "WE": 2, "TH": 3, "FR": 4, "SA": 5, "SU": 6}


def _dt(value):
    value = value.strip()
    if "T" in value:
        return datetime.strptime(value[:15], "%Y%m%dT%H%M%S").replace(second=0)
    return datetime.strptime(value[:8], "%Y%m%d")


def parse(spec):
    """(dtstart, rule dict, rdates, exdates); dtstart is None if missing."""
    dtstart, rule, rdates, exdates = None, {}, [], []
    for line in (spec or "").replace("\\n", "\n").splitlines():
        name, _, value = line.partition(":")
        name = name.split(";")[0].strip().upper()
        try:
            if name == "DTSTART":
                dtstart = _dt(value)
            elif name == "RRULE":
                rule = dict(p.split("=", 1) for p in value.strip().split(";") if "=" in p)
            elif name == "RDATE":
                rdates += [_dt(v) for v in value.split(",") if v.strip()]
            elif name == "EXDATE":
                exdates += [_dt(v) for v in value.split(",") if v.strip()]
        except ValueError:
            continue
    return dtstart, rule, rdates, exdates


def _weekdays_in_month(year, month, weekday):
    d, out = date(year, month, 1), []
    while d.month == month:
        if d.weekday() == weekday:
            out.append(d)
        d += timedelta(days=1)
    return out


def _monthly_byday(day, rule):
    setpos = int(rule["BYSETPOS"]) if rule.get("BYSETPOS", "").lstrip("-").isdigit() else None
    for part in rule["BYDAY"].split(","):
        m = re.fullmatch(r"([+-]?\d+)?([A-Z]{2})", part.strip())
        if not m or m.group(2) not in DAYS or DAYS[m.group(2)] != day.weekday():
            continue
        n = int(m.group(1)) if m.group(1) else setpos
        if n is None:
            return True
        same = _weekdays_in_month(day.year, day.month, day.weekday())
        try:
            if same[n - 1 if n > 0 else n] == day:
                return True
        except IndexError:
            continue
    return False


def _matches(day, start, rule):
    freq = rule.get("FREQ")
    interval = int(rule.get("INTERVAL") or 1)
    if freq == "DAILY":
        return (day - start).days % interval == 0
    if freq == "WEEKLY":
        wanted = {DAYS[d[-2:]] for d in rule.get("BYDAY", "").split(",") if d[-2:] in DAYS} or {start.weekday()}
        weeks = ((day - timedelta(days=day.weekday())) - (start - timedelta(days=start.weekday()))).days // 7
        return day.weekday() in wanted and weeks % interval == 0
    if freq == "MONTHLY":
        if ((day.year - start.year) * 12 + day.month - start.month) % interval:
            return False
        if rule.get("BYMONTHDAY"):
            return day.day in {int(x) for x in rule["BYMONTHDAY"].split(",") if x.strip().lstrip("-").isdigit()}
        if rule.get("BYDAY"):
            return _monthly_byday(day, rule)
        return day.day == start.day
    return False


def expand(spec, first, last):
    """Occurrence starts (naive local datetimes) whose date is in [first, last]."""
    dtstart, rule, rdates, exdates = parse(spec)
    if dtstart is None:
        return []
    until = None
    if rule.get("UNTIL"):
        try:
            until = _dt(rule["UNTIL"]).date()
        except ValueError:
            until = None
    count = int(rule["COUNT"]) if (rule.get("COUNT") or "").isdigit() else None
    found = {dtstart} if first <= dtstart.date() <= last else set()
    if rule.get("FREQ"):
        day, n = dtstart.date(), 0
        stop = min(last, until) if until else last
        while day <= stop:
            if _matches(day, dtstart.date(), rule):
                n += 1
                if count and n > count:
                    break
                if day >= first:
                    found.add(datetime.combine(day, dtstart.time()))
            day += timedelta(days=1)
    found |= {r for r in rdates if first <= r.date() <= last and (until is None or r.date() <= until)}
    skip_days = {e.date() for e in exdates}
    return sorted(o for o in found if o.date() not in skip_days)
```

- [ ] **Step 4: Run the rrule tests to make sure they pass**

Run: `python3 -m unittest discover -s tests -p test_rrule.py -v`
Expected: all OK

- [ ] **Step 5: Write the fixture** `tests/fixtures/revize.json` (real records, trimmed)

```json
[
  {"id": 160, "title": "Ranger Walks", "start": "2026-10-10T14:00:00", "end": "2026-10-10T15:00:00", "duration": "01:00",
   "calendar_displays": ["5", "4", "9", "8"], "location": "Fisherman's Park", "desc": "%3Cp%3EGuided%20walk%20for%20families%3C%2Fp%3E", "url": ""},
  {"id": 128, "title": "Ward 6 Neighborhood Advisory Board Meeting", "start": "2026-10-05T17:30:00", "end": "2026-10-05T20:00:00",
   "duration": "02:30", "calendar_displays": ["3"], "location": "Reno City Hall 1 E. First Street", "desc": "", "url": ""},
  {"id": 173, "title": "CANCELED Planning Commission Meeting", "start": "2026-10-08T18:00:00", "end": "2026-10-08T23:00:00",
   "duration": "05:00", "calendar_displays": ["3", "4"], "location": "Reno City Hall", "desc": "", "url": ""},
  {"id": 285, "title": "44th Annual Great Italian Festival", "start": "2026-10-10T10:00:00", "end": "2026-10-10T20:00:00",
   "duration": "10:00", "calendar_displays": ["9"], "location": "Virginia St, between 2nd and 6th Downtown Reno",
   "rrule": "DTSTART:20261010T100000\nRDATE:20261010T100000\nRRULE:FREQ=DAILY;INTERVAL=1;UNTIL=20261011T000000",
   "desc": "", "url": "https://www.eldoradoreno.com/italian-festival"},
  {"id": 264, "title": "Food Truck Wednesdays", "start": "2026-07-27T16:00:40", "end": "2026-07-27T20:00:00", "duration": "04:00",
   "calendar_displays": ["9"], "location": "Cyan Park",
   "rrule": "DTSTART:20260727T160040\nRDATE:20260727T160040\nRRULE:FREQ=WEEKLY;INTERVAL=1;BYDAY=WE", "desc": "", "url": ""},
  {"id": 439, "title": "Rec Swim Movie at the Pool", "start": "2026-10-03T13:00:00", "end": "2026-10-03T15:00:00", "duration": "02:00",
   "calendar_displays": ["6", "5", "8"], "location": "Moana Comp Pool",
   "rrule": "DTSTART:20261003T130000\nRDATE:20261003T130000\nRRULE:FREQ=WEEKLY;INTERVAL=1;BYDAY=SU,SA;UNTIL=20261102T000000\nEXDATE:20261010T130000",
   "desc": "", "url": ""},
  {"id": 390, "title": "Pool Closure - Northwest Pool", "start": "2026-10-06T00:00:00", "allDay": true,
   "calendar_displays": ["6", "7", "5"], "location": "Northwest Pool", "desc": "", "url": ""},
  {"id": 900, "title": "Biggest Little Ultra", "start": "2026-10-09T00:00:00", "end": "2026-10-12T00:00:00",
   "calendar_displays": ["1"], "location": "Sparks Marina Parkhttps://www.biggestlittleultra.com/", "desc": "", "url": ""}
]
```

- [ ] **Step 6: Write the failing tests** `tests/test_revize.py`

```python
import unittest
from datetime import date
from unittest import mock

from helpers import fixture_json, la
import net
from sources.base import Context, SourceError
from sources.revize import RevizeSource

RENO = RevizeSource("reno", "City of Reno", "www.reno.gov", "renonv", city="Reno",
                    page_url="https://www.reno.gov/", skip_calendars={"3"}, kid_calendars={"8"},
                    calendar_names={"5": "parks & rec", "8": "youth", "9": "special events"})


class RevizeTest(unittest.TestCase):
    def setUp(self):
        self.events = RENO.parse(fixture_json("revize.json"), date(2026, 10, 5), date(2026, 10, 12))
        self.by_title = {}
        for e in self.events:
            self.by_title.setdefault(e["title"], []).append(e)

    def test_meetings_cancellations_and_closures_are_dropped(self):
        self.assertEqual(sorted(self.by_title), ["44th Annual Great Italian Festival", "Biggest Little Ultra",
                                                 "Food Truck Wednesdays", "Ranger Walks", "Rec Swim Movie at the Pool"])

    def test_one_off_event(self):
        [e] = self.by_title["Ranger Walks"]
        self.assertEqual((e["start"], e["end"]), ("2026-10-10T14:00:00-07:00", "2026-10-10T15:00:00-07:00"))
        self.assertTrue(e["_family"])
        self.assertIn("youth", e["_tags"])
        self.assertEqual(e["_text"], "Guided walk for families")
        self.assertEqual(e["venue"]["name"], "Fisherman's Park")
        self.assertEqual(e["links"][0]["url"], "https://www.reno.gov/")

    def test_recurrences_expand_within_the_window(self):
        self.assertEqual([e["start"] for e in self.by_title["44th Annual Great Italian Festival"]],
                         ["2026-10-10T10:00:00-07:00", "2026-10-11T10:00:00-07:00"])
        self.assertEqual([e["end"] for e in self.by_title["44th Annual Great Italian Festival"]],
                         ["2026-10-10T20:00:00-07:00", "2026-10-11T20:00:00-07:00"])
        self.assertEqual([e["start"] for e in self.by_title["Food Truck Wednesdays"]], ["2026-10-07T16:00:00-07:00"])
        self.assertEqual([e["start"] for e in self.by_title["Rec Swim Movie at the Pool"]], ["2026-10-11T13:00:00-07:00"])
        ids = [e["id"] for e in self.by_title["44th Annual Great Italian Festival"]]
        self.assertEqual(ids, ["reno:285-202610101000", "reno:285-202610111000"])

    def test_multi_day_all_day_event_and_url_in_location(self):
        [e] = self.by_title["Biggest Little Ultra"]
        self.assertTrue(e["allDay"])
        self.assertEqual((e["start"], e["end"]), ("2026-10-09T00:00:00-07:00", "2026-10-11T00:00:00-07:00"))
        self.assertEqual(e["venue"]["name"], "Sparks Marina Park")
        self.assertEqual(e["links"][0]["url"], "https://www.biggestlittleultra.com/")

    def test_fetch_checks_the_shape(self):
        ctx = Context(la(2026, 10, 5), la(2026, 10, 13))
        with mock.patch.object(net, "get_json", lambda url, **kw: fixture_json("revize.json")):
            self.assertEqual(len(RENO.fetch(ctx)), len(self.events))
        with mock.patch.object(net, "get_json", lambda url, **kw: {"error": "x"}):
            with self.assertRaises(SourceError):
                RENO.fetch(ctx)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 7: Run them to make sure they fail**

Run: `python3 -m unittest discover -s tests -v`
Expected: `ModuleNotFoundError: No module named 'sources.revize'`

- [ ] **Step 8: Implement** `collector/sources/revize.py`

```python
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
```

Add the instances to `collector/sources/__init__.py` (and to `ALL`, after `DISCOVERY`). Before committing, check `page_url` for each city with `curl -sI` and use the city's events-calendar page if one exists.
```python
from sources.revize import RevizeSource

CITY_OF_RENO = RevizeSource("reno", "City of Reno", "www.reno.gov", "renonv", city="Reno",
                            page_url="https://www.reno.gov/", skip_calendars={"3"}, kid_calendars={"8"},
                            calendar_names={"4": "events", "5": "parks & rec", "6": "aquatics", "7": "athletics",
                                            "8": "youth", "9": "special events"})
CITY_OF_SPARKS = RevizeSource("sparks", "City of Sparks", "www.sparksnv.gov", "sparksnv", city="Sparks",
                              page_url="https://www.sparksnv.gov/", skip_calendars={"2", "5"},
                              calendar_names={"1": "community events"})
```

- [ ] **Step 9: Run all tests, try both live, commit**

```bash
python3 -m unittest discover -s tests -v
python3 dev/try_source.py reno && python3 dev/try_source.py sparks
git add collector/rrule.py collector/sources/revize.py collector/sources/__init__.py tests/test_rrule.py tests/test_revize.py tests/fixtures/revize.json
git commit -m "City of Reno and Sparks calendars, with recurrence"
git pull --rebase -q && git push
```
Expected:
- All tests pass.
- Reno lists about 20–40 events (Rolling Recreation, Tot Pool and so on) and no meetings.
- Sparks lists a few, or none.

---

### Task 26: Washoe County Regional Parks (Tockify page data)

**Files:**
- Create: `collector/sources/tockify.py`, `tests/test_tockify.py`, `tests/fixtures/tockify.html`
- Modify: `collector/sources/__init__.py`

**Interfaces:**
- Consumes: `net.get_text`, `model.make_event / venue / city_from_address / FREE`, `SourceError`
- Produces: `tockify.parse(page_html) -> list[event]`, `NAME = "wcparks"`

Research on 2026-10-05:
- **The page:** the county parks calendar is the Tockify calendar `wcparks`. Tockify's `robots.txt` **disallows `/api/`**, which rules out its iCal and JSON feeds. `https://tockify.com/wcparks` is **allowed**.
- **The data:** that page embeds its data as `window.tkf = {… "bootdata": {…}}`. Events are under `bootdata.query.upcoming.events` (about 16, from a week back to December) and `bootdata.query.pinboard.events` (overlapping).
- **Fields:**
  - `eid.uid` and `eid.tid`
  - `when.start.millis` (UTC epoch ms), `when.start.offset` (ms), `when.end.millis`, `when.allDay`
  - `content.summary.text`, `content.place`, `content.address`
  - `content.description.text` (plain, cut at 400 characters)
  - `content.tagset.tags.default`, `status.name`
- **Kid events:** Junior Ranger days, Wild Wednesday nature talks and fall festivals.
- **Links:** `https://tockify.com/wcparks/detail/{uid}/{tid}`. We only link to these and never fetch them.

- [ ] **Step 1: Write the fixture** `tests/fixtures/tockify.html`

```html
<!doctype html><html><head><title>Washoe County Parks</title></head><body><div id="app"></div>
<script>window.tkf = {"version":"x","bootdata":{"query":{"upcoming":{"events":[
 {"eid":{"uid":"801","tid":1791651600000},"when":{"start":{"millis":1791651600000,"tzid":"America/Los_Angeles","offset":-25200000},"end":{"millis":1791657000000,"offset":-25200000},"allDay":false},
  "content":{"summary":{"text":"Fall Photo Hike: Slide Mountain Trail"},"place":"Slide Mountain Trailhead","address":"Mt Rose Hwy, Reno, NV 89511","description":{"text":"This is a free event. Bring water."},"tagset":{"tags":{"default":[]}}},"status":{"name":"scheduled"}},
 {"eid":{"uid":"802","tid":1792020600000},"when":{"start":{"millis":1792020600000,"offset":-25200000},"end":{"millis":1792024200000,"offset":-25200000},"allDay":false},
  "content":{"summary":{"text":"Wild Wednesday - Owls, Spiders, and Bats Oh My!"},"place":"Galena Creek Visitor Center","address":"18350 Mt Rose Hwy, Reno, NV 89511","description":{"text":"Kids learn about night animals."},"tagset":{"tags":{"default":["Kids"]}}},"status":{"name":"scheduled"}},
 {"eid":{"uid":"803","tid":1790870400000},"when":{"start":{"millis":1790870400000,"offset":-25200000},"end":{"millis":1793487600000,"offset":-25200000},"allDay":false},
  "content":{"summary":{"text":"Sierra-Nevada Autumn Photo Exhibit at Bartley Ranch Regional Park"},"place":"Bartley Ranch","address":"6000 Bartley Ranch Rd, Reno, NV 89511","description":{"text":"Free parking."},"tagset":{"tags":{"default":[]}}},"status":{"name":"scheduled"}},
 {"eid":{"uid":"804","tid":1791651600000},"when":{"start":{"millis":1791651600000,"offset":-25200000},"allDay":false},
  "content":{"summary":{"text":"Cancelled Hike"},"place":"Somewhere","address":"","description":{"text":""}},"status":{"name":"cancelled"}},
 {"eid":{"uid":"805","tid":1792220400000},"when":{"start":{"millis":1792220400000,"offset":-25200000},"allDay":true},
  "content":{"summary":{"text":"Junior Ranger Adventure Day! (Bowers Mansion Regional Park)"},"place":"Bowers Mansion","address":"4005 US-395, Washoe Valley, NV 89704","description":{"text":""},"tagset":{"tags":{"default":["Festival"]}}},"status":{"name":"scheduled"}}
]},"pinboard":{"events":[
 {"eid":{"uid":"801","tid":1791651600000},"when":{"start":{"millis":1791651600000,"offset":-25200000},"end":{"millis":1791657000000,"offset":-25200000},"allDay":false},
  "content":{"summary":{"text":"Fall Photo Hike: Slide Mountain Trail"},"place":"Slide Mountain Trailhead","address":"Mt Rose Hwy, Reno, NV 89511","description":{"text":"This is a free event."}},"status":{"name":"scheduled"}}
]}}},"other":{"a":1}};</script></body></html>
```

- [ ] **Step 2: Write the failing tests** `tests/test_tockify.py`

```python
import unittest
from unittest import mock

from helpers import fixture_text, la
import net
from sources import tockify
from sources.base import Context, SourceError


class TockifyTest(unittest.TestCase):
    def setUp(self):
        self.by_uid = {e["id"].split(":")[1].split("-")[0]: e for e in tockify.parse(fixture_text("tockify.html"))}

    def test_reads_page_data_once_per_event_and_skips_cancelled(self):
        self.assertEqual(sorted(self.by_uid), ["801", "802", "803", "805"])

    def test_event(self):
        e = self.by_uid["801"]
        self.assertEqual(e["title"], "Fall Photo Hike: Slide Mountain Trail")
        self.assertEqual((e["start"], e["end"]), ("2026-10-10T10:00:00-07:00", "2026-10-10T11:30:00-07:00"))
        self.assertEqual(e["price"], {"free": True})
        self.assertEqual(e["venue"]["name"], "Slide Mountain Trailhead")
        self.assertEqual(e["links"][0]["url"], "https://tockify.com/wcparks/detail/801/1791651600000")

    def test_free_parking_is_not_a_free_event_and_month_long_is_ongoing(self):
        e = self.by_uid["803"]
        self.assertIsNone(e["price"])
        self.assertTrue(e["ongoing"])

    def test_all_day_uses_the_local_date_and_washoe_valley_is_nearby(self):
        e = self.by_uid["805"]
        self.assertTrue(e["allDay"])
        self.assertEqual(e["start"], "2026-10-17T00:00:00-07:00")
        self.assertEqual((e["area"], e["drive"]), ("other", "~25 min"))

    def test_page_without_data_is_a_source_error(self):
        with self.assertRaises(SourceError):
            tockify.parse("<html>new design</html>")
        with mock.patch.object(net, "get_text", lambda url, **kw: "<html>x</html>"):
            with self.assertRaises(SourceError):
                tockify.fetch(Context(la(2026, 10, 5), la(2026, 10, 13)))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run them to make sure they fail**

Run: `python3 -m unittest discover -s tests -v`
Expected: `ImportError: cannot import name 'tockify'`

- [ ] **Step 4: Implement** `collector/sources/tockify.py`, and add `tockify` to `ALL`

```python
"""Washoe County Regional Parks events: the Tockify calendar page's embedded
data (tockify.com/wcparks). Tockify's robots.txt rules out its /api/ feeds but
allows this page; we read it once per refresh and only ever link to event pages."""

import json
import re
from datetime import datetime, timezone

import net
from model import FREE, city_from_address, make_event, venue
from sources.base import SourceError

NAME = "wcparks"
LABEL = "Washoe County Parks"
URL = "https://tockify.com/wcparks"
MARKER = '"bootdata":'
FREE_EVENT = re.compile(r"\bfree (event|admission|entry|program)\b|\(free event\)", re.I)


def fetch(ctx):
    return parse(net.get_text(URL))


def _when(part):
    return datetime.fromtimestamp(part["millis"] / 1000, tz=timezone.utc)


def parse(page):
    at = page.find(MARKER)
    if at < 0:
        raise SourceError("no calendar data in the page (did Tockify change its page?)")
    try:
        boot, _ = json.JSONDecoder().raw_decode(page[at + len(MARKER):])
    except ValueError:
        raise SourceError("the calendar data didn't parse") from None
    query = boot.get("query") or {}
    seen, events = set(), []
    for bucket in ("upcoming", "pinboard"):
        for e in (query.get(bucket) or {}).get("events") or []:
            eid = e.get("eid") or {}
            key = (eid.get("uid"), eid.get("tid"))
            if key in seen or ((e.get("status") or {}).get("name") or "").lower() in ("cancelled", "canceled"):
                continue
            seen.add(key)
            when, c = e.get("when") or {}, e.get("content") or {}
            try:
                start = _when(when["start"])
                end = _when(when["end"]) if (when.get("end") or {}).get("millis") else None
            except (KeyError, TypeError, ValueError):
                continue
            all_day = bool(when.get("allDay"))
            if all_day:
                local_ms = when["start"]["millis"] + (when["start"].get("offset") or 0)
                start = datetime.fromtimestamp(local_ms / 1000, tz=timezone.utc).date()
                end = None
            title = " ".join(((c.get("summary") or {}).get("text") or "").split())
            text = (c.get("description") or {}).get("text") or ""
            address = c.get("address") or ""
            events.append(make_event(
                "wcparks", f"{eid.get('uid')}-{eid.get('tid')}", title, start, end=end, all_day=all_day,
                venue=venue(c.get("place"), address), city=city_from_address(address, "Reno"),
                price=dict(FREE) if FREE_EVENT.search(f"{title} {text}") else None,
                url=f"https://tockify.com/wcparks/detail/{eid.get('uid')}/{eid.get('tid')}",
                text=text, tags=((c.get("tagset") or {}).get("tags") or {}).get("default") or [],
                kind="organiser"))
    return events
```

- [ ] **Step 5: Run the tests, try it live, commit**

```bash
python3 -m unittest discover -s tests -v
python3 dev/try_source.py wcparks
git add collector/sources/tockify.py collector/sources/__init__.py tests/test_tockify.py tests/fixtures/tockify.html
git commit -m "Washoe County Parks events from the Tockify calendar page"
git pull --rebase -q && git push
```
Expected:
- All tests pass.
- Live, there are 0–5 events in the next 8 days. It's low volume, so 0 can be normal.
- If live parsing fails with "no calendar data", Tockify changed its page. Check `python3 -c "import sys; sys.path.insert(0,'collector'); import net; t=net.get_text('https://tockify.com/wcparks'); print(t.find('bootdata'))"`. Don't look for a way around the robots rule.

---

### Task 27: Standing events (`standing.json`): Riverside Farmers Market and Hands ON! Second Saturday

**Files:**
- Create: `standing.json`, `collector/sources/standing.py`, `tests/test_standing.py`
- Modify: `collector/sources/__init__.py`

**Interfaces:**
- Consumes: `model.make_event / venue / FREE / LA`, `SourceError`
- Produces:
  - `standing.occurrences(entries, first, last) -> list[event]`
  - `standing.PATH` (the repo-root `standing.json`; tests replace it)
  - `NAME = "standing"`, `LABEL = "Weekly regulars"`

These are regular events with no feed:
- **Riverside Farmers Market:** every Sunday at Idlewild Park, all year. The market's own site says "9am–1pm (time changes seasonally)".
- **Nevada Museum of Art's free "Hands ON! Second Saturday":** a family day on the second Saturday of every month. The museum doesn't list a time, so it's all-day.

The page links each one to its own site.

- [ ] **Step 1: Write** `standing.json`

```json
[
  {"id": "riverside-farmers-market", "title": "Riverside Farmers Market", "weekday": "sun", "start": "09:00", "end": "13:00",
   "months": null, "venue": "Idlewild Park", "address": "2055 Idlewild Dr, Reno, NV 89509", "city": "Reno",
   "url": "https://www.renofarmersmarket.com/", "free": true, "allAges": true, "outdoor": true},
  {"id": "nma-hands-on", "title": "Hands ON! Second Saturday (free museum day)", "weekday": "sat", "nth": 2, "allDay": true,
   "months": null, "venue": "Nevada Museum of Art", "address": "160 W Liberty St, Reno, NV 89501", "city": "Reno",
   "url": "https://www.nevadaart.org/", "free": true, "family": true}
]
```

- [ ] **Step 2: Write the failing tests** `tests/test_standing.py`

```python
import json
import os
import tempfile
import unittest
from datetime import date
from unittest import mock

from helpers import ROOT, la
from sources import standing
from sources.base import Context, SourceError


class StandingTest(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(ROOT, "standing.json"), encoding="utf-8") as f:
            self.entries = json.load(f)

    def test_weekly_and_nth_weekday(self):
        events = standing.occurrences(self.entries, date(2026, 10, 5), date(2026, 10, 12))
        self.assertEqual([(e["title"][:12], e["start"]) for e in events],
                         [("Riverside Fa", "2026-10-11T09:00:00-07:00"), ("Hands ON! Se", "2026-10-10T00:00:00-07:00")])
        market = events[0]
        self.assertEqual(market["end"], "2026-10-11T13:00:00-07:00")
        self.assertEqual(market["price"], {"free": True})
        self.assertTrue(market["_outdoor"] and market["_allAges"])
        self.assertEqual(market["id"], "standing:riverside-farmers-market-2026-10-11")
        self.assertTrue(events[1]["allDay"] and events[1]["_family"])

    def test_second_saturday_in_november(self):
        events = standing.occurrences(self.entries[1:], date(2026, 11, 1), date(2026, 11, 30))
        self.assertEqual([e["start"][:10] for e in events], ["2026-11-14"])

    def test_months_limit(self):
        summer = [dict(self.entries[0], months=[6, 7, 8])]
        self.assertEqual(standing.occurrences(summer, date(2026, 10, 1), date(2026, 10, 31)), [])

    def test_broken_file_is_a_source_error_and_missing_file_is_empty(self):
        ctx = Context(la(2026, 10, 5), la(2026, 10, 13))
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "standing.json")
            with mock.patch.object(standing, "PATH", path):
                self.assertEqual(standing.fetch(ctx), [])
                with open(path, "w") as f:
                    f.write("[{broken")
                with self.assertRaises(SourceError):
                    standing.fetch(ctx)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run them to make sure they fail**

Run: `python3 -m unittest discover -s tests -v`
Expected: `ImportError: cannot import name 'standing'`

- [ ] **Step 4: Implement** `collector/sources/standing.py`, and add `standing` to `ALL`

```python
"""Standing events kept by hand in standing.json: regular things with no feed.
Each entry: id, title, weekday (mon…sun), optional nth (2 = second of the month),
start/end ("HH:MM") or allDay, optional months, venue, address, city, url and the
flags free / family / allAges / outdoor."""

import json
import os
from datetime import datetime, timedelta

from model import FREE, LA, make_event, venue
from sources.base import SourceError

NAME = "standing"
LABEL = "Weekly regulars"
PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "standing.json")
WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def fetch(ctx):
    try:
        with open(PATH, encoding="utf-8") as f:
            entries = json.load(f)
    except FileNotFoundError:
        return []
    except ValueError as err:
        raise SourceError(f"standing.json is broken: {err}") from None
    return occurrences(entries, ctx.start.date(), (ctx.end - timedelta(days=1)).date())


def _on(entry, day):
    if WEEKDAYS[day.weekday()] != entry.get("weekday"):
        return False
    if entry.get("months") and day.month not in entry["months"]:
        return False
    return not entry.get("nth") or (day.day - 1) // 7 + 1 == entry["nth"]


def _at(day, hhmm):
    h, m = (int(x) for x in hhmm.split(":"))
    return datetime(day.year, day.month, day.day, h, m, tzinfo=LA)


def occurrences(entries, first, last):
    events = []
    for entry in entries:
        day = first
        while day <= last:
            if _on(entry, day):
                all_day = bool(entry.get("allDay"))
                start = day if all_day else _at(day, entry["start"])
                end = None if all_day or not entry.get("end") else _at(day, entry["end"])
                events.append(make_event(
                    "standing", f"{entry['id']}-{day.isoformat()}", entry["title"], start, end=end, all_day=all_day,
                    venue=venue(entry.get("venue"), entry.get("address")), city=entry.get("city"),
                    price=dict(FREE) if entry.get("free") else None, url=entry.get("url"),
                    family=bool(entry.get("family")), all_ages=bool(entry.get("allAges")),
                    outdoor=bool(entry.get("outdoor")), kind="organiser"))
            day += timedelta(days=1)
    return events
```

- [ ] **Step 5: Run all tests, run the collector locally, commit**

```bash
python3 -m unittest discover -s tests -v
rm -f state/refresh.json       # force a refresh; the git checkout below restores it
python3 collector/collect.py && python3 -c "import json; s=json.load(open('docs/data/status.json'))['sources']; print({k:(v['ok'],v['count']) for k,v in s.items()})"
git checkout -- docs/data state 2>/dev/null; git clean -fdq docs/data state
git add standing.json collector/sources/standing.py collector/sources/__init__.py tests/test_standing.py
git commit -m "Standing events: Riverside Farmers Market and Hands ON! Second Saturday"
git pull --rebase -q && git push
```
Expected:
- Every phase 2 source shows `ok` with a count. `library` takes about 80 s; that's its crawl delay.
- The local run's data files are discarded (Actions commits the real ones).
- Afterwards, trigger one live run (`gh workflow run collect.yml --repo natanforestree/reno-today`) and look at the page at 390 px. Little-ones sections should now be well filled on weekdays.

---

# Phase 3: Polish

### Task 28: Loving Reno pick badges

**Files:**
- Modify: `collector/guide.py` (add `norm`, `page_text`, `badges`), `collector/collect.py` (`run` fetches the card before writing events and applies badges), `tests/test_guide.py`, `tests/test_collect.py`

**Interfaces:**
- Consumes:
  - `dedupe.tokens(text) -> set` (Task 5)
  - finalized event dicts (`lovingReno` is `None` by default)
  - the guide card `{title, shortTitle, url, published}`
- Produces:
  - `guide.norm(text) -> " words … "` (lower-case alphanumeric words, with years, ordinals, "annual" and "the" removed, padded with spaces)
  - `guide.page_text(html) -> str`
  - `guide.badges(events, card, text) -> int` (sets `event["lovingReno"] = {"title", "url"}` in place)

The spec: "For each event with a distinctive title (≥ 3 significant words, or a title plus venue match), set `lovingReno` when the guide's text contains it. Only the guide's title and URL are stored." The guide's HTML is fetched once per full refresh (`robots.txt` allows it). Nothing from it is stored except that match.

- [ ] **Step 1: Write the failing tests.** Add to `tests/test_guide.py`: put the two imports with the file's other imports at the top, and the rest above the `if __name__ == "__main__":` block:

```python
import model
from helpers import la


def fin(title, venue_name=None):
    e = model.make_event("x", title, title, la(2026, 10, 10, 10), city="Reno",
                         venue=model.venue(venue_name, "Reno, NV") if venue_name else None)
    return model.finalize(e)


GUIDE_HTML = """<html><head><style>.x{}</style><script>var t = "Great Italian Festival";</script></head><body>
<h2>Fall Festivals</h2><p>Don't miss the <b>44th Annual Great Italian Festival</b> downtown.</p>
<p>The Pumpkin Patch at Andelin Family Farm is great for kids.</p>
<p>Trick or Treat at the Sparks Marina is a local favorite.</p></body></html>"""
CARD = {"title": "2026 Ultimate Reno Halloween & Fall Guide: More", "shortTitle": "2026 Ultimate Reno Halloween & Fall Guide",
        "url": "https://www.lovingreno.com/2026/09/guide.html", "published": "2026-09-24"}


class BadgesTest(unittest.TestCase):
    def test_norm(self):
        self.assertEqual(guide.norm("The 44th Annual Great Italian Festival!"), " great italian festival ")
        self.assertEqual(guide.norm("Kids&#8217; Day"), " kids day ")

    def test_page_text_drops_scripts_and_styles(self):
        text = guide.page_text(GUIDE_HTML)
        self.assertNotIn("var t", text)
        self.assertIn(" great italian festival ", text)

    def test_badges(self):
        events = [fin("Great Italian Festival"),                       # 3 words, in the guide
                  fin("Pumpkin Patch", "Andelin Family Farm"),         # 2 words + venue nearby
                  fin("Pumpkin Patch", "Lattin Farms"),                # 2 words, venue not mentioned
                  fin("Storytime"),                                     # 1 word: never
                  fin("Fall Festivals"),                                # 2 words, no venue
                  fin("Trick or Treat at the Sparks Marina"),
                  fin("Wind Ensemble Concert")]                         # not in the guide
        n = guide.badges(events, CARD, guide.page_text(GUIDE_HTML))
        self.assertEqual([bool(e["lovingReno"]) for e in events], [True, True, False, False, False, True, False])
        self.assertEqual(n, 3)
        self.assertEqual(events[0]["lovingReno"], {"title": "2026 Ultimate Reno Halloween & Fall Guide",
                                                   "url": "https://www.lovingreno.com/2026/09/guide.html"})
```

Append to `tests/test_collect.py` (inside `CollectTest`):

```python
    def test_loving_reno_badges_are_applied_before_writing(self):
        page = "<p>Join the Baby Storytime at Sparks Library every week.</p>"
        with mock.patch.object(net, "get_text", lambda url, **kw: page):
            collect.run(self.root, NOW, {}, srcs=[fake_source("lib", [storytime()])])
        [e] = self.read("docs/data/events.json")["events"]
        self.assertEqual(e["lovingReno"], {"title": "Fall Guide", "url": "https://www.lovingreno.com/g.html"})

    def test_guide_page_failure_does_not_stop_the_run(self):
        with mock.patch.object(net, "get_text", mock.Mock(side_effect=net.FetchError("x", "HTTP 500", 500))):
            collect.run(self.root, NOW, {}, srcs=[fake_source("lib", [storytime()])])
        self.assertIsNone(self.read("docs/data/events.json")["events"][0]["lovingReno"])

    def test_loving_reno_alone_does_not_count_as_a_working_source(self):
        collect.run(self.root, NOW, {}, srcs=[fake_source("lib", [storytime()])])
        before = self.read("docs/data/events.json")
        with mock.patch.object(net, "get_text", lambda url, **kw: ""):
            collect.run(self.root, NOW + timedelta(days=2), {}, srcs=[fake_source("lib", error=SourceError("down"))])
        self.assertEqual(self.read("docs/data/events.json"), before)
```

Also add `mock.patch.object(net, "get_text", lambda url, **kw: "")` to the `self.patches` list in `CollectTest.setUp`, so no test reaches the real site. The two tests above override it.

- [ ] **Step 2: Run them to make sure they fail**

Run: `python3 -m unittest discover -s tests -v`
Expected: `AttributeError: module 'guide' has no attribute 'norm'`, and the collect test finds `lovingReno` is `None`

- [ ] **Step 3: Implement.** In `collector/guide.py`, add `import html` and `import re` at the top, `from dedupe import tokens`, and then:

```python
DROP = re.compile(r"\b((19|20)\d\d|\d+(st|nd|rd|th)|annual|the)\b")
NEAR = 300   # characters either side of a two-word title where the venue must appear


def norm(text):
    """Lower-case words only, padded with spaces: ' great italian festival '."""
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or "")).lower().replace("'", "").replace("’", "")
    return " " + " ".join(re.sub(r"[^a-z0-9]+", " ", DROP.sub(" ", text)).split()) + " "


def page_text(page_html):
    return norm(re.sub(r"(?is)<(script|style)\b[^>]*>.*?</\1>", " ", page_html or ""))


def badges(events, card, text):
    """Mark events the guide mentions. Distinctive titles only: 3+ significant words
    found as a phrase, or 2 words with the venue's name close by."""
    mark = {"title": card.get("shortTitle") or card["title"], "url": card["url"]}
    marked = 0
    for e in events:
        phrase = norm(e["title"]).strip()
        words = tokens(e["title"])
        if len(words) < 2 or not phrase:
            continue
        at = text.find(f" {phrase} ")
        if at < 0:
            continue
        place = norm((e.get("venue") or {}).get("name")).strip()
        if len(words) >= 3 or (place and f" {place} " in text[max(0, at - NEAR):at + len(phrase) + NEAR]):
            e["lovingReno"] = dict(mark)
            marked += 1
    return marked
```

In `collector/collect.py`, replace the whole `run()` function with this version. The guide card is now fetched before `events.json` is written, the badges are applied, and "did any source work?" is decided **before** the Loving Reno and weather entries join `status`:

```python
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
        except net.FetchError as err:
            print(f"lovingreno: badges skipped ({err})")

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
        day_wx = next((d for d in (wx or {}).get("days", []) if d.get("date") == today), None)
        text = digest.build(today, events, day_wx, places, card)
        if (post or digest.post)(webhook, text):
            store.set_digest_date(today)
            print("digest sent")
        else:
            print("digest not sent; the next hourly run will try again (until 10:59)")
    return decision
```

- [ ] **Step 4: Run all tests**

Run: `python3 -m unittest discover -s tests -v`
Expected: all OK

- [ ] **Step 5: Check against the real guide**

```bash
python3 - <<'EOF'
import sys; sys.path.insert(0, "collector")
import json, guide, net
card = guide.fetch()
text = guide.page_text(net.get_text(card["url"]))
events = json.load(open("docs/data/events.json"))["events"] if __import__("os").path.exists("docs/data/events.json") else []
print(card["shortTitle"], len(text), "chars;", guide.badges(events, card, text), "picks")
print([e["title"] for e in events if e.get("lovingReno")][:20])
EOF
```
Run `git pull` first, so `docs/data/events.json` is the live data. Expected: a handful of picks that really are in the guide. If generic titles slip through (e.g. "Trick or Treat"), raise the bar for that case in `badges` and add the title to the tests.

- [ ] **Step 6: Commit and push**

```bash
git add collector/guide.py collector/collect.py tests/test_guide.py tests/test_collect.py
git commit -m "Loving Reno pick badges on events their current guide mentions"
git pull --rebase -q && git push
```

---

### Task 29: The Reno Arch island (in `arcadipelago`)

**Files** (in `~/Documents/code/games`):
- Create: `art/site/island-reno-today.lua`; it writes `art/site/island-reno-today.aseprite`, `site/assets/island-reno-today.png` and `site/assets/island-reno-today.json`
- Modify: `art/site/palette.lua` (add `renoToday` colours and `glow["reno-today"]`)

**Interfaces:**
- Consumes:
  - `art/site/lib.lua`:
    - `L.buffer`, `L.set`, `L.get`, `L.fillRect`, `L.disc`
    - `L.outline(b, color)` (it outlines around **any** painted pixel, so outline before adding translucent glow)
    - `L.blit`
  - `art/site/island.lua`: `I.write(id, frames, ms, glowColor)` (asserts a 3 px empty margin and computes `hit`)
- Produces: a 12-frame island, **88×84 frames**, 160 ms, with **hit exactly 80 wide and ≤ 72 tall**. Task 30's layout depends on that size: 7 islands only fit the landscape stage if this island is at most 80 px wide (2026-10-05 layout study), and Task 30 makes 80 the minimum game-island width.

The island: a chunk of Virginia Street on warm desert stone, with the Reno Arch over it:
- steel pillars
- the starburst on top
- tiny neon **RENO** (it flickers on frame 7)
- the red banner
- bulbs chasing round the arch
- a street lamp at each end

This is a first version. Refine it to match the other islands' finish (light from the top-left, dithered stone, details hanging under the rock), and keep within the size limits.

- [ ] **Step 1: Add the palette.** In `art/site/palette.lua`:
- Add `["reno-today"] = "#ff6fb5"` to the `glow` table.
- Add this table after `rubyRadar`:

```lua
  -- Reno Today (a website): from reno-today's art/lib.lua palette, plus warm desert stone.
  renoToday = {
    outline = "#1b1420",
    rock = { "#2b2230", "#3d3042", "#5a4658", "#7a6170" },   -- dark -> light
    grass = { "#4f6b48", "#6f8f64", "#93b58c" },             -- sage
    road = { "#2a2a33", "#3b3b46" }, paint = "#f6ecd9",
    steel = { "#666c82", "#a3a9bb", "#d9dce6" },
    gold = { "#c7902e", "#ffd36b", "#fff1c2" }, bulbOff = "#6e5634",
    neon = { "#a8466f", "#ff5fa2", "#ffd6ea" }, glow = "#ff3b5566",
    red = { "#8f1b2b", "#d42a3a", "#ec5562" },
    lamp = "#ffe08a",
  },
```

- [ ] **Step 2: Write** `art/site/island-reno-today.lua`

```lua
-- The Reno Today island for the games page (it links to Reno Today, Nathan's page of what's on in Reno each
-- day, a website rather than a game). A chunk of Virginia Street floats on warm desert stone under the Reno
-- Arch: steel pillars, the starburst on top, RENO in pink neon (it flickers on one frame), the red Biggest
-- Little City banner and bulbs chasing round the arch, with a street lamp at each end of the street.
-- Kept narrow (hit <= 80 px) so seven islands fit the landscape stage. Run from the repo root:
--   /Applications/Aseprite.app/Contents/MacOS/aseprite -b --script art/site/island-reno-today.lua
local here = debug.getinfo(1, "S").source:sub(2):match("^(.-)[^/]+$") or ""
local L = dofile(here .. "lib.lua")
local P = dofile(here .. "palette.lua")
local I = dofile(here .. "island.lua")
local W, H, N, MS = 88, 84, 12, 160
local C = P.renoToday

local function ell(x, y, cx, cy, rx, ry)
  local dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
  return dx * dx + dy * dy <= 1
end

local function copy(b)
  local c = L.buffer(b.w, b.h)
  for y = 0, b.h - 1 do for x = 0, b.w - 1 do c[y][x] = b[y][x] end end
  return c
end

local GLYPHS = {   -- RENO in a 3x5 font
  R = { "##.", "#.#", "##.", "#.#", "#.#" }, E = { "###", "#..", "##.", "#..", "###" },
  N = { "#.#", "###", "###", "#.#", "#.#" }, O = { ".#.", "#.#", "#.#", "#.#", ".#." },
}

-- Arch geometry: a ring between two ellipses centred on (44, 34), top half only.
local AX, AY, ORX, ORY, IRX, IRY = 44, 34, 26, 17, 22, 13

local function scenery()
  local b = L.buffer(W, H)
  -- the underside, narrowing to a tip; lit from the left
  for y = 56, 77 do
    local half = math.floor(36 * (1 - (y - 56) / 22) ^ 1.3 + 0.5)
    for x = 44 - half, 44 + half do
      local c = C.rock[2]
      if x < 44 - half * 0.45 then c = C.rock[3] elseif x > 44 + half * 0.55 then c = C.rock[1] end
      if (x + y * 3) % 9 == 0 then c = C.rock[1] end
      L.set(b, x, y, c)
    end
  end
  -- the top: a sage verge with Virginia Street across it, and the rim's front edge
  for y = 44, 62 do
    for x = 4, 84 do
      if ell(x, y, 44, 53, 39, 8) then
        local c = (y <= 47) and C.grass[3] or C.grass[2]
        if y >= 50 and y <= 55 then c = (y == 50) and C.road[2] or C.road[1] end
        if y == 52 and x % 6 < 3 and x > 12 and x < 76 then c = C.paint end
        if y >= 58 then c = C.rock[3] end
        L.set(b, x, y, c)
      end
    end
  end
  -- street lamps at both ends
  for _, lx in ipairs({ 9, 79 }) do
    for y = 40, 49 do L.set(b, lx, y, C.steel[1]) end
    L.fillRect(b, lx - 1, 38, lx + 1, 39, C.lamp)
  end
  -- the starburst (the band covers its lower rays)
  for k = 0, 7 do
    local a = math.rad(k * 45)
    for r = 2, (k % 2 == 0) and 5 or 3 do
      L.set(b, math.floor(AX + r * math.cos(a) + 0.5), math.floor(13 - r * math.sin(a) + 0.5), C.steel[3])
    end
  end
  L.disc(b, AX, 13, 2, C.gold[2])
  -- pillars on the far kerb
  for y = 30, 50 do
    for x = 18, 21 do L.set(b, x, y, (x == 18) and C.steel[3] or (x == 21) and C.steel[1] or C.steel[2]) end
    for x = 66, 69 do L.set(b, x, y, (x == 66) and C.steel[3] or (x == 69) and C.steel[1] or C.steel[2]) end
  end
  -- the arch band, lit along its top
  for y = AY - ORY, AY do
    for x = AX - ORX, AX + ORX do
      if ell(x, y, AX, AY, ORX, ORY) and not ell(x, y, AX, AY, IRX, IRY) then
        L.set(b, x, y, ell(x, y - 1, AX, AY, ORX, ORY) and C.steel[2] or C.steel[3])
      end
    end
  end
  -- the banner under the arch, its lettering abstracted to dots at this size
  L.fillRect(b, 22, 35, 65, 37, C.red[2])
  L.fillRect(b, 22, 35, 65, 35, C.red[3])
  for x = 24, 63, 2 do L.set(b, x, 36, C.paint) end
  return b
end

-- Bulbs along the middle of the band, left foot to right foot.
local BULBS = {}
for i = 0, 17 do
  local t = math.rad(170 - i * (160 / 17))
  BULBS[#BULBS + 1] = { math.floor(AX + 24 * math.cos(t) + 0.5), math.floor(AY - 15 * math.sin(t) + 0.5) }
end

local base = scenery()
local frames = {}
for f = 1, N do
  local b = copy(base)
  for i, p in ipairs(BULBS) do L.set(b, p[1], p[2], ((i - f) % 3 ~= 0) and C.gold[2] or C.bulbOff) end
  L.outline(b, C.outline)
  -- RENO goes on after the outline so its translucent glow isn't outlined
  local tube = (f == 7) and C.neon[1] or C.neon[2]
  local x0, y0 = 37, 24
  local neon = L.buffer(W, H)
  for li, ch in ipairs({ "R", "E", "N", "O" }) do
    for gy = 1, 5 do
      for gx = 1, 3 do
        if GLYPHS[ch][gy]:sub(gx, gx) == "#" then L.set(neon, x0 + (li - 1) * 4 + gx - 1, y0 + gy - 1, tube) end
      end
    end
  end
  if f ~= 7 then
    for y = y0 - 1, y0 + 5 do
      for x = x0 - 1, x0 + 15 do
        if not neon[y][x] and (L.get(neon, x - 1, y) or L.get(neon, x + 1, y) or L.get(neon, x, y - 1) or L.get(neon, x, y + 1)) then
          neon[y][x] = C.glow
        end
      end
    end
  end
  L.blit(b, neon, 0, 0)
  frames[f] = b
end
I.write("reno-today", frames, MS, P.glow["reno-today"])
```

In the glow loop, `neon[y][x]` reads a row of the buffer; rows run from 0 to H−1 and all of the loop's rows are inside, so this is safe.

- [ ] **Step 3: Render, check the size, look at it**

```bash
cd ~/Documents/code/games
/Applications/Aseprite.app/Contents/MacOS/aseprite -b --script art/site/island-reno-today.lua
cat site/assets/island-reno-today.json
```
Expected:
- It prints `island reno-today: 12 frames of 88x84, 160 ms; hit X,Y WxH` with **W = 80 and H ≤ 72** (expected: hit `4,7 80x72`).
- There's no margin assertion.

Then view `site/assets/island-reno-today.png` (top row: frames; bottom row: hover glow) and `art/site/preview-island-reno-today.gif`. Refine until it sits well beside the other islands:
- the arch reads at a glance
- RENO is legible
- the bulbs chase
- the stone matches the others' lighting

Re-run after each change. The hit must stay exactly 80 wide and at most 72 tall: if it grows, pull the rock edges in; if it shrinks below 80, widen the rim ellipse.

- [ ] **Step 4: Commit (in the games repo; don't push until Task 30)**

```bash
git add art/site/island-reno-today.lua art/site/island-reno-today.aseprite art/site/palette.lua site/assets/island-reno-today.png site/assets/island-reno-today.json
git commit -m "Reno Today island: the Reno Arch over Virginia Street"
```

---

### Task 30: Arcadipelago with seven islands

**Files** (in `~/Documents/code/games`):
- Modify:
  - `site/games.json` (new positions and the `reno-today` entry)
  - `site/islands.js` (`WIDTHS.game` becomes `[80, 140]`)
  - `site/test/islands.test.js` (the expected message `80–140`)
  - `site/layout.js` (the landscape moon goes to `[364, 14]`)
  - `art/site/style-test.lua` (the `ISLANDS` landscape spots and `MOON`)
  - `index.html` (the Reno Today link after Rowan)
  - `README.md` ("Keep it 80–140 px wide")

**Interfaces:**
- Consumes: Task 29's `site/assets/island-reno-today.json` (`hit = [hx, hy, hw, hh]`).
- Produces: the live front page at `https://natanforestree.github.io/arcadipelago/` with seven islands; Reno Today links to `https://natanforestree.github.io/reno-today/`.

**Why the rule changes** (2026-10-05 layout study, checked by exhaustive search and a constraint solver):
- At 97 px or more wide, seven padded island boxes can't fit the 384×216 landscape stage at all.
- Making Reno ≤ 80 px wide and lowering the game minimum width from 96 to 80 fits, moving the existing islands only 97 px in total.
- The portrait layout fits either way.
- The moon moves because Marrow's new spot covers it.

**This changes one of the site's layout rules.** Nathan approved the 7-island re-layout in the spec; mention the 96 → 80 change in the summary to him.

- [ ] **Step 1: Change the width rule and its test message**
- `site/islands.js`: `const WIDTHS = { game: [80, 140], unfinished: [48, 80] };`
- `site/test/islands.test.js`: change the text `it should be 96–140` to `it should be 80–140` (it sits inside a longer message string; match it without quotes)
- `README.md`, "Adding a game" step 3: "Keep it 96–140 px wide" becomes "Keep it 80–140 px wide"

- [ ] **Step 2: Work out Reno's spots from its real hit box, and write `site/games.json`**

Read `hit = [hx, hy, hw, hh]` from `site/assets/island-reno-today.json`. Reno's spots are:
- landscape `[196 - hx, 26 - hy]`
- portrait `[3 - hx, 216 - hy]`

(The study put Reno's hit top-left at (196, 26) in landscape and (3, 216) in portrait.)

```json
{
  "games": [
    { "id": "snake", "island": "island-snake", "at": { "landscape": [-7, 105], "portrait": [-11, 23] }, "bob": { "period": 4200, "phase": 0 } },
    { "id": "marrow", "island": "island-marrow", "at": { "landscape": [266, -4], "portrait": [94, 136] }, "bob": { "period": 5300, "phase": 0.4 } },
    { "id": "last-light", "island": "island-last-light", "at": { "landscape": [124, 113], "portrait": [2, 281] }, "bob": { "period": 4600, "phase": 0.2 } },
    { "id": "open-case", "island": "island-open-case", "at": { "landscape": [263, 124], "portrait": [111, 266] }, "bob": { "period": 3900, "phase": 0.7 } },
    { "id": "ruby-radar", "island": "island-ruby-radar", "at": { "landscape": [93, 41], "portrait": [-3, 130] }, "bob": { "period": 4400, "phase": 0.85 } },
    { "id": "rowan", "island": "island-rowan", "at": { "landscape": [-4, 44], "portrait": [109, 46] }, "bob": { "period": 5000, "phase": 0.55 } },
    { "id": "reno-today", "island": "island-reno-today", "at": { "landscape": [196 - hx, 26 - hy], "portrait": [3 - hx, 216 - hy] }, "bob": { "period": 4800, "phase": 0.3 } }
  ]
}
```
Write the two Reno numbers out (e.g. `[191, 18]`), not the expressions.

- [ ] **Step 3: Move the moon, and update the style test's list**
- `site/layout.js`: in `landscape`, change `moon: [336, 14]` to `moon: [364, 14]`.
- `art/site/style-test.lua`:
  - `MOON` becomes `{ 364, 14 }`.
  - The `ISLANDS` table becomes the landscape spots above, adding `{ "reno-today", <x>, <y> }`.

- [ ] **Step 4: Add the link** in `index.html`, on one line, right after Rowan's `<li>` (the order must match `games.json`):

```html
      <li><a href="https://natanforestree.github.io/reno-today/" data-game="reno-today"><strong>Reno Today</strong> <span class="blurb">What's on in Reno today, little ones first.</span> <span class="controls">Opens Reno Today.</span></a></li>
```

- [ ] **Step 5: Run the tests**

Run: `cd ~/Documents/code/games/site && npm test`
Expected: all pass (70).
- If a test reports an overlap involving `reno-today`, its hit box differs from the study's. Move Reno only, within its free region (landscape: hit x exactly 196 when 80 wide, hit y from 5 to 120 − hh). Re-run.
- If a test says `reno-today: island is N px wide`, fix Task 29's island to exactly 80 px wide; don't change `WIDTHS`. If it can't fit, adjust the island in Task 29 rather than moving the others.

- [ ] **Step 6: Look at it.** Rebuild the style preview, serve the site and screenshot it:

```bash
cd ~/Documents/code/games
/Applications/Aseprite.app/Contents/MacOS/aseprite -b --script art/site/style-test.lua
python3 -m http.server 8001 >/dev/null 2>&1 &
```
With the Playwright tools, take screenshots at:
- `http://localhost:8001/?time=night` and `?time=day`, at 1280×720
- `?time=dusk`, at 390×844

Check:
- Reno sits just right of the title.
- The moon is visible.
- Nothing overlaps.
- Hovering Reno shows its sign.
- Clicking opens Reno Today.

Save the screenshots in the scratchpad to share with Nathan.

- [ ] **Step 7: Commit and push** (Pages redeploys in about a minute)

```bash
git add site/games.json site/islands.js site/test/islands.test.js site/layout.js art/site/style-test.lua index.html README.md
git commit -m "Seven islands: add Reno Today and re-lay out both stages (game min width 80)"
git pull --rebase -q && git push
```
Then open `https://natanforestree.github.io/arcadipelago/` and confirm that the Reno Today island is live.

- [ ] **Step 8: Update the games memory note** `/Users/nathan/.claude/projects/-Users-nathan-Documents-code/memory/games-site-github-pages.md`:
- seven islands, with Reno Today as an island that links out
- game minimum width 80
- landscape moon at [364, 14]

---

### Task 31: Wrap-up

**Files:**
- Modify: `README.md` (sources, how to add a source, maintenance notes)
- Create: `/Users/nathan/.claude/projects/-Users-nathan-Documents-code/memory/reno-today.md`, plus its line in `MEMORY.md`

- [ ] **Step 1: README: sources and maintenance**

````markdown
## Sources

| Source | Module | Notes |
| --- | --- | --- |
| Ticketmaster | `sources/ticketmaster.py` | needs `TICKETMASTER_KEY` |
| UNR events | `sources/unr.py` | Localist API |
| Nevada Wolf Pack | `sources/wolfpack.py` | iCal, home games only |
| Reno Aces | `sources/aces.py` | MLB Stats API; off-season Oct–Mar |
| Washoe County Library | `sources/library.py` | LibCal; 10 s crawl delay, read twice a day |
| The Discovery, Carson City, South Lake Tahoe, Virginia City | `sources/tribe.py` | The Events Calendar REST API |
| City of Reno, City of Sparks | `sources/revize.py` + `rrule.py` | Revize JSON, read twice a day |
| Washoe County Parks | `sources/tockify.py` | Tockify page data (its /api/ is off-limits by robots.txt) |
| Weekly regulars | `sources/standing.py` + `standing.json` | hand-kept |
| Weather | `weather.py` | Open-Meteo |
| Loving Reno | `guide.py` | guide card + "Loving Reno pick" badges; title and link only |

Skipped on purpose: North Lake Tahoe (robots.txt), This Is Reno (blocks programs),
Artown (no feed; July only).

## Adding a source

1. Find a feed (API, iCal, RSS, JSON-LD); check robots.txt.
2. Save a real response, write a small hand-made fixture with the cases that
   matter, and write `tests/test_<name>.py` first.
3. Add `collector/sources/<name>.py` with `NAME`, `LABEL`, `fetch(ctx)` (raise
   `SourceError` on a reshaped response), and add it to `sources.ALL`.
4. `python3 dev/try_source.py <name>`, then run all tests.
5. Add its link label to `SOURCE_LABEL` in `docs/lib.js`.

## Maintenance

- `places.json` hours change with the seasons (county parks switch to 8–5
  after the November time change). Each entry has a `checked` date.
- `overrides.json` fixes misclassified events without code changes.
- If a source goes red on the page footer for days, run
  `python3 dev/try_source.py <name>` to see why.
````

- [ ] **Step 2: Memory note.** Write `/Users/nathan/.claude/projects/-Users-nathan-Documents-code/memory/reno-today.md`:

```markdown
---
name: reno-today
description: Reno Today (natanforestree/reno-today): Nathan's page + 7:xx Discord digest of everything on in Reno each day, toddler-friendly first; built 2026-10
metadata:
  type: project
---

Nathan, his partner and their ~1-year-old son live in Reno. Reno Today lists everything going on each day, little-ones events first (they "use their judgement"; nothing is hidden). Repo github.com/natanforestree/reno-today (public), local ~/Documents/code/reno-today, page https://natanforestree.github.io/reno-today/. Design spec and plan: docs/superpowers/.

- **How it runs:** Python stdlib collector, GitHub Actions `collect.yml`, dispatched hourly at :30 by the ruby-radar Cloudflare Worker (same fine-grained PAT, now covering both repos). It refreshes every ~3 h, and the Discord digest goes out from 07:00 (it retries until 10:59).
- **Secrets:** TICKETMASTER_KEY and DISCORD_WEBHOOK_URL (Nathan created both).
- **The page:** reads raw.githubusercontent.com first, so Pages build outages don't make it stale (the lesson from Ruby Radar on 2026-10-05).
- **Sources:** Ticketmaster, UNR, Wolf Pack, Aces, the library (LibCal, crawl-delay 10), Tribe sites (The Discovery, Carson, South Tahoe, Virginia City), Reno/Sparks Revize calendars, Washoe parks (Tockify page), standing.json, Open-Meteo, Loving Reno (link and badges only). Skipped: North Lake Tahoe (robots).
- **Arcadipelago:** has a Reno Arch island; seven islands needed the game minimum width lowered to 80.

Related: [[finals-radar-ruby-radar]], [[games-site-github-pages]], [[nathan-prefers-end-to-end-builds]].
```
Add to `MEMORY.md`: `- [Reno Today](reno-today.md) — daily Reno events page + Discord digest for Nathan's family, live 2026-10`.

- [ ] **Step 3: Final checks**

```bash
cd ~/Documents/code/reno-today
python3 -m unittest discover -s tests && npm test
gh run list --repo natanforestree/reno-today --workflow collect.yml --limit 5
```
Expected: everything passes, and recent runs are green and come at about `:30` each hour.

Then open the live page at 390 px. Every source in the footer should be listed, with no red notes (or explained ones).

- [ ] **Step 4: Commit, push, and tell Nathan**

```bash
git add README.md && git commit -m "README: sources, adding a source, maintenance" && git pull --rebase -q && git push
```

Send Nathan a short summary:
- the live link and the screenshots
- when the first real 7:xx message comes
- what he can tune (`overrides.json`, `places.json`)
- the Arcadipelago change (min width 96 → 80)

Offer a draft of a friendly note to the Loving Reno blogger, asking whether Reno Today may list their guide's events in full (the spec's "full inclusion only if the blogger says yes"). Write the draft in chat; Nathan sends it himself if he wants to.
