import os
import unittest
from unittest import mock

from helpers import fixture_json, fixture_path, la
import net
from sources import ticketmaster
from sources.base import Context, SourceError

CTX = Context(la(2026, 10, 5), la(2026, 10, 13), {"TICKETMASTER_KEY": "k123"})


class ParseTest(unittest.TestCase):
    def setUp(self):
        self.by_id = {e["id"]: e for e in ticketmaster.parse(fixture_json("ticketmaster.json")["_embedded"]["events"])}

    def test_drops_parking_and_cancelled(self):
        self.assertEqual(sorted(self.by_id), ["tm:G5vYZ9A1", "tm:G5vYZ9A2", "tm:G5vYZ9A3", "tm:G5vYZ9A6"])

    def test_drops_season_passes_and_hotel_packages(self):
        self.assertNotIn("tm:G5vYZ9A7", self.by_id)
        self.assertNotIn("tm:G5vYZ9A8", self.by_id)
        self.assertNotIn("tm:G5vYZ9A9", self.by_id)

    def test_concert(self):
        e = self.by_id["tm:G5vYZ9A1"]
        self.assertEqual(e["start"], "2026-10-10T19:30:00-07:00")
        self.assertEqual(e["price"], {"min": 45.5, "max": 129.0})
        self.assertEqual(e["venue"], {"name": "Grand Sierra Resort and Casino", "address": "2500 E 2nd St, Reno, NV",
                                      "lat": 39.5232, "lon": -119.7762})
        self.assertEqual(e["links"], [{"source": "tm", "url": "https://www.ticketmaster.com/event/G5vYZ9A1"}])
        self.assertEqual(e["_kind"], "ticketing")
        self.assertEqual(e["_tags"], ["music", "pop", "rock"])

    def test_family_and_adult_flags(self):
        self.assertTrue(self.by_id["tm:G5vYZ9A2"]["_family"])
        self.assertIn("children's theatre", self.by_id["tm:G5vYZ9A2"]["_tags"])
        self.assertTrue(self.by_id["tm:G5vYZ9A3"]["_adult"])

    def test_time_tba_is_all_day_and_tahoe(self):
        e = self.by_id["tm:G5vYZ9A6"]
        self.assertTrue(e["allDay"])
        self.assertEqual(e["start"], "2026-10-12T00:00:00-07:00")
        self.assertEqual(e["area"], "tahoe")
        self.assertIsNone(e["price"])


class PriceTest(unittest.TestCase):
    def price(self, ranges):
        item = {"id": "P1", "name": "Comedy Night", "dates": {"start": {"dateTime": "2026-10-11T03:00:00Z"}},
                "priceRanges": ranges}
        [e] = ticketmaster.parse([item])
        return e["price"]

    def test_a_bad_price_entry_does_not_fail_the_source(self):
        self.assertEqual(self.price([{"min": 20, "max": 50}, {"min": 30, "max": None}]), {"min": 20.0, "max": 50.0})
        self.assertEqual(self.price([{"max": 99}, {"min": 25.5, "max": 60}]), {"min": 25.5, "max": 60.0})
        self.assertEqual(self.price([None, "x", {"min": "10", "max": "20"}, {"min": 15}]), {"min": 15.0, "max": 15.0})
        self.assertEqual(self.price([{"min": None, "max": None}]), None)
        self.assertEqual(self.price(None), None)


class FetchTest(unittest.TestCase):
    def test_not_set_up_yet(self):
        with self.assertRaises(SourceError) as cm:
            ticketmaster.fetch(Context(la(2026, 10, 5), la(2026, 10, 13), {}))
        self.assertIn("not set up", str(cm.exception))

    def test_window_in_utc_and_paging(self):
        calls = []

        def fake(url, **kw):
            calls.append((url, kw))
            page = int(url.split("&page=")[1].split("&")[0])
            body = fixture_json("ticketmaster.json")
            body["page"] = {"size": 200, "totalElements": 400, "totalPages": 2, "number": page}
            return body

        with mock.patch.object(net, "get_json", fake):
            got = ticketmaster.fetch(CTX)
        self.assertEqual(len(calls), 2)
        self.assertIn("startDateTime=2026-10-05T07:00:00Z", calls[0][0])
        self.assertIn("endDateTime=2026-10-13T07:00:00Z", calls[0][0])
        self.assertEqual(calls[0][1].get("label"), "ticketmaster")
        self.assertEqual(len(got), 8)

    def test_no_matches_is_zero_events(self):
        with mock.patch.object(net, "get_json", lambda url, **kw: {"page": {"size": 200, "totalElements": 0,
                                                                            "totalPages": 0, "number": 0}}):
            self.assertEqual(ticketmaster.fetch(CTX), [])

    def test_reshaped_body_is_a_source_error(self):
        with mock.patch.object(net, "get_json", lambda url, **kw: {"fault": {"faultstring": "Invalid ApiKey"}}):
            with self.assertRaises(SourceError):
                ticketmaster.fetch(CTX)

    def test_real_recording_parses(self):
        if not os.path.exists(fixture_path("real/ticketmaster.json")):
            self.skipTest("kept local only (git-ignored; Ticketmaster's terms limit storing event data)")
        data = fixture_json("real/ticketmaster.json")
        self.assertNotIn("apikey", str(data).lower())
        events = ticketmaster.parse((data.get("_embedded") or {}).get("events") or [])
        self.assertTrue(events)
        self.assertTrue(all(e["id"].startswith("tm:") for e in events))


if __name__ == "__main__":
    unittest.main()
