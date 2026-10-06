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

## Visitor count

The page keeps a tiny daily visitor count, and the morning Discord message ends
with a line like `👀 Yesterday: 12 visitors`.

- **Stored:** only a site name (`reno-today`), a Reno-local date and a number,
  in the Ruby Radar Worker's database (`visits` table, repo `finals-radar`).
- **Not stored, anywhere:** IP addresses, user agents, cookies, referrers, or
  anything else about who visited. The request carries no body and no custom headers.
- **Once a day per browser:** the browser remembers "already counted today" in
  its own localStorage (`reno-today:counted`); that never leaves the device.
- Only the live hosts count (`natanforestree.github.io`, `renotoday.com`,
  `www.renotoday.com`), never localhost, `?data=` fixtures or `?now=` previews.
- The collector reads the count only when it is about to send the digest. If
  that fails, the line is simply left out.

## Previewing the page

    python3 dev/make_fixture.py --today 2026-10-10
    python3 -m http.server 8000
    open "http://localhost:8000/docs/?data=../dev/fixture/full/&now=2026-10-10T10:45:00-07:00"

Variants: `full`, `empty`, `partial`, `failing`. Without `?data=` the page reads
`docs/data/` (the live data once the collector has run).

**After editing anything in `docs/`**, run `node dev/stamp.mjs`. It stamps each file's
address with a hash of its content (`app.js?v=1a2b3c4d`), so browsers fetch new page code
right away instead of reusing a cached copy for up to 10 minutes. `npm test` fails while a
stamp is out of date.

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

**Facts only.** The repo is public, so new sources and recordings keep facts
(title, time, place, price, link), not write-ups. Real recordings in
`tests/fixtures/real/` are scrubbed: descriptions are reduced to keyword cues
(`classify.cues`), and there are no write-ups, contacts, join links or tokens.
Saved last-good results in `state/sources/` likewise keep only the keyword cues
(`classify.cues`), not descriptions.

The Ticketmaster recording (`tests/fixtures/real/ticketmaster.json`) stays on your
own machine and is git-ignored: Ticketmaster's terms allow storing event data only
for as long as the service needs it. Its test skips when the file isn't there.

## Maintenance

- `places.json` hours change with the seasons. Each entry has a `checked` date.
  Seasonal re-checks:
  - County park hours switch after the November time change (re-check 2026-11-01).
  - Animal Ark closes after Thanksgiving, though `places.json` lists all of November.
  - V&T Railroad starts May 23, though May is listed.
  - Idlewild, Virginia Lake and Wingfield hours are winter hours (re-check in April).
- `overrides.json` fixes misclassified events without code changes.
- If a source goes red on the page footer for days, run
  `python3 dev/try_source.py <name>` to see why.
