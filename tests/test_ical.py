import unittest
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import helpers  # noqa: F401
import ical

FEED = (
    "BEGIN:VCALENDAR\r\nVERSION:2.0\r\n"
    "BEGIN:VEVENT\r\nUID:a1\r\nDTSTART:20261010T013000Z\r\nDTEND:20261010T033000Z\r\n"
    "LOCATION:Reno\\, Nev.\\, Mackay Stadium\r\n"
    "SUMMARY:A very long title that is folded\r\n  across two lines\r\n"
    "DESCRIPTION:Line one\\nLine two\\; with semicolon\\\\done\r\nEND:VEVENT\r\n"
    "BEGIN:VEVENT\r\nUID:a2\r\nDTSTART;VALUE=DATE:20261102\r\nSUMMARY:All day\r\nEND:VEVENT\r\n"
    "BEGIN:VEVENT\r\nUID:a3\r\nDTSTART;TZID=America/New_York:20261010T100000\r\nSUMMARY:East\r\nEND:VEVENT\r\n"
    "BEGIN:VEVENT\r\nUID:a4\r\nDTSTART:20261010T100000\r\nSUMMARY:Floating\r\nEND:VEVENT\r\n"
    "BEGIN:VEVENT\r\nUID:a5\r\nDTSTART;TZID=Pacific Standard Time:20261010T100000\r\nSUMMARY:Windows\r\nEND:VEVENT\r\n"
    "BEGIN:VEVENT\r\nUID:a6\r\nDTSTART:2026-10-10\r\nSUMMARY:Broken date\r\nEND:VEVENT\r\n"
    'BEGIN:VEVENT\r\nUID:a7\r\nATTENDEE;CN="Doe: Jane":mailto:j@example.com\r\nDTSTART:20261010\r\nEND:VEVENT\r\n'
    "END:VCALENDAR\r\n"
)
LA = ZoneInfo("America/Los_Angeles")


class IcalTest(unittest.TestCase):
    def setUp(self):
        self.evs = list(ical.events(FEED))

    def test_finds_every_event(self):
        self.assertEqual([ical.text(e, "UID") for e in self.evs], ["a1", "a2", "a3", "a4", "a5", "a6", "a7"])

    def test_unfolds_and_unescapes_text(self):
        e = self.evs[0]
        self.assertEqual(ical.text(e, "SUMMARY"), "A very long title that is folded across two lines")
        self.assertEqual(ical.text(e, "LOCATION"), "Reno, Nev., Mackay Stadium")
        self.assertEqual(ical.text(e, "DESCRIPTION"), "Line one\nLine two; with semicolon\\done")
        self.assertEqual(ical.text(e, "NOPE"), "")

    def test_utc_times(self):
        self.assertEqual(ical.when(self.evs[0].get("DTSTART")), datetime(2026, 10, 10, 1, 30, tzinfo=timezone.utc))

    def test_dates(self):
        self.assertEqual(ical.when(self.evs[1].get("DTSTART")), date(2026, 11, 2))
        self.assertEqual(ical.when(self.evs[6].get("DTSTART")), date(2026, 10, 10))

    def test_tzid_times(self):
        self.assertEqual(ical.when(self.evs[2].get("DTSTART")),
                         datetime(2026, 10, 10, 10, 0, tzinfo=ZoneInfo("America/New_York")))

    def test_floating_and_unknown_zones_mean_reno_time(self):
        self.assertEqual(ical.when(self.evs[3].get("DTSTART")), datetime(2026, 10, 10, 10, 0, tzinfo=LA))
        self.assertEqual(ical.when(self.evs[4].get("DTSTART")), datetime(2026, 10, 10, 10, 0, tzinfo=LA))

    def test_bad_or_missing_values_are_none(self):
        self.assertIsNone(ical.when(self.evs[5].get("DTSTART")))
        self.assertIsNone(ical.when(None))

    def test_quoted_parameter_with_a_colon(self):
        params, value = self.evs[6]["ATTENDEE"]
        self.assertEqual(params["CN"], "Doe: Jane")
        self.assertEqual(value, "mailto:j@example.com")


if __name__ == "__main__":
    unittest.main()
