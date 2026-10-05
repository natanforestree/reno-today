import unittest
from datetime import date

from helpers import la
import dedupe
import model


def ev(source, sid, title, start, venue_name=None, kind="organiser", price=None, url=None, all_day=False, **kw):
    v = model.venue(venue_name, "Reno, NV") if venue_name else None
    return model.make_event(source, sid, title, start, venue=v, city="Reno", kind=kind, price=price,
                            url=url or f"https://{source}.example/{sid}", all_day=all_day, **kw)


class TokensTest(unittest.TestCase):
    def test_tokens_drop_filler_and_years(self):
        self.assertEqual(dedupe.tokens("The 2026 Reno Aces vs. the Sacramento River Cats — Live!"),
                         {"reno", "aces", "sacramento", "river", "cats"})

    def test_overlap_uses_the_shorter_title(self):
        a, b = dedupe.tokens("Reno Aces vs Sacramento River Cats"), dedupe.tokens("Reno Aces vs Sacramento")
        self.assertEqual(dedupe.overlap(a, b), 1.0)

    def test_one_word_titles_must_match_exactly(self):
        self.assertEqual(dedupe.overlap({"storytime"}, {"toddler", "storytime"}), 0.0)
        self.assertEqual(dedupe.overlap({"storytime"}, {"storytime"}), 1.0)


class DuplicateTest(unittest.TestCase):
    def test_same_show_from_two_sources_merges(self):
        unr = ev("unr", "1", "Wind Ensemble Fall Concert", la(2026, 10, 10, 19, 30), "Nightingale Concert Hall")
        tm = ev("tm", "Z1", "UNR Wind Ensemble: Fall Concert", la(2026, 10, 10, 19, 30), "Nightingale Hall",
                kind="ticketing", price={"min": 10.0, "max": 15.0})
        self.assertTrue(dedupe.is_duplicate(unr, tm))

    def test_start_times_more_than_30_minutes_apart_do_not_merge(self):
        a = ev("unr", "1", "Fall Concert", la(2026, 10, 10, 19, 0), "Hall")
        b = ev("tm", "2", "Fall Concert", la(2026, 10, 10, 19, 31), "Hall")
        self.assertFalse(dedupe.is_duplicate(a, b))

    def test_same_venue_allows_a_looser_title_match(self):
        a = ev("unr", "1", "Brahms Requiem Choir Orchestra", la(2026, 10, 10, 19), "Pioneer Center")
        b = ev("tm", "2", "Brahms Requiem Choir Reno Phil", la(2026, 10, 10, 19), "Pioneer Center for the Performing Arts")
        self.assertTrue(dedupe.is_duplicate(a, b))  # overlap 3/4 = 0.75: below 0.8, enough at the same venue
        c = ev("tm", "3", "Brahms Requiem Choir Reno Phil", la(2026, 10, 10, 19), "Grand Sierra Resort")
        self.assertFalse(dedupe.is_duplicate(a, c))

    def test_different_events_from_one_source_stay_apart(self):
        a = ev("library", "1", "Baby Storytime", la(2026, 10, 10, 10, 0), "Downtown Library")
        b = ev("library", "2", "Toddler Storytime", la(2026, 10, 10, 10, 30), "Downtown Library")
        self.assertFalse(dedupe.is_duplicate(a, b))

    def test_exact_repeat_from_one_source_merges(self):
        a = ev("tm", "1", "Comedy Night", la(2026, 10, 10, 20), "Silver Legacy", kind="ticketing")
        b = ev("tm", "2", "Comedy Night", la(2026, 10, 10, 20), "Silver Legacy", kind="ticketing")
        self.assertTrue(dedupe.is_duplicate(a, b))

    def test_one_source_at_different_branches_stays_apart(self):
        # Live 2026-10-06: Sparks's "Book a Librarian" was swallowed by Incline Village's.
        sparks = ev("library", "1", "Book a Librarian", la(2026, 10, 6, 10), "Sparks Library")
        incline = ev("library", "2", "Book a Librarian", la(2026, 10, 6, 10), "Incline Village Library")
        self.assertFalse(dedupe.is_duplicate(sparks, incline))
        north = ev("library", "3", "Book a Librarian", la(2026, 10, 7, 10), "North Valleys Library")
        south = ev("library", "4", "Book a Librarian", la(2026, 10, 7, 10), "South Valleys Library")
        self.assertFalse(dedupe.is_duplicate(north, south))

    def test_same_storytime_at_three_branches_is_three_events(self):
        branches = ["Sparks Library", "Downtown Reno Library", "Northwest Reno Library"]
        events = [ev("library", str(i), "Baby Story Time", la(2026, 10, 7, 10, 30), b) for i, b in enumerate(branches)]
        self.assertEqual(sorted(e["venue"]["name"] for e in dedupe.dedupe(events)), sorted(branches))

    def test_one_source_listing_with_and_without_a_venue_stays_apart(self):
        a = ev("library", "1", "Book Sale", la(2026, 10, 7, 10), "Sparks Library")
        b = ev("library", "2", "Book Sale", la(2026, 10, 7, 10))
        self.assertFalse(dedupe.is_duplicate(a, b))

    def test_generic_venue_words_do_not_make_the_same_venue(self):
        a = ev("unr", "1", "Brahms Requiem Choir Orchestra", la(2026, 10, 10, 19), "Pioneer Center")
        b = ev("tm", "2", "Brahms Requiem Choir Reno Phil", la(2026, 10, 10, 19), "Reno Events Center")
        self.assertFalse(dedupe.is_duplicate(a, b))  # only "center" in common
        c = ev("reno", "3", "Fall Family Fun Day", la(2026, 10, 10, 10), "Wingfield Park")
        d = ev("wcparks", "4", "Fall Family Picnic Day", la(2026, 10, 10, 10), "Idlewild Park")
        self.assertFalse(dedupe.is_duplicate(c, d))  # only "park" in common
        e = ev("wcparks", "5", "Fall Family Picnic Day", la(2026, 10, 10, 10), "Wingfield Park Amphitheater")
        self.assertTrue(dedupe.is_duplicate(c, e))   # overlap 3/4 at the same park

    def test_all_day_listing_matches_a_timed_one_on_the_same_day(self):
        wp = ev("wolfpack", "1", "Nevada Men's Basketball vs Idaho", date(2026, 11, 18), all_day=True)
        tm = ev("tm", "2", "Nevada Wolf Pack Men's Basketball vs. Idaho Vandals", la(2026, 11, 18, 19),
                "Lawlor Events Center", kind="ticketing")
        self.assertTrue(dedupe.is_duplicate(wp, tm))


class MergeTest(unittest.TestCase):
    def test_fields_come_from_the_most_specific_source(self):
        unr = ev("unr", "1", "Wind Ensemble Fall Concert", la(2026, 10, 10, 19, 30), "Nightingale Concert Hall",
                 text="Free parking.", tags=["Arts & Culture"])
        tm = ev("tm", "Z1", "UNR Wind Ensemble: Fall Concert", la(2026, 10, 10, 19, 0), "Nightingale Hall",
                kind="ticketing", price={"min": 10.0, "max": 15.0}, family=True)
        [m] = dedupe.dedupe([tm, unr])
        self.assertEqual(m["id"], "unr:1")
        self.assertEqual(m["title"], "Wind Ensemble Fall Concert")
        self.assertEqual(m["start"], "2026-10-10T19:30:00-07:00")      # organiser's time
        self.assertEqual(m["venue"]["name"], "Nightingale Concert Hall")
        self.assertEqual(m["price"], {"min": 10.0, "max": 15.0})         # ticketing's price
        self.assertEqual([l["source"] for l in m["links"]], ["unr", "tm"])
        self.assertTrue(m["_family"])
        self.assertEqual(m["_tags"], ["arts & culture"])

    def test_timed_listing_replaces_an_all_day_one(self):
        wp = ev("wolfpack", "1", "Nevada Men's Basketball vs Idaho", date(2026, 11, 18), all_day=True)
        tm = ev("tm", "2", "Nevada Wolf Pack Men's Basketball vs. Idaho Vandals", la(2026, 11, 18, 19),
                "Lawlor Events Center", kind="ticketing")
        [m] = dedupe.dedupe([wp, tm])
        self.assertFalse(m["allDay"])
        self.assertEqual(m["start"], "2026-11-18T19:00:00-08:00")
        self.assertEqual(m["venue"]["name"], "Lawlor Events Center")

    def test_unrelated_events_pass_through_in_order(self):
        a = ev("unr", "1", "Morning Talk", la(2026, 10, 10, 9))
        b = ev("tm", "2", "Evening Show", la(2026, 10, 10, 20), kind="ticketing")
        c = ev("aces", "3", "Ballgame", la(2026, 10, 11, 13))
        self.assertEqual([e["id"] for e in dedupe.dedupe([c, b, a])], ["unr:1", "tm:2", "aces:3"])


if __name__ == "__main__":
    unittest.main()
