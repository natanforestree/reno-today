import os
import unittest
from unittest import mock

from helpers import fixture_path, fixture_text, la
import net
from sources import wolfpack
from sources.base import Context, SourceError


class WolfpackTest(unittest.TestCase):
    def setUp(self):
        self.by_id = {e["id"].split(":", 1)[1]: e for e in wolfpack.parse(fixture_text("wolfpack.ics"))}

    def test_home_games_only(self):
        self.assertEqual(sorted(self.by_id), ["vcal_14076-nevadawolfpack.com", "vcal_14215-nevadawolfpack.com",
                                              "vcal_14224-nevadawolfpack.com", "vcal_14250-nevadawolfpack.com",
                                              "vcal_14290-nevadawolfpack.com"])

    def test_title_venue_time_and_link(self):
        e = self.by_id["vcal_14076-nevadawolfpack.com"]
        self.assertEqual(e["title"], "Nevada Football vs San José State")
        self.assertEqual(e["venue"]["name"], "Mackay Stadium")
        self.assertEqual(e["start"], "2026-10-24T14:00:00-07:00")
        self.assertEqual(e["end"], "2026-10-24T17:00:00-07:00")
        self.assertEqual(e["links"][0]["url"], "https://nevadawolfpack.com/calendar.aspx?game_id=14076&sport_id=2")
        self.assertEqual(e["area"], "reno")

    def test_result_tag_and_spacing(self):
        e = self.by_id["vcal_14250-nevadawolfpack.com"]
        self.assertEqual(e["title"], "Nevada Women's Basketball vs Sacramento State")
        self.assertEqual(e["venue"]["name"], "Lawlor Events Center")

    def test_time_tba_is_all_day(self):
        e = self.by_id["vcal_14224-nevadawolfpack.com"]
        self.assertTrue(e["allDay"])
        self.assertEqual(e["start"], "2026-11-18T00:00:00-08:00")

    def test_stateline_counts_as_tahoe(self):
        e = self.by_id["vcal_14215-nevadawolfpack.com"]
        self.assertEqual((e["area"], e["drive"]), ("tahoe", "~70 min"))

    def test_no_venue_name(self):
        e = self.by_id["vcal_14290-nevadawolfpack.com"]
        self.assertIsNone(e["venue"]["name"])
        self.assertEqual(e["venue"]["address"], "Reno, NV")

    def test_not_a_calendar_is_a_source_error(self):
        ctx = Context(la(2026, 10, 5), la(2026, 10, 13))
        with mock.patch.object(net, "get_text", lambda url, **kw: "<html>maintenance</html>"):
            with self.assertRaises(SourceError):
                wolfpack.fetch(ctx)

    def test_real_recording_parses(self):
        if not os.path.exists(fixture_path("real/wolfpack.ics")):
            self.skipTest("no real recording yet")
        events = wolfpack.parse(fixture_text("real/wolfpack.ics"))
        self.assertTrue(events)
        self.assertTrue(all(e["area"] in ("reno", "tahoe") for e in events))
        self.assertFalse([e for e in events if e["title"].startswith("[")])


if __name__ == "__main__":
    unittest.main()
