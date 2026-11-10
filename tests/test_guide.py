import unittest
from datetime import date

from helpers import fixture_text, la
import guide
import model
import net


class GuideTest(unittest.TestCase):
    def test_newest_guide_wins(self):
        g = guide.parse(fixture_text("lovingreno.xml"))
        self.assertEqual(g, {
            "title": "2026 Ultimate Reno Halloween & Fall Guide: Haunted Houses, Fall Foliage, Workshops",
            "shortTitle": "2026 Ultimate Reno Halloween & Fall Guide",
            "url": "https://www.lovingreno.com/2026/09/2026-reno-halloween-fall-guide-haunted.html",
            "published": "2026-09-24",
        })

    def test_newest_post_when_no_guide(self):
        xml = fixture_text("lovingreno.xml").replace("Guide", "Roundup")
        self.assertEqual(guide.parse(xml)["published"], "2026-09-24")

    def test_empty_feed(self):
        self.assertIsNone(guide.parse("<feed xmlns='http://www.w3.org/2005/Atom'></feed>"))

    def test_broken_xml_is_a_fetch_error(self):
        with self.assertRaises(net.FetchError):
            guide.parse("<html>oops")

    def test_current_until_six_weeks_old(self):
        card = {"title": "Fall Guide", "url": "https://www.lovingreno.com/g.html", "published": "2026-09-24"}
        self.assertIs(guide.current(card, date(2026, 9, 24)), card)
        self.assertIs(guide.current(card, date(2026, 11, 4)), card)       # 41 days
        self.assertIsNone(guide.current(card, date(2026, 11, 5)))         # 6 weeks: Halloween is over
        self.assertIsNone(guide.current(card, date(2026, 11, 10)))

    def test_undated_or_missing_card_is_not_current(self):
        today = date(2026, 10, 1)
        self.assertIsNone(guide.current(None, today))
        self.assertIsNone(guide.current({"title": "G", "url": "https://x.org/"}, today))
        self.assertIsNone(guide.current({"title": "G", "url": "https://x.org/", "published": ""}, today))
        self.assertIsNone(guide.current({"title": "G", "url": "https://x.org/", "published": "soon"}, today))


def fin(title, venue_name=None):
    e = model.make_event("x", title, title, la(2026, 10, 10, 10), city="Reno",
                         venue=model.venue(venue_name, "Reno, NV") if venue_name else None)
    return model.finalize(e)


GUIDE_HTML = """<html><head><style>.x{}</style><script>var t = "Great Italian Festival";</script></head><body>
<h2>Fall Festivals</h2><p>Don't miss the <b>44th Annual Great Italian Festival</b> downtown.</p>
<p>The Pumpkin Patch at Andelin Family Farm is great for kids.</p>
<p>Trick or Treat at the Sparks Marina is a local favorite.</p></body></html>"""
CARD = {"title": "2026 Ultimate Reno Halloween & Fall Guide: More", "shortTitle": "2026 Ultimate Reno Halloween & Fall Guide",
        "url": "https://www.lovingreno.com/2026/09/guide.html", "published": "2026-09-24"}


class BadgesTest(unittest.TestCase):
    def test_norm(self):
        self.assertEqual(guide.norm("The 44th Annual Great Italian Festival!"), " great italian festival ")
        self.assertEqual(guide.norm("Kids&#8217; Day"), " kids day ")

    def test_page_text_drops_scripts_and_styles(self):
        text = guide.page_text(GUIDE_HTML)
        self.assertNotIn("var t", text)
        self.assertIn(" great italian festival ", text)

    def test_badges(self):
        events = [fin("Great Italian Festival"),                       # 3 words, in the guide
                  fin("Pumpkin Patch", "Andelin Family Farm"),         # 2 words + venue nearby
                  fin("Pumpkin Patch", "Lattin Farms"),                # 2 words, venue not mentioned
                  fin("Storytime"),                                     # 1 word: never
                  fin("Fall Festivals"),                                # 2 words, no venue
                  fin("Trick or Treat at the Sparks Marina"),
                  fin("Wind Ensemble Concert")]                         # not in the guide
        n = guide.badges(events, CARD, guide.page_text(GUIDE_HTML))
        self.assertEqual([bool(e["lovingReno"]) for e in events], [True, True, False, False, False, True, False])
        self.assertEqual(n, 3)
        self.assertEqual(events[0]["lovingReno"], {"title": "2026 Ultimate Reno Halloween & Fall Guide",
                                                   "url": "https://www.lovingreno.com/2026/09/guide.html"})

    def test_mentions_are_keyed_by_title_and_venue(self):
        events = [fin("Great Italian Festival"), fin("Pumpkin Patch", "Andelin Family Farm"),
                  fin("Pumpkin Patch", "Lattin Farms"), fin("Wind Ensemble Concert")]
        keys = guide.mentions(events, guide.page_text(GUIDE_HTML))
        self.assertEqual(keys, {"great italian festival @ ", "pumpkin patch @ andelin family farm"})
        self.assertNotIn("Fall Guide", repr(keys), "only our own events' names, never the guide's text")

    def test_mark_applies_saved_keys_to_later_occurrences(self):
        later = [fin("The 45th Annual Great Italian Festival"), fin("Pumpkin Patch", "Andelin Family Farm"),
                 fin("Pumpkin Patch", "Lattin Farms")]
        n = guide.mark(later, CARD, {"great italian festival @ ", "pumpkin patch @ andelin family farm"})
        self.assertEqual([bool(e["lovingReno"]) for e in later], [True, True, False])
        self.assertEqual(n, 2)


if __name__ == "__main__":
    unittest.main()
