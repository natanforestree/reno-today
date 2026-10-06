import json
from unittest import mock
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from helpers import la
import classify
import digest
import model
import net

DAY = "2026-10-10"   # a Saturday


def ev(title, hh, mm=0, area_city="Reno", venue_name="Somewhere", free=False, day=10, **kw):
    e = model.make_event("x", f"{title}{hh}", title, la(2026, 10, day, hh, mm), city=area_city,
                         venue=model.venue(venue_name, "addr"), price=model.FREE if free else None, **kw)
    return model.finalize(classify.classify(e))


WX = {"date": DAY, "high": 78.4, "low": 63.6, "summary": "Clear", "emoji": "☀️"}
GUIDE = {"title": "2026 Ultimate Reno Halloween & Fall Guide: Haunted Houses", "shortTitle": "2026 Ultimate Reno Halloween & Fall Guide",
         "url": "https://www.lovingreno.com/x.html", "published": "2026-09-24"}
PLACES = [{"name": "The Discovery", "hours": {"sat": "10:00-17:00"}},
          {"name": "Idlewild Park", "hours": {"sat": "dawn-dusk"}},
          {"name": "Closed Place", "hours": {"sat": None}}]


class FormatTest(unittest.TestCase):
    def test_fmt_time(self):
        self.assertEqual(digest.fmt_time(ev("A", 10, 30)), "10:30am")
        self.assertEqual(digest.fmt_time(ev("A", 13, 5)), "1:05pm")
        self.assertEqual(digest.fmt_time(ev("A", 19)), "7pm")
        self.assertEqual(digest.fmt_time(ev("A", 0, 15)), "12:15am")
        self.assertEqual(digest.fmt_time(ev("A", 12)), "12pm")


class BuildTest(unittest.TestCase):
    def test_full_example(self):
        events = [
            ev("Baby & Toddler Storytime", 10, 30, venue_name="Downtown Reno Library", free=True),
            ev("Reno Aces vs Sacramento", 13, 5, venue_name="Greater Nevada Field"),
            ev("Lake Tahoe Oktoberfest", 11, area_city="Tahoe City", venue_name="Commons Beach"),
            ev("Tomorrow's Thing", 9, day=11),
        ]
        text = digest.build(DAY, events, WX, PLACES, GUIDE)
        self.assertEqual(text, "\n".join([
            "☀️ Saturday, Oct 10 · 64° → 78°, clear",
            "👶 For little ones",
            "• 10:30am Baby & Toddler Storytime · Downtown Reno Library · free",
            "🎟️ Also today",
            "• 1:05pm Reno Aces vs Sacramento · Greater Nevada Field",
            "🚗 Worth the drive",
            "• 11am Lake Tahoe Oktoberfest (Lake Tahoe, ~55 min)",
            "🏠 Always an option: The Discovery 10–5 · Idlewild Park",
            "📖 Loving Reno: 2026 Ultimate Reno Halloween & Fall Guide",
            "Full list → https://renotoday.org/",
        ]))

    def test_empty_sections_are_skipped_and_always_an_option_hides_with_3_little(self):
        little = [ev(f"Storytime {i}", 9 + i) for i in range(3)]
        text = digest.build(DAY, little, None, PLACES, None)
        self.assertTrue(text.startswith("📅 Saturday, Oct 10\n👶 For little ones\n"))
        self.assertNotIn("Also today", text)
        self.assertNotIn("Worth the drive", text)
        self.assertNotIn("Always an option", text)
        self.assertNotIn("Loving Reno", text)

    def test_nothing_today(self):
        text = digest.build(DAY, [], WX, [], None)
        self.assertIn("Nothing listed for today yet.", text)

    def test_also_today_prefers_free_all_ages_daytime_and_puts_21_plus_last(self):
        events = [ev("Club Night", 22, text="21+ only"), ev("Evening Concert", 19), ev("Free Day Fair", 11, free=True),
                  ev("Ballgame", 13, all_ages=True)]
        lines = digest.build(DAY, events, None, [], None).splitlines()
        also = [l for l in lines if l.startswith("•")]
        self.assertEqual([l.split(" ", 2)[2].split(" ·")[0] for l in also],
                         ["Free Day Fair", "Ballgame", "Evening Concert", "Club Night"])

    def test_at_most_five_per_section(self):
        events = [ev(f"Show {i}", 12 + (i % 8), i) for i in range(12)]
        text = digest.build(DAY, events, None, [], None)
        self.assertEqual(sum(1 for l in text.splitlines() if l.startswith("•")), 5)

    def test_visitor_line_sits_right_before_the_link(self):
        text = digest.build(DAY, [ev("Storytime", 10)], WX, PLACES, GUIDE, visitors=12)
        lines = text.splitlines()
        self.assertEqual(lines[-2:], ["👀 Yesterday: 12 visitors", f"Full list → {digest.PAGE_URL}"])

    def test_visitor_line_absent_without_a_count(self):
        self.assertNotIn("👀", digest.build(DAY, [ev("Storytime", 10)], WX, PLACES, GUIDE))
        self.assertNotIn("👀", digest.build(DAY, [ev("Storytime", 10)], WX, PLACES, GUIDE, visitors=None))

    def test_visitor_singular_plural_and_zero(self):
        for n, word in ((0, "visitors"), (1, "visitor"), (2, "visitors")):
            text = digest.build(DAY, [], WX, PLACES, GUIDE, visitors=n)
            self.assertIn(f"👀 Yesterday: {n} {word}\nFull list", text)

    def test_visitor_line_survives_trimming_within_2000(self):
        long = "Very " * 60
        events = ([ev(f"{long}{i}", 9 + i % 10, i) for i in range(15)]
                  + [ev(f"Storytime {long}{i}", 8, i) for i in range(15)]
                  + [ev(f"Tahoe {long}{i}", 9 + i % 10, i, area_city="Truckee") for i in range(15)])
        text = digest.build(DAY, events, WX, PLACES, GUIDE, visitors=123456)
        self.assertLessEqual(len(text), digest.LIMIT)
        self.assertTrue(text.endswith(f"👀 Yesterday: 123456 visitors\nFull list → {digest.PAGE_URL}"))

    def test_hard_trim_keeps_the_visitor_line(self):
        huge = "x" * 3000
        text = digest.build(DAY, [], WX, PLACES, {"title": huge, "shortTitle": huge}, visitors=5)
        self.assertLessEqual(len(text), digest.LIMIT)
        self.assertTrue(text.endswith(f"👀 Yesterday: 5 visitors\nFull list → {digest.PAGE_URL}"))

    def test_trimmed_to_2000_characters(self):
        long = "Very " * 60
        events = ([ev(f"{long}{i}", 9 + i % 10, i) for i in range(15)]
                  + [ev(f"Storytime {long}{i}", 8, i) for i in range(15)]
                  + [ev(f"Tahoe {long}{i}", 9 + i % 10, i, area_city="Truckee") for i in range(15)])
        text = digest.build(DAY, events, WX, PLACES, GUIDE)
        self.assertLessEqual(len(text), digest.LIMIT)
        self.assertLess(sum(1 for l in text.splitlines() if l.startswith("•")), 15, "sections were cut")
        self.assertTrue(text.endswith(digest.PAGE_URL), "the link survives trimming")

    def test_a_weekend_festival_is_in_each_days_digest_but_a_late_show_is_not(self):
        fest = model.finalize(classify.classify(model.make_event(
            "x", "f", "Great Italian Festival", la(2026, 10, 9).date(), end=la(2026, 10, 11).date(),
            all_day=True, city="Reno")))
        self.assertIn("Great Italian Festival", digest.build(DAY, [fest], None, [], None))
        late = ev("Late Show", 21)
        late["end"] = "2026-10-11T01:00:00-07:00"
        self.assertNotIn("Late Show", digest.build("2026-10-11", [late], None, [], None))

    def test_ongoing_events_are_left_out(self):
        exhibit = ev("Exhibit", 10)
        exhibit["ongoing"] = True
        self.assertNotIn("Exhibit", digest.build(DAY, [exhibit], None, [], None))


class Hook(BaseHTTPRequestHandler):
    status = 200
    received = None
    query = None

    def log_message(self, *a):
        pass

    def do_POST(self):
        Hook.query = self.path.split("?", 1)[1] if "?" in self.path else ""
        Hook.received = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        body = b"{}"
        self.send_response(Hook.status)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class PostTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Hook)
        cls.url = f"http://127.0.0.1:{cls.server.server_port}/api/webhooks/1/token"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        net.RETRY_PAUSE = 0

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_posts_plain_content_without_pings(self):
        Hook.status = 200
        self.assertTrue(digest.post(self.url, "hello @everyone"))
        self.assertEqual(Hook.received["content"], "hello @everyone")
        self.assertEqual(Hook.received["allowed_mentions"], {"parse": []})
        self.assertEqual(Hook.received["flags"], 4)
        self.assertEqual(Hook.query, "wait=true")

    def test_deleted_or_rate_limited_webhook_returns_false(self):
        for status in (404, 429):
            Hook.status = status
            self.assertFalse(digest.post(self.url, "hi"))

    def test_post_never_retries(self):
        with mock.patch.object(net, "post_json", return_value=204) as m:
            self.assertTrue(digest.post(self.url, "hi"))
        self.assertEqual(m.call_args.kwargs["retries"], 0)

    def test_no_webhook(self):
        self.assertFalse(digest.post("", "hi"))


if __name__ == "__main__":
    unittest.main()
