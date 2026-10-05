import json
import os
import tempfile
import unittest
from datetime import timedelta
from types import SimpleNamespace
from unittest import mock

from helpers import la
import collect
import guide
import model
import net
import weather
from sources.base import SourceError

NOW = la(2026, 10, 10, 7, 31)     # Saturday, digest time


def fake_source(name, events=None, error=None, every=None):
    def fetch(ctx):
        if error:
            raise error
        return [dict(e) for e in events or []]
    src = SimpleNamespace(NAME=name, LABEL=name.title(), fetch=mock.Mock(side_effect=fetch))
    if every:
        src.EVERY = every
    return src


def storytime(day=10):
    return model.make_event("lib", f"st{day}", "Baby Storytime", la(2026, 10, day, 10, 30), city="Reno",
                            venue=model.venue("Sparks Library", "1125 12th St"), price=model.FREE,
                            url="https://example.org/st", text="For babies and caregivers")


def concert():
    return model.make_event("tm", "c1", "Big Concert", la(2026, 10, 10, 20), city="Reno",
                            venue=model.venue("GSR", "2500 E 2nd St"), kind="ticketing")


WX = {"generatedAt": "x", "days": [{"date": "2026-10-10", "high": 70, "low": 50, "summary": "Clear", "emoji": "☀️",
                                    "nice": [], "hours": []}]}
GUIDE = {"title": "Fall Guide", "shortTitle": "Fall Guide", "url": "https://www.lovingreno.com/g.html",
         "published": "2026-09-24"}


class CollectTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.sent = []
        self.patches = [mock.patch.object(weather, "fetch", lambda now: WX),
                        mock.patch.object(guide, "fetch", lambda: GUIDE),
                        mock.patch.object(net, "get_text", lambda url, **kw: "")]
        for p in self.patches:
            p.start()
        with open(os.path.join(self.root, "places.json"), "w") as f:
            json.dump([{"name": "Idlewild Park", "hours": {"sat": "dawn-dusk"}}], f)

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def read(self, rel):
        with open(os.path.join(self.root, rel), encoding="utf-8") as f:
            return json.load(f)

    def post_ok(self, url, text):
        self.sent.append(text)
        return True

    def test_refresh_writes_every_file_and_sends_the_digest(self):
        env = {"DISCORD_WEBHOOK_URL": "https://discord.example/hook"}
        d = collect.run(self.root, NOW, env, srcs=[fake_source("lib", [storytime()]), fake_source("tm", [concert()])],
                        post=self.post_ok)
        self.assertTrue(d.refresh and d.digest)
        events = self.read("docs/data/events.json")
        self.assertEqual(events["generatedAt"], "2026-10-10T14:31:00Z")
        self.assertEqual([e["title"] for e in events["events"]], ["Baby Storytime", "Big Concert"])
        self.assertEqual(events["events"][0]["tier"], "little")
        self.assertFalse([k for e in events["events"] for k in e if k.startswith("_")], "no private fields")
        self.assertNotIn("For babies and caregivers", json.dumps(events), "no write-ups")
        status = self.read("docs/data/status.json")["sources"]
        self.assertEqual(status["lib"], {"label": "Lib", "ok": True, "count": 1,
                                         "lastSuccess": "2026-10-10T14:31:00Z", "error": None})
        self.assertTrue(status["weather"]["ok"] and status["lovingreno"]["ok"])
        self.assertEqual(self.read("docs/data/weather.json"), WX)
        self.assertEqual(self.read("docs/data/guide.json"), GUIDE)
        self.assertEqual(self.read("docs/data/places.json")[0]["name"], "Idlewild Park")
        self.assertEqual(self.read("state/digest.json"), {"date": "2026-10-10"})
        self.assertEqual(len(self.sent), 1)
        self.assertIn("Baby Storytime", self.sent[0])

    def test_next_hour_does_nothing(self):
        env = {"DISCORD_WEBHOOK_URL": "https://discord.example/hook"}
        src = fake_source("lib", [storytime()])
        collect.run(self.root, NOW, env, srcs=[src], post=self.post_ok)
        d = collect.run(self.root, NOW + timedelta(hours=1), env, srcs=[src], post=self.post_ok)
        self.assertFalse(d.refresh or d.digest)
        self.assertEqual(src.fetch.call_count, 1)
        self.assertEqual(len(self.sent), 1)

    def test_failed_post_keeps_data_and_retries_next_hour(self):
        env = {"DISCORD_WEBHOOK_URL": "https://discord.example/hook"}
        collect.run(self.root, NOW, env, srcs=[fake_source("lib", [storytime()])], post=lambda u, t: False)
        self.assertTrue(os.path.exists(os.path.join(self.root, "docs/data/events.json")))
        self.assertFalse(os.path.exists(os.path.join(self.root, "state/digest.json")))
        d = collect.run(self.root, NOW + timedelta(hours=1), env, srcs=[fake_source("lib", [storytime()])],
                        post=self.post_ok)
        self.assertTrue(d.digest)
        self.assertEqual(self.read("state/digest.json"), {"date": "2026-10-10"})

    def test_failing_source_keeps_its_last_good_events(self):
        collect.run(self.root, NOW, {}, srcs=[fake_source("lib", [storytime()])])
        later = NOW + timedelta(hours=3)
        collect.run(self.root, later, {}, srcs=[fake_source("lib", error=net.FetchError("lib", "HTTP 503", 503))])
        self.assertEqual([e["title"] for e in self.read("docs/data/events.json")["events"]], ["Baby Storytime"])
        status = self.read("docs/data/status.json")["sources"]["lib"]
        self.assertEqual((status["ok"], status["count"], status["error"]), (False, 1, "HTTP 503 (lib)"))
        self.assertEqual(status["lastSuccess"], "2026-10-10T14:31:00Z")

    def test_parser_crash_is_contained(self):
        collect.run(self.root, NOW, {}, srcs=[fake_source("bad", error=KeyError("boom")),
                                               fake_source("lib", [storytime()])])
        status = self.read("docs/data/status.json")["sources"]
        self.assertEqual(status["bad"]["error"], "collector error: KeyError")
        self.assertTrue(status["lib"]["ok"])

    def test_every_source_failing_keeps_the_previous_events_file(self):
        collect.run(self.root, NOW, {}, srcs=[fake_source("lib", [storytime()])])
        before = self.read("docs/data/events.json")
        much_later = NOW + timedelta(days=2)
        collect.run(self.root, much_later, {}, srcs=[fake_source("lib", error=SourceError("down"))])
        self.assertEqual(self.read("docs/data/events.json"), before)
        self.assertFalse(self.read("docs/data/status.json")["sources"]["lib"]["ok"])

    def test_weather_failure_keeps_the_previous_file(self):
        collect.run(self.root, NOW, {}, srcs=[])
        with mock.patch.object(weather, "fetch", mock.Mock(side_effect=net.FetchError("open-meteo", "HTTP 500", 500))):
            collect.run(self.root, NOW + timedelta(hours=3), {}, srcs=[])
        self.assertEqual(self.read("docs/data/weather.json"), WX)
        w = self.read("docs/data/status.json")["sources"]["weather"]
        self.assertEqual((w["ok"], w["lastSuccess"]), (False, "2026-10-10T14:31:00Z"))

    def test_window_filter_and_dedupe_and_overrides(self):
        with open(os.path.join(self.root, "overrides.json"), "w") as f:
            json.dump([{"match": "concert", "hide": True}], f)
        old = model.make_event("x", "old", "Last Week", la(2026, 10, 3, 10), city="Reno")
        dup = model.make_event("tm", "st", "Baby Storytime!", la(2026, 10, 10, 10, 30), city="Reno",
                               venue=model.venue("Sparks Library", "x"), kind="ticketing",
                               url="https://tm.example/st")
        collect.run(self.root, NOW, {}, srcs=[fake_source("lib", [storytime(), old]), fake_source("tm", [dup, concert()])])
        [e] = self.read("docs/data/events.json")["events"]
        self.assertEqual(e["id"], "lib:st10")
        self.assertEqual(len(e["links"]), 2)

    def test_every_reuses_a_fresh_result_without_fetching(self):
        src = fake_source("library", [storytime()], every=timedelta(hours=12))
        collect.run(self.root, NOW, {}, srcs=[src])
        collect.run(self.root, NOW + timedelta(hours=3), {}, srcs=[src])
        self.assertEqual(src.fetch.call_count, 1)
        self.assertTrue(self.read("docs/data/status.json")["sources"]["library"]["ok"])
        collect.run(self.root, NOW + timedelta(hours=13), {}, srcs=[src])
        self.assertEqual(src.fetch.call_count, 2)

    def test_last_good_keeps_keyword_cues_not_descriptions(self):
        sing = model.make_event("lib", "sing1", "Sing-Along", la(2026, 10, 10, 10, 30), city="Reno",
                                url="https://example.org/sing", text="Songs for toddlers and their grown-ups")
        collect.run(self.root, NOW, {}, srcs=[fake_source("lib", [sing])])
        with open(os.path.join(self.root, "state/sources/lib.json"), encoding="utf-8") as f:
            saved = f.read()
        self.assertNotIn("grown-ups", saved)
        self.assertIn("toddlers", saved)
        later = NOW + timedelta(hours=3)
        collect.run(self.root, later, {}, srcs=[fake_source("lib", error=net.FetchError("lib", "HTTP 503", 503))])
        self.assertEqual(self.read("docs/data/events.json")["events"][0]["tier"], "little")

    def test_force_digest(self):
        env = {"DISCORD_WEBHOOK_URL": "https://discord.example/hook", "FORCE_DIGEST": "true"}
        afternoon = la(2026, 10, 10, 15, 0)
        d = collect.run(self.root, afternoon, env, srcs=[fake_source("lib", [storytime()])], post=self.post_ok)
        self.assertTrue(d.digest)
        self.assertEqual(len(self.sent), 1)

    def test_loving_reno_badges_are_applied_before_writing(self):
        page = "<p>Join the Baby Storytime at Sparks Library every week.</p>"
        with mock.patch.object(net, "get_text", lambda url, **kw: page):
            collect.run(self.root, NOW, {}, srcs=[fake_source("lib", [storytime()])])
        [e] = self.read("docs/data/events.json")["events"]
        self.assertEqual(e["lovingReno"], {"title": "Fall Guide", "url": "https://www.lovingreno.com/g.html"})

    def test_guide_page_failure_does_not_stop_the_run(self):
        with mock.patch.object(net, "get_text", mock.Mock(side_effect=net.FetchError("x", "HTTP 500", 500))):
            collect.run(self.root, NOW, {}, srcs=[fake_source("lib", [storytime()])])
        self.assertIsNone(self.read("docs/data/events.json")["events"][0]["lovingReno"])

    def test_loving_reno_alone_does_not_count_as_a_working_source(self):
        collect.run(self.root, NOW, {}, srcs=[fake_source("lib", [storytime()])])
        before = self.read("docs/data/events.json")
        with mock.patch.object(net, "get_text", lambda url, **kw: ""):
            collect.run(self.root, NOW + timedelta(days=2), {}, srcs=[fake_source("lib", error=SourceError("down"))])
        self.assertEqual(self.read("docs/data/events.json"), before)


if __name__ == "__main__":
    unittest.main()
