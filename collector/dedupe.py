"""Merge the same event listed by more than one source (spec: "Merging
duplicates"). Same local date, starts within 30 minutes, and titles that
mostly match (or match less well at the same venue). A listing calendar's
copy of a show also merges at the same venue within 90 minutes (doors vs
show time) when one title, without its venue words, holds the other's."""

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
# Which listing wins title, time and place: the organiser's own feed, then the ticket seller,
# then a listing calendar (a district guide or radio station relisting other people's shows).
ABBREVIATIONS = {"st": "street", "ave": "avenue", "blvd": "boulevard", "rd": "road", "pkwy": "parkway"}
KIND_RANK = {"organiser": 0, "ticketing": 1, "listing": 2}
SAME_SHOW_MINUTES = 90
LOOKALIKE_HOURS = 3
# Words too common to tie two events together on their own (with GENERIC_VENUE).
COMMON_WORDS = {
    "monday", "mondays", "tuesday", "tuesdays", "wednesday", "wednesdays", "thursday", "thursdays",
    "friday", "fridays", "saturday", "saturdays", "sunday", "sundays", "weekend", "weekends",
    "morning", "afternoon", "evening", "tonight", "january", "february", "august", "september",
    "october", "november", "december", "halloween", "pumpkin", "pumpkins", "spooky", "harvest",
    "thanksgiving", "christmas", "holiday", "holidays", "festival", "festivals", "concert", "concerts",
    "market", "markets", "farmers", "series", "season", "special", "annual", "celebration", "carnival",
    "parade", "tournament", "workshop", "presents", "featuring", "tickets", "edition", "opening",
    "family", "families", "children", "district", "street", "avenue", "virginia", "brewery",
    "breweries", "national", "american", "northern", "sierra", "truckee", "washoe", "trivia",
    "karaoke", "comedy", "dancing", "country", "classic", "outdoor", "outdoors", "walking",
}


def tokens(text):
    text = (text or "").lower().replace("'", "").replace("’", "")
    return {ABBREVIATIONS.get(w, w) for w in re.findall(r"[a-z0-9]+", text)
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


def venue_words(e):
    return tokens((e.get("venue") or {}).get("name"))


def headline(e):
    """Title words without the event's own venue: "Strangelove at Cargo Concert Hall" -> strangelove."""
    return tokens(e["title"]) - venue_words(e)


def same_show(a, b):
    """A listing calendar's copy of a show: "Nekrogoblikon at Cargo Concert Hall" at 6pm (doors)
    and Ticketmaster's "Nekrogoblikon, Rivers of Nihil, ..." at 7pm, both at Cargo."""
    if "listing" not in (a.get("_kind"), b.get("_kind")) or a["allDay"] or b["allDay"]:
        return False
    if a["start"][:10] != b["start"][:10] or not same_venue(a, b):
        return False
    gap = datetime.fromisoformat(a["start"]) - datetime.fromisoformat(b["start"])
    ha, hb = headline(a), headline(b)
    return (abs(gap.total_seconds()) <= SAME_SHOW_MINUTES * 60 and bool(ha and hb)
            and (ha <= hb or hb <= ha))


def same_address(a, b):
    ka, kb = (tokens((e.get("venue") or {}).get("address")) for e in (a, b))
    return bool(ka) and ka == kb


def ticket_repeat(a, b):
    """Ticketmaster lists some club shows twice, on ticketmaster.com and on TicketWeb: a shorter
    title ("Nekrogoblikon" vs "Nekrogoblikon, Rivers of Nihil, ..."), doors vs show time and
    another venue name ("Cargo" vs "Cargo Concert Hall"), at the same address. Identical titles at
    different times are early and late shows, so one title must hold the other's words and more."""
    if a.get("_kind") != "ticketing" or b.get("_kind") != "ticketing" or a["allDay"] or b["allDay"]:
        return False
    if a["start"][:10] != b["start"][:10] or not same_address(a, b):
        return False
    gap = datetime.fromisoformat(a["start"]) - datetime.fromisoformat(b["start"])
    ha, hb = headline(a), headline(b)
    return (abs(gap.total_seconds()) <= SAME_SHOW_MINUTES * 60 and bool(ha and hb)
            and (ha < hb or hb < ha))


def is_duplicate(a, b):
    ta, tb = tokens(a["title"]), tokens(b["title"])
    if _source(a) == _source(b):
        no_venues = not a.get("venue") and not b.get("venue")
        return ((same_time(a, b) and ta == tb and a["start"] == b["start"]
                 and (no_venues or same_place(a, b))) or ticket_repeat(a, b))
    if same_time(a, b):
        o = overlap(ta, tb)
        # Also compare the titles without either venue's words ("Great Italian Festival: Virginia
        # Street" vs "44th Annual Great Italian Festival" at Virginia St), while two words are left.
        places = venue_words(a) | venue_words(b)
        sa, sb = ta - places, tb - places
        if len(sa) >= 2 and len(sb) >= 2:
            o = max(o, overlap(sa, sb))
        if o >= 0.8 or (o >= 0.6 and same_venue(a, b)):
            return True
    return same_show(a, b)


def _detail(e):
    """Between two ticket listings of one show, the one with a price and the fuller title wins."""
    if e.get("_kind") != "ticketing":
        return (False, 0)
    return (not e.get("price"), -len(tokens(e["title"])))


def merge(group):
    ranked = sorted(group, key=lambda e: (KIND_RANK.get(e.get("_kind"), 0), _detail(e), e["id"]))
    m = dict(ranked[0])
    timed = [e for e in ranked if not e["allDay"]]
    if m["allDay"] and timed:
        m["start"], m["end"], m["allDay"] = timed[0]["start"], timed[0]["end"], False
    placed = next((e for e in ranked if e.get("venue")), ranked[0])
    m["venue"], m["area"], m["drive"] = placed.get("venue"), placed["area"], placed["drive"]
    by_price = sorted(ranked, key=lambda e: e.get("_kind") != "ticketing")
    m["price"] = next((e["price"] for e in by_price if e.get("price")), None)
    links, seen = [], set()
    for e in ranked:   # one link per source: two copies from one source sell the same tickets
        for link in e["links"]:
            if link["source"] not in seen:
                seen.add(link["source"])
                links.append(link)
    m["links"] = links
    m["ongoing"] = all(e["ongoing"] for e in ranked)
    m["_text"] = " ".join(e.get("_text", "") for e in ranked)[:4000]
    m["_tags"] = sorted(set().union(*(e.get("_tags", []) for e in ranked)))
    for flag in ("_family", "_adult", "_allAges", "_outdoor"):
        m[flag] = any(e.get(flag) for e in ranked)
    return m


def _unusual(e):
    return {w for w in tokens(e["title"])
            if len(w) >= 6 and not w.isdigit() and w not in COMMON_WORDS and w not in GENERIC_VENUE}


def _lookalike(listing, other):
    if listing["start"][:10] != other["start"][:10] or not (_unusual(listing) & _unusual(other)):
        return False
    if listing["allDay"] or other["allDay"]:
        return True
    gap = datetime.fromisoformat(listing["start"]) - datetime.fromisoformat(other["start"])
    return abs(gap.total_seconds()) <= LOOKALIKE_HOURS * 3600


def drop_listing_lookalikes(events):
    """A listing calendar's event that didn't merge but shares an unusual title word with another
    calendar's event the same day, within LOOKALIKE_HOURS ("Burning Man Decompression Event:
    Brewery District" vs "Reno Decompression 2026"), is most likely the same event: drop the copy."""
    others = [e for e in events if e.get("_kind") != "listing"]
    return [e for e in events
            if e.get("_kind") != "listing" or not any(_lookalike(e, o) for o in others)]


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
    return sorted(drop_listing_lookalikes(merged), key=lambda e: (e["start"], e["id"]))
