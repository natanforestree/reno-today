import unittest
from unittest import mock

from helpers import fixture_text, la
import net
from sources import tockify
from sources.base import Context, SourceError


def page(boot):
    return f'<script>window.tkf = {{"version":"x","bootdata":{boot}}};</script>'


class TockifyTest(unittest.TestCase):
    def setUp(self):
        self.by_uid = {e["id"].split(":")[1].split("-")[0]: e for e in tockify.parse(fixture_text("tockify.html"))}

    def test_reads_page_data_once_per_event_and_skips_cancelled(self):
        self.assertEqual(sorted(self.by_uid), ["801", "802", "803", "805"])

    def test_event(self):
        e = self.by_uid["801"]
        self.assertEqual(e["title"], "Fall Photo Hike: Slide Mountain Trail")
        self.assertEqual((e["start"], e["end"]), ("2026-10-10T10:00:00-07:00", "2026-10-10T11:30:00-07:00"))
        self.assertEqual(e["price"], {"free": True})
        self.assertEqual(e["venue"]["name"], "Slide Mountain Trailhead")
        self.assertEqual(e["links"][0]["url"], "https://tockify.com/wcparks/detail/801/1791651600000")

    def test_free_parking_is_not_a_free_event_and_month_long_is_ongoing(self):
        e = self.by_uid["803"]
        self.assertIsNone(e["price"])
        self.assertTrue(e["ongoing"])

    def test_all_day_uses_the_local_date_and_washoe_valley_is_nearby(self):
        e = self.by_uid["805"]
        self.assertTrue(e["allDay"])
        self.assertEqual(e["start"], "2026-10-17T00:00:00-07:00")
        self.assertEqual((e["area"], e["drive"]), ("other", "~25 min"))

    def test_reshaped_calendar_data_is_a_source_error(self):
        for boot in ['null', '[1, 2]', '{}', '{"query": null}', '{"query": "x"}', '{"query": {}}',
                     '{"query": {"other": {"events": []}}}', '{"query": {"upcoming": []}}',
                     '{"query": {"upcoming": {"events": {}}}}', '{"query": {"pinboard": {"events": "x"}}}']:
            with self.subTest(boot=boot):
                with self.assertRaises(SourceError):
                    tockify.parse(page(boot))

    def test_an_empty_calendar_is_zero_events(self):
        self.assertEqual(tockify.parse(page('{"query": {"upcoming": {"events": []}}}')), [])
        self.assertEqual(tockify.parse(page('{"query": {"upcoming": {"events": []}, "pinboard": {}}}')), [])
        self.assertEqual(tockify.parse(page('{"query": {"upcoming": {"events": null}}}')), [])

    def test_page_without_data_is_a_source_error(self):
        with self.assertRaises(SourceError):
            tockify.parse("<html>new design</html>")
        with mock.patch.object(net, "get_text", lambda url, **kw: "<html>x</html>"):
            with self.assertRaises(SourceError):
                tockify.fetch(Context(la(2026, 10, 5), la(2026, 10, 13)))


if __name__ == "__main__":
    unittest.main()
