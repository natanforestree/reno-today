import unittest
from datetime import date, datetime

import helpers  # noqa: F401
import rrule

OCT_FIRST, OCT_LAST = date(2026, 10, 5), date(2026, 10, 12)


def starts(spec, first=OCT_FIRST, last=OCT_LAST):
    return [d.strftime("%a %m-%d %H:%M") for d in rrule.expand(spec, first, last)]


class RruleTest(unittest.TestCase):
    def test_weekly_on_several_days(self):
        spec = "DTSTART:20260901T143000\nRRULE:FREQ=WEEKLY;INTERVAL=1;BYDAY=TU,WE;UNTIL=20261111T000000"
        self.assertEqual(starts(spec), ["Tue 10-06 14:30", "Wed 10-07 14:30"])

    def test_daily_until_is_an_inclusive_date(self):
        spec = "DTSTART:20261010T100000\nRDATE:20261010T100000\nRRULE:FREQ=DAILY;INTERVAL=1;UNTIL=20261011T000000"
        self.assertEqual(starts(spec), ["Sat 10-10 10:00", "Sun 10-11 10:00"])

    def test_exdate_removes_an_occurrence(self):
        spec = ("DTSTART:20261003T130000\nRRULE:FREQ=WEEKLY;INTERVAL=1;BYDAY=SU,SA;UNTIL=20261102T000000\n"
                "EXDATE:20261010T130000")
        self.assertEqual(starts(spec), ["Sun 10-11 13:00"])

    def test_no_until_runs_on(self):
        spec = "DTSTART:20260727T160040\nRRULE:FREQ=WEEKLY;INTERVAL=1;BYDAY=WE"
        self.assertEqual(starts(spec), ["Wed 10-07 16:00"])

    def test_every_other_week(self):
        spec = "DTSTART:20260902T090000\nRRULE:FREQ=WEEKLY;INTERVAL=2;BYDAY=WE"     # Sep 2, 16, 30, Oct 14
        self.assertEqual(starts(spec, date(2026, 9, 28), date(2026, 10, 18)), ["Wed 09-30 09:00", "Wed 10-14 09:00"])

    def test_monthly_by_setpos_and_ordinal(self):
        fourth_monday = "DTSTART:20260727T140000\nRRULE:FREQ=MONTHLY;INTERVAL=1;BYSETPOS=4;BYDAY=MO"
        self.assertEqual(starts(fourth_monday, date(2026, 10, 1), date(2026, 10, 31)), ["Mon 10-26 14:00"])
        second_saturday = "DTSTART:20260110T100000\nRRULE:FREQ=MONTHLY;BYDAY=2SA"
        self.assertEqual(starts(second_saturday, date(2026, 10, 1), date(2026, 10, 31)), ["Sat 10-10 10:00"])
        last_friday = "DTSTART:20260130T180000\nRRULE:FREQ=MONTHLY;BYDAY=-1FR"
        self.assertEqual(starts(last_friday, date(2026, 10, 1), date(2026, 10, 31)), ["Fri 10-30 18:00"])

    def test_count(self):
        spec = "DTSTART:20261001T090000\nRRULE:FREQ=DAILY;COUNT=7"                  # Oct 1–7
        self.assertEqual(starts(spec), ["Mon 10-05 09:00", "Tue 10-06 09:00", "Wed 10-07 09:00"])

    def test_plain_dtstart_and_bad_input(self):
        self.assertEqual(starts("DTSTART:20261008T120000"), ["Thu 10-08 12:00"])
        self.assertEqual(rrule.expand("nonsense", OCT_FIRST, OCT_LAST), [])

    def test_wall_clock_time_is_kept_across_the_fall_back(self):
        # DTSTART is in PDT; Nov 1 2026 is when clocks fall back. Occurrences stay at 14:30 local.
        spec = "DTSTART:20261018T143000\nRRULE:FREQ=WEEKLY;BYDAY=SU"
        got = rrule.expand(spec, date(2026, 10, 25), date(2026, 11, 15))
        self.assertEqual([d.strftime("%m-%d %H:%M") for d in got],
                         ["10-25 14:30", "11-01 14:30", "11-08 14:30", "11-15 14:30"])
        self.assertTrue(all(d.tzinfo is None for d in got))

    def test_parse(self):
        dtstart, rule, rdates, exdates = rrule.parse("DTSTART:20261003T130000\nRRULE:FREQ=WEEKLY;BYDAY=SA\nEXDATE:20261010T130000")
        self.assertEqual(dtstart, datetime(2026, 10, 3, 13, 0))
        self.assertEqual(rule, {"FREQ": "WEEKLY", "BYDAY": "SA"})
        self.assertEqual(exdates, [datetime(2026, 10, 10, 13, 0)])


if __name__ == "__main__":
    unittest.main()
