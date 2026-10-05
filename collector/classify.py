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
