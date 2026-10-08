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
        self.assertEqual(dedupe.tokens("Virginia St"), dedupe.tokens("Virginia Street"))

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



class SameShowTwoStylesTest(unittest.TestCase):
    """A district guide lists "Nekrogoblikon at Cargo Concert Hall" at doors time; Ticketmaster
    lists the band (and the support acts) at show time. Real listings from 2026-10-08."""

    def test_the_venue_in_a_title_still_matches(self):
        guide = ev("downtown", "1", "Nekrogoblikon at Cargo Concert Hall", la(2026, 10, 11, 18), "Cargo Concert Hall",
                   kind="listing")
        tm = ev("tm", "Z1", "Nekrogoblikon", la(2026, 10, 11, 18), "Cargo", kind="ticketing")
        self.assertTrue(dedupe.is_duplicate(guide, tm))

    def test_doors_and_show_times_at_one_venue_merge_and_the_ticket_seller_wins(self):
        guide = ev("downtown", "2", "Strangelove at Cargo Concert Hall", la(2026, 10, 10, 19), "Cargo Concert Hall",
                   kind="listing")
        tm = ev("tm", "Z2", "Strangelove: The Depeche Mode Experience with Asphalt Socialites and DJ Bobby G",
                la(2026, 10, 10, 20), "Cargo Concert Hall", kind="ticketing")
        [m] = dedupe.dedupe([guide, tm])
        self.assertEqual(m["title"], tm["title"])
        self.assertEqual(m["start"], "2026-10-10T20:00:00-07:00")
        self.assertEqual(len(m["links"]), 2)

    def test_different_shows_at_one_venue_stay_apart(self):
        a = ev("downtown", "11", "Buzz Kull + Kontravoid, Blood Rave", la(2026, 10, 13, 19), "The Holland Project",
               kind="listing")
        b = ev("tm", "Z3", "Dummy, Golomb", la(2026, 10, 13, 20), "The Holland Project", kind="ticketing")
        self.assertFalse(dedupe.is_duplicate(a, b))

    def test_more_than_90_minutes_apart_stays_apart(self):
        a = ev("downtown", "3", "Nekrogoblikon at Cargo Concert Hall", la(2026, 10, 11, 18), "Cargo Concert Hall",
               kind="listing")
        b = ev("tm", "Z4", "Nekrogoblikon", la(2026, 10, 11, 19, 31), "Cargo", kind="ticketing")
        self.assertFalse(dedupe.is_duplicate(a, b))

    def test_a_different_venue_stays_apart(self):
        a = ev("downtown", "4", "Strangelove at Cargo Concert Hall", la(2026, 10, 10, 19), "Cargo Concert Hall",
               kind="listing")
        b = ev("tm", "Z5", "Strangelove: The Depeche Mode Experience", la(2026, 10, 10, 20), "The Alpine",
               kind="ticketing")
        self.assertFalse(dedupe.is_duplicate(a, b))

    def test_only_a_listing_calendar_gets_the_looser_match(self):
        unr = ev("unr", "1", "Fall Concert", la(2026, 10, 10, 19), "Nightingale Concert Hall")
        tm = ev("tm", "Z6", "Fall Choir Showcase", la(2026, 10, 10, 20), "Nightingale Concert Hall", kind="ticketing")
        self.assertFalse(dedupe.is_duplicate(unr, tm))

    def test_annual_and_a_street_in_the_title_still_match(self):
        city = ev("reno", "1", "44th Annual Great Italian Festival", la(2026, 10, 10, 10), "Virginia St")
        guide = ev("downtown", "5", "Great Italian Festival: Virginia Street", la(2026, 10, 10, 10), kind="listing")
        self.assertTrue(dedupe.is_duplicate(city, guide))

    def test_a_vip_tent_ticket_is_its_own_listing(self):
        city = ev("reno", "1", "44th Annual Great Italian Festival", la(2026, 10, 10, 10), "Virginia St")
        tm = ev("tm", "Z7", "The Great Italian Festival VIP Tent Saturday 10AM - 2PM", la(2026, 10, 10, 10),
                "Eldorado Casino Reno", kind="ticketing")
        self.assertFalse(dedupe.is_duplicate(city, tm))

    def test_one_sources_own_listings_are_untouched(self):
        a = ev("library", "1", "Storytime", la(2026, 10, 10, 10), "Sparks Library")
        b = ev("library", "2", "Storytime", la(2026, 10, 10, 11), "Sparks Library")
        self.assertFalse(dedupe.is_duplicate(a, b))



class ListingLookalikeTest(unittest.TestCase):
    """A listing calendar's copy that's worded too differently to merge is dropped when it shares
    an unusual word with another calendar's event that day: a missing copy beats a duplicate."""

    def test_a_listing_lookalike_is_dropped(self):
        city = ev("reno", "1", "Reno Decompression 2026", la(2026, 10, 10, 17), "Venues in and around 4th Street")
        guide = ev("downtown", "6", "Burning Man Decompression Event: Brewery District", la(2026, 10, 10, 18),
                   kind="listing")
        self.assertEqual([e["id"] for e in dedupe.dedupe([city, guide])], ["reno:1"])

    def test_common_words_do_not_count(self):
        city = ev("reno", "2", "Halloween Carnival", la(2026, 10, 31, 16), "Idlewild Park")
        guide = ev("downtown", "7", "Halloween Pub Crawl", la(2026, 10, 31, 18), kind="listing")
        self.assertEqual(len(dedupe.dedupe([city, guide])), 2)

    def test_three_hours_apart_or_another_day_is_kept(self):
        city = ev("reno", "3", "Reno Decompression 2026", la(2026, 10, 10, 12), "Brewery District")
        late = ev("downtown", "8", "Decompression Afterparty", la(2026, 10, 10, 15, 1), kind="listing")
        nextday = ev("downtown", "9", "Decompression Brunch", la(2026, 10, 11, 12), kind="listing")
        self.assertEqual(len(dedupe.dedupe([city, late, nextday])), 3)

    def test_only_listing_copies_are_dropped(self):
        city = ev("reno", "4", "Reno Decompression 2026", la(2026, 10, 10, 17), "Brewery District")
        tm = ev("tm", "Z8", "Decompression Afterparty", la(2026, 10, 10, 18), "Cargo", kind="ticketing")
        self.assertEqual(len(dedupe.dedupe([city, tm])), 2)

    def test_a_listing_event_that_merged_is_kept(self):
        city = ev("reno", "5", "44th Annual Great Italian Festival", la(2026, 10, 10, 10), "Virginia St")
        guide = ev("downtown", "10", "Great Italian Festival: Virginia Street", la(2026, 10, 10, 10), kind="listing")
        tm = ev("tm", "Z9", "The Great Italian Festival VIP Tent Saturday 10AM - 2PM", la(2026, 10, 10, 10),
                "Eldorado Casino Reno", kind="ticketing")
        got = dedupe.dedupe([city, guide, tm])
        self.assertEqual(len(got), 2)
        self.assertEqual(sorted(l["source"] for l in got[0]["links"] + got[1]["links"]), ["downtown", "reno", "tm"])



CARGO = "255 North Virginia Street, Reno, NV"


def tm(sid, title, start, venue_name, address=CARGO, price=None, host="www.ticketmaster.com"):
    return model.make_event("tm", sid, title, start, venue=model.venue(venue_name, address), city="Reno",
                            kind="ticketing", price=price, url=f"https://{host}/event/{sid}")


class TicketRepeatTest(unittest.TestCase):
    """Ticketmaster lists some club shows twice, on ticketmaster.com and on TicketWeb, with a
    shorter title, another start time (doors vs show) and another venue name. Real pairs from 2026-10-08."""

    def test_ticketmaster_and_ticketweb_copies_merge_and_the_fuller_one_wins(self):
        short = tm("Z7r9jZ1A7Pt7f", "Nekrogoblikon", la(2026, 10, 11, 18), "Cargo")
        full = tm("rZ7HnEZ1AfFaf7", "Nekrogoblikon, Rivers of Nihil, Cyborg Octopus, Cyanate", la(2026, 10, 11, 19),
                  "Cargo Concert Hall", price={"min": 38.43, "max": 38.43}, host="www.ticketweb.com")
        [m] = dedupe.dedupe([short, full])
        self.assertEqual(m["title"], full["title"])
        self.assertEqual(m["start"], "2026-10-11T19:00:00-07:00")
        self.assertEqual(m["price"], {"min": 38.43, "max": 38.43})
        self.assertEqual([l["url"] for l in m["links"]], [full["links"][0]["url"]])   # one ticket link

    def test_same_time_copies_merge(self):
        a = tm("A1", "CLUB SLAYYY: SLAYYYTER + HYPERPOP NIGHT", la(2026, 10, 9, 21), "Cargo Concert Hall",
               host="www.ticketweb.com")
        b = tm("B1", "Club Slayyy", la(2026, 10, 9, 21), "Cargo")
        self.assertEqual(len(dedupe.dedupe([a, b])), 1)

    def test_early_and_late_shows_with_one_title_stay_apart(self):
        a = tm("C1", "Laugh Factory", la(2026, 10, 10, 19), "Laugh Factory", "407 N Virginia St, Reno, NV")
        b = tm("C2", "Laugh Factory", la(2026, 10, 10, 20, 30), "Laugh Factory", "407 N Virginia St, Reno, NV")
        self.assertEqual(len(dedupe.dedupe([a, b])), 2)

    def test_another_address_stays_apart(self):
        a = tm("D1", "The Rasmus", la(2026, 10, 7, 19), "Cargo")
        b = tm("D2", "The Rasmus, Saint Agnes, Death Valley Dreams", la(2026, 10, 7, 19), "The Alpine",
               "324 E 4th St, Reno, NV")
        self.assertEqual(len(dedupe.dedupe([a, b])), 2)

    def test_sessions_more_than_90_minutes_apart_stay_apart(self):
        a = tm("E1", "The Great Italian Festival VIP Tent Saturday", la(2026, 10, 10, 10), "Eldorado Casino Reno",
               "345 N Virginia St, Reno, NV")
        b = tm("E2", "The Great Italian Festival VIP Tent Saturday Afternoon", la(2026, 10, 10, 14, 30),
               "Eldorado Casino Reno", "345 N Virginia St, Reno, NV")
        self.assertEqual(len(dedupe.dedupe([a, b])), 2)

    def test_only_ticketmaster(self):
        def lib(sid, title, hh):
            return model.make_event("library", sid, title, la(2026, 10, 10, hh), city="Reno",
                                    venue=model.venue("Sparks Library", "1125 12th St, Sparks, NV"))
        self.assertEqual(len(dedupe.dedupe([lib("1", "Storytime", 10), lib("2", "Storytime Sing-Along", 11)])), 2)


if __name__ == "__main__":
    unittest.main()
