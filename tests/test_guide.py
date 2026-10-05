import unittest

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


if __name__ == "__main__":
    unittest.main()
