import unittest

from helpers import fixture_text
import guide
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


if __name__ == "__main__":
    unittest.main()
