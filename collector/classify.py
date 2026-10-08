"""Tier and hints for each event (spec: "Classification"). The rules are plain
regular expressions so they're testable and easy to adjust; overrides.json has
the last word."""

import json
import re

LITTLE_WORDS = re.compile(
    r"\b(story ?times?|bab(y|ies)|toddlers?|tots?|lap-?sits?|little ones|preschool(ers?)?|"
    r"famil(y|ies)|kids|children(['’]s)?|sensory|puppets?|play ?groups?)\b", re.I)
# Exact (lower-cased) source categories that mean "made for little ones". Looser
# categories such as a tourism site's "Kids & Families" are judged by the source
# module, which sets family=True only where it holds (see sources/tribe.py).
LITTLE_TAGS = {"family", "children's theatre", "children's music", "story time",
               "storytime", "babies & toddlers", "preschool"}
ADULT_WORDS = re.compile(
    r"(\b(21|18) ?\+|\b(21|18) (and|&) (over|older|up)\b|\b(bar|pub) crawls?\b|"
    r"\b(wine|beer) tastings?\b|\bburlesque\b)", re.I)
ADULT_VENUES = re.compile(r"\b(lounge|bar|tavern|pub|saloon|nightclub|cocktails?)\b", re.I)
# The same places named in a title ("Live Music at Rush Lounge"); "bar" is left out here
# ("Storytime at the Snack Bar").
ADULT_PLACE_IN_TITLE = re.compile(r"\bat\b.*\b(lounge|tavern|pub|saloon|nightclub|cocktails?)\b", re.I)
OUTDOOR_WORDS = re.compile(
    r"\b(park|trails?|festival grounds|outdoors?|markets?|amphitheat(er|re)|beach)\b", re.I)
# Live music: Ticketmaster's "Music" segment, plain words in a title, or "live music" or a
# concert in the description. Broad tags such as a tourism site's "Music & Dance" (karaoke,
# nightclubs, DJ trivia) and a bare "music" (Baby Music & Movement) aren't enough.
MUSIC_TAGS = {"music", "concert", "concerts", "live music"}
MUSIC_TITLE = re.compile(
    r"\b(symphon(y|ic|ies)|orchestras?|philharmonic|jazz|blues|bluegrass|recitals?|choirs?|"
    r"chorales?|dueling pianos)\b", re.I)
MUSIC_TEXT = re.compile(r"\b(live (music|bands?)|concerts?)\b", re.I)
HINTS = ("all-ages", "outdoors", "daytime", "music", "21+")


def classify(event):
    e = dict(event)
    venue_name = (e.get("venue") or {}).get("name") or ""
    text = f"{e['title']} {e.get('_text', '')}"
    adult = bool(e.get("_adult") or ADULT_WORDS.search(text) or ADULT_VENUES.search(venue_name)
                 or ADULT_PLACE_IN_TITLE.search(e["title"]))
    daytime = e["allDay"] or int(e["start"][11:13]) < 17
    # A description that only mentions families or kids counts in the daytime; an evening
    # event needs it in the title, a family tag, or the source's say-so.
    little = not adult and bool(e.get("_family") or LITTLE_WORDS.search(e["title"])
                                or set(e.get("_tags", [])) & LITTLE_TAGS
                                or (daytime and LITTLE_WORDS.search(e.get("_text", ""))))
    hints = []
    if e.get("_allAges") and not adult:
        hints.append("all-ages")
    if e.get("_outdoor") or OUTDOOR_WORDS.search(f"{e['title']} {venue_name}"):
        hints.append("outdoors")
    if daytime:
        hints.append("daytime")
    if set(e.get("_tags", [])) & MUSIC_TAGS or MUSIC_TITLE.search(e["title"]) or MUSIC_TEXT.search(text):
        hints.append("music")
    if adult:
        hints.append("21+")
    e["tier"] = "little" if little else "general"
    e["hints"] = hints
    return e


def cues(text):
    """Only the words of a description that classify() looks for, e.g. "toddlers 21+ live music".
    Saved last-good results keep these instead of the description: write-ups aren't
    ours to store (spec: "Store and show only facts")."""
    found = [m.group(0) for pattern in (LITTLE_WORDS, ADULT_WORDS, MUSIC_TEXT) for m in pattern.finditer(text or "")]
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
