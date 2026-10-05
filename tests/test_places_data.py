import json
import os
import re
import unittest
from datetime import date, timedelta

from helpers import ROOT
import places

AREAS = {"reno", "sparks", "tahoe", "carson", "virginia-city", "other"}
HOURS = re.compile(r"^(\d\d:\d\d-\d\d:\d\d|dawn-dusk)$")


class PlacesDataTest(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(ROOT, "places.json"), encoding="utf-8") as f:
            self.places = json.load(f)

    def test_shape(self):
        self.assertGreaterEqual(len(self.places), 12)
        names = set()
        for p in self.places:
            with self.subTest(place=p.get("name")):
                self.assertTrue(p["name"])
                self.assertNotIn(p["name"], names)
                names.add(p["name"])
                self.assertIn(p["area"], AREAS)
                self.assertIn(p["setting"], ("indoor", "outdoor", "both"))
                self.assertLessEqual(len(p["goodFor"]), 40)
                self.assertEqual(set(p["hours"]), set(places.WEEKDAYS))
                for h in p["hours"].values():
                    self.assertTrue(h is None or HOURS.match(h), h)
                self.assertTrue(p["months"] is None or all(1 <= m <= 12 for m in p["months"]))
                self.assertTrue(p["url"].startswith("https://"))
                self.assertIsInstance(p["free"], bool)
                self.assertRegex(p["checked"], r"^\d{4}-\d\d-\d\d$")

    def test_something_is_open_every_day_of_the_year(self):
        day = date(2026, 1, 1)
        while day.year == 2026:
            self.assertTrue(places.open_on(self.places, day.isoformat()), day)
            day += timedelta(days=1)


if __name__ == "__main__":
    unittest.main()
