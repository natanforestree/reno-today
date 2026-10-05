import contextlib
import io
import os
import unittest
from unittest import mock

from helpers import fixture_json, fixture_path, la
import net
from sources import library
from sources.base import Context, SourceError

CTX = Context(la(2026, 10, 5), la(2026, 10, 13))


class LibraryParseTest(unittest.TestCase):
    def setUp(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:    # the fixture's unknown branch is reported
            self.by_id = {e["id"]: e for e in library.parse(fixture_json("library.json")["results"])}
        self.assertIn("Mystery Branch Library", out.getvalue())

    def test_skips_online_events(self):
        self.assertEqual(sorted(self.by_id), ["library:1001", "library:1002", "library:1003", "library:1005", "library:1006"])

    def test_implausible_end_is_dropped_and_incline_is_tahoe(self):
        e = self.by_id["library:1001"]
        self.assertEqual(e["start"], "2026-10-05T10:30:00-07:00")
        self.assertIsNone(e["end"])
        self.assertEqual((e["area"], e["drive"]), ("tahoe", "~45 min"))
        self.assertTrue(e["_family"])
        self.assertIn("babies & toddlers", e["_tags"])
        self.assertEqual(e["price"], {"free": True})

    def test_branch_address(self):
        e = self.by_id["library:1002"]
        self.assertEqual(e["venue"]["name"], "Downtown Reno Library")
        self.assertEqual(e["venue"]["address"], "301 S Center St, Reno, NV 89501")
        self.assertEqual(e["end"], "2026-10-06T10:45:00-07:00")

    def test_all_day_series_is_ongoing(self):
        e = self.by_id["library:1003"]
        self.assertTrue(e["allDay"] and e["ongoing"])
        self.assertFalse(e["_family"])

    def test_unknown_branch_still_lists(self):
        e = self.by_id["library:1005"]
        self.assertEqual((e["venue"]["name"], e["area"]), ("Mystery Branch Library", "reno"))

    def test_registration_cost(self):
        self.assertEqual(self.by_id["library:1006"]["price"], {"min": 5.0, "max": 5.0})
        self.assertEqual(self.by_id["library:1006"]["area"], "sparks")


class LibraryFetchTest(unittest.TestCase):
    def test_one_request_per_day_with_the_crawl_delay(self):
        urls, sleeps = [], []
        with mock.patch.object(net, "get_json", lambda url, **kw: urls.append(url) or {"results": []}), \
                mock.patch.object(library.time, "sleep", sleeps.append):
            self.assertEqual(library.fetch(CTX), [])
        self.assertEqual([u.split("date=")[1][:10] for u in urls],
                         [f"2026-10-{d:02d}" for d in range(5, 13)])
        self.assertEqual(sleeps, [library.CRAWL_DELAY] * 7)

    def test_reshaped_body_is_a_source_error(self):
        with mock.patch.object(net, "get_json", lambda url, **kw: {"error": "x"}), \
                mock.patch.object(library.time, "sleep", lambda s: None):
            with self.assertRaises(SourceError):
                library.fetch(CTX)

    def test_real_recording_parses(self):
        if not os.path.exists(fixture_path("real/library.json")):
            self.skipTest("no real recording yet")
        events = library.parse(fixture_json("real/library.json")["results"])
        self.assertTrue(events)
        self.assertTrue(any(e["_family"] for e in events))


if __name__ == "__main__":
    unittest.main()
