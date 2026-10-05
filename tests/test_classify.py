import json
import os
import tempfile
import unittest

from helpers import la
import classify
import model


def ev(title, hh=10, text="", venue_name=None, tags=(), **kw):
    v = model.venue(venue_name, "Reno, NV") if venue_name else None
    return model.make_event("x", title, title, la(2026, 10, 10, hh), venue=v, city="Reno",
                            text=text, tags=tags, **kw)


class TierTest(unittest.TestCase):
    CASES = [
        # (title, text, tags, flags, expected tier)
        ("Baby & Toddler Storytime", "", (), {}, "little"),
        ("Lapsit Rhymes", "", (), {}, "little"),
        ("Preschool Science Hour", "", (), {}, "little"),
        ("Sensory Play Morning", "", (), {}, "little"),
        ("Puppet Show: The Three Bears", "", (), {}, "little"),
        ("Family Day at the Museum", "", (), {}, "little"),
        ("Fall Festival", "Fun for kids and families of all ages.", (), {}, "little"),
        ("Disney On Ice", "", ("Family",), {}, "little"),
        ("Sesame Street Live", "", (), {"family": True}, "little"),
        ("Kid Rock", "", (), {}, "general"),                       # "kid" alone isn't "kids"
        ("Babyface Live", "", (), {}, "general"),                  # word boundary
        ("Chamber Orchestra", "An evening of Brahms.", (), {}, "general"),
        ("Family Feud Trivia Night", "21+ with ID.", (), {}, "general"),   # 21+ wins
        ("Kids Comedy Hour", "", (), {"adult": True}, "general"),          # age-enforced wins
    ]

    def test_cases(self):
        for title, text, tags, flags, tier in self.CASES:
            with self.subTest(title=title):
                self.assertEqual(classify.classify(ev(title, text=text, tags=tags, **flags))["tier"], tier)


class HintsTest(unittest.TestCase):
    def test_adult_words(self):
        for text in ("21+ only", "Ages 21 and over", "18+ show", "Bar crawl downtown", "Wine tasting flight",
                     "A burlesque revue"):
            with self.subTest(text=text):
                self.assertIn("21+", classify.classify(ev("Night Out", hh=20, text=text))["hints"])

    def test_bar_venues_are_21_plus(self):
        e = classify.classify(ev("DJ Night", hh=22, venue_name="The Loft Lounge"))
        self.assertIn("21+", e["hints"])
        self.assertNotIn("21+", classify.classify(ev("Concert", hh=20, venue_name="Bartley Ranch"))["hints"])

    def test_daytime_and_outdoors(self):
        e = classify.classify(ev("Farmers Market", hh=9, venue_name="Idlewild Park"))
        self.assertEqual(e["hints"], ["outdoors", "daytime"])
        self.assertEqual(classify.classify(ev("Concert", hh=19))["hints"], [])

    def test_all_day_counts_as_daytime(self):
        e = model.make_event("x", "1", "Expo", la(2026, 10, 10).date(), all_day=True, city="Reno")
        self.assertIn("daytime", classify.classify(e)["hints"])

    def test_all_ages_only_when_the_source_says_so_and_not_21(self):
        self.assertIn("all-ages", classify.classify(ev("Ballgame", all_ages=True))["hints"])
        self.assertNotIn("all-ages", classify.classify(ev("Ballgame", all_ages=True, adult=True))["hints"])

    def test_classify_does_not_mutate_its_input(self):
        e = ev("Storytime")
        classify.classify(e)
        self.assertEqual(e["tier"], "general")


class CuesTest(unittest.TestCase):
    def test_keeps_only_the_words_classify_looks_for(self):
        self.assertEqual(classify.cues("A gentle class for toddlers and their grown-ups. 21+ after 9pm."),
                         "toddlers 21+")
        self.assertEqual(classify.cues("Kids, kids, kids!"), "Kids kids")
        self.assertEqual(classify.cues("An evening of chamber music."), "")
        self.assertEqual(classify.cues(None), "")

    def test_classifying_from_cues_matches_classifying_from_the_text(self):
        for text in ("Songs and puppets for little ones", "Wine tasting, 21 and over", "Chamber music",
                     "Kids eat free before the bar crawl"):
            full = classify.classify(ev("Event", text=text))
            short = classify.classify(ev("Event", text=classify.cues(text)))
            self.assertEqual((full["tier"], full["hints"]), (short["tier"], short["hints"]), text)


class OverridesTest(unittest.TestCase):
    def setUp(self):
        self.events = [classify.classify(ev("Storytime at Sparks Library")),
                       classify.classify(ev("Trivia Night", hh=19)),
                       classify.classify(ev("Spam Event"))]

    def test_rules(self):
        rules = [{"match": "trivia", "addHint": "21+"},
                 {"match": "id:x:Spam Event", "hide": True},
                 {"match": "^storytime", "tier": "general"}]
        out = classify.apply_overrides(self.events, rules)
        self.assertEqual([e["title"] for e in out], ["Storytime at Sparks Library", "Trivia Night"])
        self.assertEqual(out[0]["tier"], "general")
        self.assertIn("21+", out[1]["hints"])
        self.assertEqual(self.events[0]["tier"], "little", "input untouched")

    def test_adding_21_plus_removes_little_and_all_ages(self):
        e = classify.classify(ev("Kids Disco", all_ages=True))
        out = classify.apply_overrides([e], [{"match": "disco", "addHint": "21+"}])[0]
        self.assertEqual(out["tier"], "general")
        self.assertNotIn("all-ages", out["hints"])

    def test_load_skips_broken_rules_and_tolerates_a_broken_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "overrides.json")
            with open(path, "w") as f:
                json.dump([{"match": "(unclosed"}, {"tier": "little"}, {"match": "ok", "hide": True}], f)
            self.assertEqual(classify.load_overrides(path), [{"match": "ok", "hide": True}])
            with open(path, "w") as f:
                f.write("{not json")
            self.assertEqual(classify.load_overrides(path), [])
            self.assertEqual(classify.load_overrides(os.path.join(d, "missing.json")), [])


if __name__ == "__main__":
    unittest.main()
