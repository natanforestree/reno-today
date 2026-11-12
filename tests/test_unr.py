import os
import unittest
from datetime import datetime
from unittest import mock

from helpers import fixture_json, fixture_path, la
import net
from sources import unr
from sources.base import Context, SourceError

CTX = Context(start=la(2026, 10, 5), end=la(2026, 10, 13))


class UnrParseTest(unittest.TestCase):
    def setUp(self):
        self.by_id = {e["id"]: e for e in unr.parse(fixture_json("unr.json")["events"])}

    def test_keeps_only_public_reno_listings(self):
        self.assertEqual(sorted(self.by_id), ["unr:103", "unr:104", "unr:107", "unr:109"])

    def test_exhibit_is_ongoing_on_campus(self):
        e = self.by_id["unr:103"]
        self.assertTrue(e["ongoing"])
        self.assertEqual(e["venue"]["name"], "Mathewson-IGT Knowledge Center")
        self.assertEqual(e["area"], "reno")
        self.assertEqual((e["start"], e["end"]), ("2026-10-06T08:00:00-07:00", "2026-10-06T17:00:00-07:00"))
        self.assertEqual(e["links"], [{"source": "unr", "url": "https://events.unr.edu/event/a-few-of-our-favorite-things"}])

    def test_prices(self):
        self.assertEqual(self.by_id["unr:104"]["price"], {"free": True})
        self.assertEqual(self.by_id["unr:107"]["price"], {"min": 5.0, "max": 5.0})
        self.assertIsNone(self.by_id["unr:103"]["price"])

    def test_all_day(self):
        e = self.by_id["unr:109"]
        self.assertTrue(e["allDay"])
        self.assertEqual(e["start"], "2026-10-09T00:00:00-07:00")
        self.assertEqual(e["venue"]["name"], "University of Nevada, Reno")

    def test_classification_inputs(self):
        e = self.by_id["unr:107"]
        self.assertIn("family engagement", e["_tags"])
        self.assertIn("kids and families", e["_text"])
        self.assertEqual((e["venue"]["lat"], e["venue"]["lon"]), (39.5466, -119.8175))
        self.assertEqual(e["_kind"], "organiser")


def _item(title, types=(), groups=(), topics=()):
    def names(xs):
        return [{"name": x} for x in xs]
    return {"event": {
        "id": 1, "title": title, "status": "live", "experience": "inperson", "geo": {"city": "Reno"},
        "groups": names(groups), "filters": {"event_types": names(types), "event_special_topics": names(topics)},
        "event_instances": [{"event_instance": {"id": 1, "start": "2026-11-13T12:00:00-08:00"}}]}}


class UnrCampusOnlyTest(unittest.TestCase):
    def kept(self, title, **labels):
        return bool(unr.parse([_item(title, **labels)]))

    def test_drops_listings_for_students_staff_and_doctors_in_training(self):
        for title, labels in [
            ("Dissertation Defense - A. Student", {"types": ["Lectures & Seminars"], "groups": ["The Graduate School"]}),
            ("Pediatric Grand Rounds", {"types": ["Lectures & Seminars"], "groups": ["Pediatrics"]}),
            ("Neonatal ventilator management", {"types": ["Lectures & Seminars"],
                                                "groups": ["SOM Pediatrics - Resident Training"]}),
            ("Faculty Senate Meeting", {"groups": ["Faculty Senate"]}),
            ("Designing for Engagement", {"groups": ["Teaching & Learning Technologies"]}),
            ("WebCampus Accessibility", {"topics": ["TLT: Accessibility"]}),
            ("Future Scholars Day - Nevada Bound", {"groups": ["Admissions"], "topics": ["Prospective Students"]}),
            ("NIH Funding Symposium", {"types": ["Conferences & Symposiums"]}),
            ("USAC Study Abroad Fair", {"types": ["Arts & Culture"], "groups": ["University Studies Abroad Consortium"]}),
            ("Life Skills Series", {"types": ["Social Events"], "groups": ["Student Services"]}),
        ]:
            with self.subTest(title=title):
                self.assertFalse(self.kept(title, **labels))

    def test_keeps_the_public_side_of_campus(self):
        for title, labels in [
            ("Symphony Orchestra", {"types": ["Arts & Culture"], "groups": ["School of Music"]}),
            ("Nevada Women's Volleyball vs. San José State", {"types": ["Athletics"]}),
            ("Discover Science: A Night with National Geographic", {"groups": ["College of Science"]}),
            ("Family Literacy Night", {"groups": ["College of Education and Human Development", "Community Outreach"]}),
            ("Energy Solutions Forum", {"types": ["Lectures & Seminars"], "groups": ["College of Science"]}),
            # A conference that's also listed as a public arts event isn't only for professionals.
            ("Basketry Symposium and Show", {"types": ["Conferences & Symposiums", "Arts & Culture"]}),
        ]:
            with self.subTest(title=title):
                self.assertTrue(self.kept(title, **labels))


class UnrFetchTest(unittest.TestCase):
    def test_follows_pages_with_the_window_dates(self):
        items = fixture_json("unr.json")["events"]
        pages = {1: {"events": items[:4], "page": {"current": 1, "total": 2}},
                 2: {"events": items[4:], "page": {"current": 2, "total": 2}}}
        urls = []

        def fake_get_json(url, **kw):
            urls.append(url)
            return pages[int(url.rsplit("page=", 1)[1])]

        with mock.patch.object(net, "get_json", fake_get_json):
            got = unr.fetch(CTX)
        self.assertEqual(len(urls), 2)
        self.assertIn("start=2026-10-05&end=2026-10-12", urls[0])
        self.assertEqual(len(got), 4)

    def test_a_reshaped_body_is_a_source_error(self):
        with mock.patch.object(net, "get_json", lambda url, **kw: {"error": "maintenance"}):
            with self.assertRaises(SourceError):
                unr.fetch(CTX)

    def test_real_recording_parses(self):
        if not os.path.exists(fixture_path("real/unr.json")):
            self.skipTest("no real recording yet")
        events = unr.parse(fixture_json("real/unr.json")["events"])
        self.assertTrue(events)
        for e in events:
            self.assertIn(e["area"], ("reno", "sparks"))
            self.assertTrue(e["title"])
            datetime.fromisoformat(e["start"])


if __name__ == "__main__":
    unittest.main()
