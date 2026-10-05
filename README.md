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
