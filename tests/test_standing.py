import json
import os
import tempfile
import unittest
from datetime import date
from unittest import mock

from helpers import ROOT, la
from sources import standing
from sources.base import Context, SourceError


class StandingTest(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(ROOT, "standing.json"), encoding="utf-8") as f:
            self.entries = json.load(f)

    def test_weekly_and_nth_weekday(self):
        events = standing.occurrences(self.entries, date(2026, 10, 5), date(2026, 10, 12))
        self.assertEqual([(e["title"][:12], e["start"]) for e in events],
                         [("Riverside Fa", "2026-10-11T09:00:00-07:00"), ("Hands ON! Se", "2026-10-10T00:00:00-07:00")])
        market = events[0]
        self.assertEqual(market["end"], "2026-10-11T13:00:00-07:00")
        self.assertEqual(market["price"], {"free": True})
        self.assertTrue(market["_outdoor"] and market["_allAges"])
        self.assertEqual(market["id"], "standing:riverside-farmers-market-2026-10-11")
        self.assertTrue(events[1]["allDay"] and events[1]["_family"])

    def test_second_saturday_in_november(self):
        events = standing.occurrences(self.entries[1:], date(2026, 11, 1), date(2026, 11, 30))
        self.assertEqual([e["start"][:10] for e in events], ["2026-11-14"])

    def test_months_limit(self):
        summer = [dict(self.entries[0], months=[6, 7, 8])]
        self.assertEqual(standing.occurrences(summer, date(2026, 10, 1), date(2026, 10, 31)), [])

    def test_broken_file_is_a_source_error_and_missing_file_is_empty(self):
        ctx = Context(la(2026, 10, 5), la(2026, 10, 13))
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "standing.json")
            with mock.patch.object(standing, "PATH", path):
                self.assertEqual(standing.fetch(ctx), [])
                with open(path, "w") as f:
                    f.write("[{broken")
                with self.assertRaises(SourceError):
                    standing.fetch(ctx)


if __name__ == "__main__":
    unittest.main()
