"""Loving Reno (lovingreno.com): their current seasonal guide, linked and never
copied. We keep only its title, URL and date."""

import html
import re
import xml.etree.ElementTree as ET

import net
from dedupe import tokens

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


DROP = re.compile(r"\b((19|20)\d\d|\d+(st|nd|rd|th)|annual|the)\b")
NEAR = 300   # characters either side of a two-word title where the venue must appear


def norm(text):
    """Lower-case words only, padded with spaces: ' great italian festival '."""
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or "")).lower().replace("'", "").replace("\u2019", "")
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
