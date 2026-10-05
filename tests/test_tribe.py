import os
import unittest
from unittest import mock

from helpers import fixture_json, fixture_path, la
import net
from sources.base import Context, SourceError
from sources.tribe import TribeSource, price_from

ITEMS = fixture_json("tribe.json")["events"]
DISCOVERY = TribeSource("discovery", "The Discovery", "https://nvdm.org", city="Reno",
                        place=("The Discovery", "490 S Center St, Reno, NV 89501"), family_all=True,
                        adult_categories={"adults-only"}, skip_categories={"members-only", "fundraiser"})
TAHOE = TribeSource("southtahoe", "Visit Lake Tahoe", "https://visitlaketahoe.com", city="South Lake Tahoe",
                    family_categories={"kids & families"}, family_before=17)


class TribeTest(unittest.TestCase):
    def test_skips_members_only(self):
        ids = [e["id"] for e in DISCOVERY.parse(ITEMS)]
        self.assertNotIn("discovery:12", ids)
        self.assertEqual(len(ids), 5)

    def test_discovery_events_are_family_and_adults_only_is_flagged(self):
        by_id = {e["id"]: e for e in DISCOVERY.parse(ITEMS)}
        e = by_id["discovery:11"]
        self.assertTrue(e["_family"])
        self.assertEqual(e["start"], "2026-10-07T09:00:00-07:00")
        self.assertEqual(e["venue"]["address"], "490 S. Center Street, Reno, NV, 89501")
        self.assertTrue(by_id["discovery:13"]["_adult"])
        self.assertEqual(by_id["discovery:13"]["price"], {"min": 25.0, "max": 35.0})

    def test_kids_category_counts_only_in_the_daytime(self):
        by_id = {e["id"]: e for e in TAHOE.parse(ITEMS)}
        self.assertFalse(by_id["southtahoe:14"]["_family"])          # 9 pm live music
        self.assertTrue(by_id["southtahoe:15"]["_family"])           # 10 am festival
        self.assertEqual(by_id["southtahoe:14"]["title"], "Live Music at Casey's")
        self.assertEqual(by_id["southtahoe:14"]["price"], {"free": True})
        self.assertEqual((by_id["southtahoe:14"]["area"], by_id["southtahoe:14"]["drive"]), ("tahoe", "~65 min"))
        self.assertIn("kids & families", by_id["southtahoe:15"]["_tags"])
        self.assertIn("festival", by_id["southtahoe:15"]["_tags"])

    def test_missing_venue_list_and_all_day_run(self):
        e = {e["id"]: e for e in TAHOE.parse(ITEMS)}["southtahoe:16"]
        self.assertIsNone(e["venue"])
        self.assertTrue(e["allDay"])
        self.assertEqual((e["start"], e["end"]), ("2026-10-10T00:00:00-07:00", "2026-10-11T00:00:00-07:00"))

    def test_price_from(self):
        self.assertIsNone(price_from(""))
        self.assertEqual(price_from("Free"), {"free": True})
        self.assertEqual(price_from("$10"), {"min": 10.0, "max": 10.0})
        self.assertEqual(price_from("$10 &#8211; $25.50"), {"min": 10.0, "max": 25.5})
        self.assertEqual(price_from("Free for kids, $5 adults"), {"min": 5.0, "max": 5.0})
        self.assertIsNone(price_from("Donations welcome"))

    def test_fetch_pages_and_shape_check(self):
        ctx = Context(la(2026, 10, 5), la(2026, 10, 13))
        urls = []

        def fake(url, **kw):
            urls.append(url)
            return {"events": ITEMS[:3] if "page=1" in url else ITEMS[3:], "total_pages": 2}

        with mock.patch.object(net, "get_json", fake):
            got = TAHOE.fetch(ctx)
        self.assertEqual(len(urls), 2)
        self.assertTrue(urls[0].startswith("https://visitlaketahoe.com/wp-json/tribe/events/v1/events?"))
        self.assertIn("start_date=2026-10-05&end_date=2026-10-12%2023:59:59", urls[0])
        self.assertEqual(len(got), 6)
        with mock.patch.object(net, "get_json", lambda url, **kw: {"code": "rest_no_route"}):
            with self.assertRaises(SourceError):
                TAHOE.fetch(ctx)

    def test_real_recording_parses(self):
        if not os.path.exists(fixture_path("real/nvdm.json")):
            self.skipTest("no real recording yet")
        events = DISCOVERY.parse(fixture_json("real/nvdm.json")["events"])
        self.assertTrue(events)
        self.assertTrue(all(e["area"] == "reno" for e in events))


if __name__ == "__main__":
    unittest.main()
