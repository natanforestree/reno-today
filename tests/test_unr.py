import os
import unittest
from datetime import datetime
from unittest import mock

from helpers import fixture_json, fixture_path, la
import net
from sources import unr
from sources.base import Context, SourceError

CTX = Context(start=la(2026, 10, 5), end=la(2026, 10, 13))


class UnrParseTest(unittest.TestCase):
    def setUp(self):
        self.by_id = {e["id"]: e for e in unr.parse(fixture_json("unr.json")["events"])}

    def test_keeps_only_public_reno_listings(self):
        self.assertEqual(sorted(self.by_id), ["unr:103", "unr:104", "unr:107", "unr:109"])

    def test_exhibit_is_ongoing_on_campus(self):
        e = self.by_id["unr:103"]
        self.assertTrue(e["ongoing"])
        self.assertEqual(e["venue"]["name"], "Mathewson-IGT Knowledge Center")
        self.assertEqual(e["area"], "reno")
        self.assertEqual((e["start"], e["end"]), ("2026-10-06T08:00:00-07:00", "2026-10-06T17:00:00-07:00"))
        self.assertEqual(e["links"], [{"source": "unr", "url": "https://events.unr.edu/event/a-few-of-our-favorite-things"}])

    def test_prices(self):
        self.assertEqual(self.by_id["unr:104"]["price"], {"free": True})
        self.assertEqual(self.by_id["unr:107"]["price"], {"min": 5.0, "max": 5.0})
        self.assertIsNone(self.by_id["unr:103"]["price"])

    def test_all_day(self):
        e = self.by_id["unr:109"]
        self.assertTrue(e["allDay"])
        self.assertEqual(e["start"], "2026-10-09T00:00:00-07:00")
        self.assertEqual(e["venue"]["name"], "University of Nevada, Reno")

    def test_classification_inputs(self):
        e = self.by_id["unr:107"]
        self.assertIn("family engagement", e["_tags"])
        self.assertIn("kids and families", e["_text"])
        self.assertEqual((e["venue"]["lat"], e["venue"]["lon"]), (39.5466, -119.8175))
        self.assertEqual(e["_kind"], "organiser")


class UnrFetchTest(unittest.TestCase):
    def test_follows_pages_with_the_window_dates(self):
        items = fixture_json("unr.json")["events"]
        pages = {1: {"events": items[:4], "page": {"current": 1, "total": 2}},
                 2: {"events": items[4:], "page": {"current": 2, "total": 2}}}
        urls = []

        def fake_get_json(url, **kw):
            urls.append(url)
            return pages[int(url.rsplit("page=", 1)[1])]

        with mock.patch.object(net, "get_json", fake_get_json):
            got = unr.fetch(CTX)
        self.assertEqual(len(urls), 2)
        self.assertIn("start=2026-10-05&end=2026-10-12", urls[0])
        self.assertEqual(len(got), 4)

    def test_a_reshaped_body_is_a_source_error(self):
        with mock.patch.object(net, "get_json", lambda url, **kw: {"error": "maintenance"}):
            with self.assertRaises(SourceError):
                unr.fetch(CTX)

    def test_real_recording_parses(self):
        if not os.path.exists(fixture_path("real/unr.json")):
            self.skipTest("no real recording yet")
        events = unr.parse(fixture_json("real/unr.json")["events"])
        self.assertTrue(events)
        for e in events:
            self.assertIn(e["area"], ("reno", "sparks"))
            self.assertTrue(e["title"])
            datetime.fromisoformat(e["start"])


if __name__ == "__main__":
    unittest.main()
