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

## Previewing the page

    python3 dev/make_fixture.py --today 2026-10-10
    python3 -m http.server 8000
    open "http://localhost:8000/docs/?data=../dev/fixture/full/&now=2026-10-10T10:45:00-07:00"

Variants: `full`, `empty`, `partial`, `failing`. Without `?data=` the page reads
`docs/data/` (the live data once the collector has run).
