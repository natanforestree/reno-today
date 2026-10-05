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
