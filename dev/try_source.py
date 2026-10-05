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
