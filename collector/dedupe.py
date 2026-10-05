"""Merge the same event listed by more than one source (spec: "Merging
duplicates"). Same local date, starts within 30 minutes, and titles that
mostly match (or match less well at the same venue)."""

import re
from datetime import datetime

FILLER = {"the", "a", "an", "and", "of", "at", "in", "on", "vs", "v", "with",
          "presents", "presented", "by", "featuring", "feat", "ft", "live", "tour"}
# Words many different venues share: kinds of place, towns and directions.
GENERIC_VENUE = {
    "library", "branch", "park", "parks", "center", "centre", "community", "recreation", "regional",
    "hall", "theater", "theatre", "museum", "arena", "stadium", "field", "room", "auditorium",
    "amphitheater", "amphitheatre", "plaza", "gallery", "club", "casino", "resort", "hotel",
    "church", "school", "event", "events", "venue", "building", "trail", "trailhead",
    "reno", "sparks", "carson", "city", "tahoe", "lake", "nevada", "nv", "downtown",
    "north", "south", "east", "west", "northwest", "northeast", "southwest", "southeast", "valley", "valleys",
}
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
    """Venue names share half their distinctive words ("Pioneer Center" and "Pioneer
    Center for the Performing Arts"); "Library" or "Park" alone doesn't count."""
    va = tokens((a.get("venue") or {}).get("name")) - GENERIC_VENUE
    vb = tokens((b.get("venue") or {}).get("name")) - GENERIC_VENUE
    return bool(va and vb) and len(va & vb) / min(len(va), len(vb)) >= 0.5


def same_place(a, b):
    """The very same venue: equal names, or equal addresses when a name is missing.
    One source lists one program at several branches ("Baby Story Time" at Sparks
    and at Downtown Reno), so its own listings need this, not same_venue."""
    va, vb = a.get("venue") or {}, b.get("venue") or {}
    for field in ("name", "address"):
        ka, kb = tokens(va.get(field)), tokens(vb.get(field))
        if ka and kb:
            return ka == kb
    return False


def is_duplicate(a, b):
    if not same_time(a, b):
        return False
    ta, tb = tokens(a["title"]), tokens(b["title"])
    if _source(a) == _source(b):
        no_venues = not a.get("venue") and not b.get("venue")
        return ta == tb and a["start"] == b["start"] and (no_venues or same_place(a, b))
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
