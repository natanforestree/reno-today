import unittest
from datetime import date
from unittest import mock

from helpers import fixture_json, la
import net
from sources.base import Context, SourceError
from sources.revize import RevizeSource

RENO = RevizeSource("reno", "City of Reno", "www.reno.gov", "renonv", city="Reno",
                    page_url="https://www.reno.gov/", skip_calendars={"3"}, kid_calendars={"8"},
                    calendar_names={"5": "parks & rec", "8": "youth", "9": "special events"})


class RevizeTest(unittest.TestCase):
    def setUp(self):
        self.events = RENO.parse(fixture_json("revize.json"), date(2026, 10, 5), date(2026, 10, 12))
        self.by_title = {}
        for e in self.events:
            self.by_title.setdefault(e["title"], []).append(e)

    def test_meetings_cancellations_and_closures_are_dropped(self):
        self.assertEqual(sorted(self.by_title), ["44th Annual Great Italian Festival", "Biggest Little Ultra",
                                                 "Food Truck Wednesdays", "Ranger Walks", "Rec Swim Movie at the Pool"])

    def test_one_off_event(self):
        [e] = self.by_title["Ranger Walks"]
        self.assertEqual((e["start"], e["end"]), ("2026-10-10T14:00:00-07:00", "2026-10-10T15:00:00-07:00"))
        self.assertTrue(e["_family"])
        self.assertIn("youth", e["_tags"])
        self.assertEqual(e["_text"], "Guided walk for families")
        self.assertEqual(e["venue"]["name"], "Fisherman's Park")
        self.assertEqual(e["links"][0]["url"], "https://www.reno.gov/")

    def test_recurrences_expand_within_the_window(self):
        self.assertEqual([e["start"] for e in self.by_title["44th Annual Great Italian Festival"]],
                         ["2026-10-10T10:00:00-07:00", "2026-10-11T10:00:00-07:00"])
        self.assertEqual([e["end"] for e in self.by_title["44th Annual Great Italian Festival"]],
                         ["2026-10-10T20:00:00-07:00", "2026-10-11T20:00:00-07:00"])
        self.assertEqual([e["start"] for e in self.by_title["Food Truck Wednesdays"]], ["2026-10-07T16:00:00-07:00"])
        self.assertEqual([e["start"] for e in self.by_title["Rec Swim Movie at the Pool"]], ["2026-10-11T13:00:00-07:00"])
        ids = [e["id"] for e in self.by_title["44th Annual Great Italian Festival"]]
        self.assertEqual(ids, ["reno:285-202610101000", "reno:285-202610111000"])

    def test_multi_day_all_day_event_and_url_in_location(self):
        [e] = self.by_title["Biggest Little Ultra"]
        self.assertTrue(e["allDay"])
        self.assertEqual((e["start"], e["end"]), ("2026-10-09T00:00:00-07:00", "2026-10-11T00:00:00-07:00"))
        self.assertEqual(e["venue"]["name"], "Sparks Marina Park")
        self.assertEqual(e["links"][0]["url"], "https://www.biggestlittleultra.com/")

    def test_recurrence_keeps_local_time_across_the_fall_back(self):
        item = {"id": 7, "title": "Sunday Skate", "start": "2026-10-18T14:30:00", "end": "2026-10-18T16:00:00",
                "duration": "01:30", "calendar_displays": ["5"], "location": "Idlewild Park",
                "rrule": "DTSTART:20261018T143000\nRRULE:FREQ=WEEKLY;BYDAY=SU"}
        got = RENO.parse([item], date(2026, 10, 25), date(2026, 11, 8))
        self.assertEqual([(e["start"], e["end"]) for e in got], [
            ("2026-10-25T14:30:00-07:00", "2026-10-25T16:00:00-07:00"),
            ("2026-11-01T14:30:00-08:00", "2026-11-01T16:00:00-08:00"),
            ("2026-11-08T14:30:00-08:00", "2026-11-08T16:00:00-08:00")])

    def test_area_from_the_real_address_shapes(self):
        def item(i, location):
            return {"id": i, "title": "Rolling Recreation", "start": "2026-10-10T09:00:00", "end": "2026-10-10T11:00:00",
                    "calendar_displays": ["8"], "location": location}
        got = RENO.parse([item(1, "Yori Park 2800 Yori Wy. Reno, Nevada 89502"),
                          item(2, "Reno Aces Baseball Stadium, 250 Evans Ave. Reno, Nevada 89501"),
                          item(3, "Tahoe Blue event Center 75 Hwy 50,&nbsp; Stateline, NV")],
                         date(2026, 10, 5), date(2026, 10, 12))
        self.assertEqual([(e["area"], e["drive"]) for e in got],
                         [("reno", None), ("reno", None), ("tahoe", "~70 min")])

    def test_fetch_checks_the_shape(self):
        ctx = Context(la(2026, 10, 5), la(2026, 10, 13))
        with mock.patch.object(net, "get_json", lambda url, **kw: fixture_json("revize.json")):
            self.assertEqual(len(RENO.fetch(ctx)), len(self.events))
        with mock.patch.object(net, "get_json", lambda url, **kw: {"error": "x"}):
            with self.assertRaises(SourceError):
                RENO.fetch(ctx)


if __name__ == "__main__":
    unittest.main()
