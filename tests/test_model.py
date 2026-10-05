import unittest
from datetime import date, datetime, timezone

from helpers import la
import model


class WindowTest(unittest.TestCase):
    def test_today_through_seven_days_ahead(self):
        start, end = model.window(la(2026, 10, 5, 8, 15))
        self.assertEqual(model.iso(start), "2026-10-05T00:00:00-07:00")
        self.assertEqual(model.iso(end), "2026-10-13T00:00:00-07:00")

    def test_window_across_the_dst_change_keeps_local_midnights(self):
        start, end = model.window(la(2026, 10, 28, 23, 59))
        self.assertEqual(model.iso(start), "2026-10-28T00:00:00-07:00")
        self.assertEqual(model.iso(end), "2026-11-05T00:00:00-08:00")

    def test_utc(self):
        self.assertEqual(model.utc(la(2026, 10, 10, 7, 30)), "2026-10-10T14:30:00Z")


class AreaTest(unittest.TestCase):
    def test_local_areas_have_no_drive(self):
        self.assertEqual(model.area_for("Reno"), "reno")
        self.assertEqual(model.area_for(" sparks "), "sparks")
        self.assertIsNone(model.drive_for("Reno", "reno"))

    def test_day_trips(self):
        self.assertEqual(model.area_for("Stateline"), "tahoe")
        self.assertEqual(model.drive_for("Stateline", "tahoe"), "~70 min")
        self.assertEqual(model.area_for("Carson City"), "carson")
        self.assertEqual(model.drive_for("Carson City", "carson"), "~35 min")
        self.assertEqual(model.area_for("Virginia City"), "virginia-city")

    def test_city_from_address(self):
        self.assertEqual(model.city_from_address("561 Crystal Park Road, Verdi, NV 89439"), "Verdi")
        self.assertEqual(model.city_from_address("1 Main St, South Lake Tahoe, CA"), "South Lake Tahoe")
        self.assertEqual(model.area_for(model.city_from_address("561 Crystal Park Road, Verdi, NV 89439")), "reno")
        self.assertIsNone(model.city_from_address("Idlewild Park"))
        self.assertEqual(model.city_from_address("Idlewild Park", "Reno"), "Reno")

    def test_unknown_city_is_other(self):
        self.assertEqual(model.area_for("Sacramento"), "other")
        self.assertEqual(model.area_for(None), "other")
        self.assertIsNone(model.drive_for("Sacramento", "other"))
        self.assertEqual(model.drive_for("Fernley", "other"), "~35 min")


class ValuesTest(unittest.TestCase):
    def test_plain_strips_tags_and_entities(self):
        self.assertEqual(model.plain("<p>Kids &amp; <b>families</b></p>\n welcome"),
                         "Kids & families welcome")

    def test_price_range(self):
        self.assertEqual(model.price_range(0, 0), {"free": True})
        self.assertEqual(model.price_range(25, 60), {"min": 25.0, "max": 60.0})
        self.assertEqual(model.price_range(25, None), {"min": 25.0, "max": 25.0})
        self.assertIsNone(model.price_range(None, None))

    def test_venue(self):
        self.assertEqual(model.venue("GSR", "2500 E 2nd St", "39.52321", "-119.7762"),
                         {"name": "GSR", "address": "2500 E 2nd St", "lat": 39.52321, "lon": -119.7762})
        self.assertIsNone(model.venue("", "  "))
        self.assertEqual(model.venue(None, "Reno, NV")["lat"], None)


class MakeEventTest(unittest.TestCase):
    def test_timed_event_is_written_in_reno_time(self):
        e = model.make_event("tm", "abc", "  Big   Show ", datetime(2026, 10, 11, 2, 30, tzinfo=timezone.utc),
                             city="Reno", url="https://example.com/x")
        self.assertEqual(e["id"], "tm:abc")
        self.assertEqual(e["title"], "Big Show")
        self.assertEqual(e["start"], "2026-10-10T19:30:00-07:00")
        self.assertIsNone(e["end"])
        self.assertFalse(e["allDay"])
        self.assertEqual(e["area"], "reno")
        self.assertEqual(e["links"], [{"source": "tm", "url": "https://example.com/x"}])
        self.assertEqual(e["tier"], "general")
        self.assertEqual(e["hints"], [])

    def test_all_day_uses_local_midnight(self):
        e = model.make_event("wolfpack", "1", "Game", date(2026, 11, 2), all_day=True, city="Reno")
        self.assertEqual(e["start"], "2026-11-02T00:00:00-08:00")
        self.assertTrue(e["allDay"])

    def test_end_before_start_is_dropped(self):
        e = model.make_event("x", "1", "T", la(2026, 10, 10, 12), end=la(2026, 10, 10, 11), city="Reno")
        self.assertIsNone(e["end"])

    def test_long_runs_are_ongoing(self):
        e = model.make_event("x", "1", "Exhibit", la(2026, 10, 1, 10), end=la(2026, 11, 20, 17), city="Reno")
        self.assertTrue(e["ongoing"])
        short = model.make_event("x", "2", "Fest", la(2026, 10, 9, 10), end=la(2026, 10, 11, 17), city="Reno")
        self.assertFalse(short["ongoing"])

    def test_only_http_links_are_kept(self):
        for bad in ("javascript:alert(1)", "data:text/html,hi", "", None, "ftp://x"):
            e = model.make_event("x", "1", "T", la(2026, 10, 10, 12), city="Reno", url=bad)
            self.assertEqual(e["links"], [], bad)

    def test_tags_are_lower_case_and_sorted(self):
        e = model.make_event("x", "1", "T", la(2026, 10, 10, 12), city="Reno", tags=["Family", " Music ", "", None])
        self.assertEqual(e["_tags"], ["family", "music"])

    def test_finalize_drops_private_fields(self):
        e = model.make_event("x", "1", "T", la(2026, 10, 10, 12), city="Reno", text="secret write-up")
        out = model.finalize(e)
        self.assertFalse([k for k in out if k.startswith("_")])
        self.assertNotIn("secret write-up", str(out))


class InWindowTest(unittest.TestCase):
    def setUp(self):
        self.start, self.end = model.window(la(2026, 10, 5, 9))

    def test_inside_and_outside(self):
        inside = model.make_event("x", "1", "T", la(2026, 10, 12, 20), city="Reno")
        before = model.make_event("x", "2", "T", la(2026, 10, 4, 20), city="Reno")
        after = model.make_event("x", "3", "T", la(2026, 10, 13, 0), city="Reno")
        self.assertTrue(model.in_window(inside, self.start, self.end))
        self.assertFalse(model.in_window(before, self.start, self.end))
        self.assertFalse(model.in_window(after, self.start, self.end))

    def test_exhibit_that_started_earlier_but_runs_through_today(self):
        e = model.make_event("x", "1", "Exhibit", la(2026, 8, 1, 10), end=la(2026, 11, 1, 17), city="Reno")
        self.assertTrue(model.in_window(e, self.start, self.end))


if __name__ == "__main__":
    unittest.main()
