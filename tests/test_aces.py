import os
import unittest
from unittest import mock

from helpers import fixture_json, fixture_path, la
import net
from sources import aces
from sources.base import Context, SourceError


class AcesTest(unittest.TestCase):
    def setUp(self):
        self.by_id = {e["id"]: e for e in aces.parse(fixture_json("aces.json"))}

    def test_home_games_that_are_on(self):
        self.assertEqual(sorted(self.by_id), ["aces:815155", "aces:815157"])

    def test_game(self):
        e = self.by_id["aces:815155"]
        self.assertEqual(e["title"], "Reno Aces vs Las Vegas Aviators")
        self.assertEqual(e["start"], "2026-05-13T18:05:00-07:00")
        self.assertEqual(e["venue"]["name"], "Greater Nevada Field")
        self.assertEqual(e["venue"]["address"], "250 Evans Ave, Reno, NV 89501")
        self.assertEqual(e["links"][0]["url"], "https://www.milb.com/gameday/815155")
        self.assertTrue(e["_allAges"] and e["_outdoor"])

    def test_time_tbd_is_all_day_on_the_official_date(self):
        e = self.by_id["aces:815157"]
        self.assertTrue(e["allDay"])
        self.assertEqual(e["start"], "2026-05-14T00:00:00-07:00")

    def test_off_season_is_zero_events_not_an_error(self):
        self.assertEqual(aces.parse({"totalGames": 0, "dates": []}), [])

    def test_fetch_asks_for_the_window_and_rejects_reshaped_bodies(self):
        ctx = Context(la(2026, 10, 5), la(2026, 10, 13))
        seen = []
        with mock.patch.object(net, "get_json", lambda url, **kw: seen.append(url) or {"dates": []}):
            self.assertEqual(aces.fetch(ctx), [])
        self.assertIn("startDate=2026-10-05&endDate=2026-10-12", seen[0])
        with mock.patch.object(net, "get_json", lambda url, **kw: {"message": "oops"}):
            with self.assertRaises(SourceError):
                aces.fetch(ctx)

    def test_real_recording_parses(self):
        if not os.path.exists(fixture_path("real/aces.json")):
            self.skipTest("no real recording yet")
        events = aces.parse(fixture_json("real/aces.json"))
        self.assertTrue(events)
        self.assertTrue(all(e["title"].startswith("Reno Aces vs ") for e in events))


if __name__ == "__main__":
    unittest.main()
