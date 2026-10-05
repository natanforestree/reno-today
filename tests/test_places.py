import unittest

import helpers  # noqa: F401
import places

DISCOVERY = {"name": "The Discovery", "hours": {"mon": None, "tue": "10:00-17:00", "wed": "10:00-20:00",
                                                "sat": "09:30-16:00", "sun": "12:00-17:00"}}
SPLASH = {"name": "Splash Pad", "months": [6, 7, 8], "hours": {d: "11:00-19:00" for d in places.WEEKDAYS}}
PARK = {"name": "Idlewild Park", "hours": {d: "dawn-dusk" for d in places.WEEKDAYS}}


class PlacesTest(unittest.TestCase):
    def test_hours_on_weekday(self):
        self.assertIsNone(places.hours_on(DISCOVERY, "2026-10-05"))           # Monday: closed
        self.assertEqual(places.hours_on(DISCOVERY, "2026-10-06"), "10:00-17:00")
        self.assertIsNone(places.hours_on(DISCOVERY, "2026-10-08"))           # Thursday: not listed

    def test_out_of_season(self):
        self.assertIsNone(places.hours_on(SPLASH, "2026-10-06"))
        self.assertEqual(places.hours_on(SPLASH, "2026-07-07"), "11:00-19:00")

    def test_open_on(self):
        self.assertEqual([p["name"] for p, _ in places.open_on([DISCOVERY, SPLASH, PARK], "2026-10-06")],
                         ["The Discovery", "Idlewild Park"])

    def test_short_hours(self):
        self.assertEqual(places.short_hours("10:00-17:00"), "10–5")
        self.assertEqual(places.short_hours("09:30-16:00"), "9:30–4")
        self.assertEqual(places.short_hours("12:00-17:00"), "12–5")
        self.assertEqual(places.short_hours("dawn-dusk"), "dawn–dusk")


if __name__ == "__main__":
    unittest.main()
