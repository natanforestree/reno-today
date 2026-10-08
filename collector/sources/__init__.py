"""Event sources. Each has NAME (status key), LABEL (shown on the page) and
fetch(ctx) -> list of model.make_event dicts, raising net.FetchError or
sources.base.SourceError when it can't be read. Optional EVERY (timedelta):
collect.py reuses the last good result while it's younger than that."""

from sources import aces, library, standing, ticketmaster, tockify, unr, wolfpack
from sources.revize import RevizeSource
from sources.tribe import TribeSource

DISCOVERY = TribeSource("discovery", "The Discovery", "https://nvdm.org", city="Reno",
                        place=("The Discovery", "490 S Center St, Reno, NV 89501"), family_all=True,
                        adult_categories={"adults-only"}, skip_categories={"members-only", "fundraiser"})
CARSON = TribeSource("carson", "Visit Carson City", "https://visitcarsoncity.com", city="Carson City")
SOUTH_TAHOE = TribeSource("southtahoe", "Visit Lake Tahoe", "https://visitlaketahoe.com", city="South Lake Tahoe",
                          family_categories={"kids & families"}, family_before=17)
VIRGINIA_CITY = TribeSource("vcity", "Virginia City", "https://visitvirginiacitynv.com", city="Virginia City")
# A listing calendar (other people's events), so a ticket seller's or organiser's copy wins on merge.
# It files comedy under "Live music", so its music categories aren't used as tags.
DOWNTOWN = TribeSource("downtown", "Downtown Reno", "https://downtownreno.org", city="Reno", kind="listing",
                       ignore_categories={"live music", "music"})
HOLLAND = TribeSource("holland", "The Holland Project", "https://hollandreno.org", city="Reno",
                      all_ages_all=True)   # "Always all ages. All the time."

CITY_OF_RENO = RevizeSource("reno", "City of Reno", "www.reno.gov", "renonv", city="Reno",
                            page_url="https://www.reno.gov/calendar", skip_calendars={"3"}, kid_calendars={"8"},
                            calendar_names={"4": "events", "5": "parks & rec", "6": "aquatics", "7": "athletics",
                                            "8": "youth", "9": "special events"})
CITY_OF_SPARKS = RevizeSource("sparks", "City of Sparks", "www.sparksnv.gov", "sparksnv", city="Sparks",
                              page_url="https://www.sparksnv.gov/calendar", skip_calendars={"2", "5"},
                              calendar_names={"1": "community events"})

ALL = [ticketmaster, unr, wolfpack, aces, library, tockify, standing, DISCOVERY, CITY_OF_RENO, CITY_OF_SPARKS, CARSON,
       SOUTH_TAHOE, VIRGINIA_CITY, DOWNTOWN, HOLLAND]
