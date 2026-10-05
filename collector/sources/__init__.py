"""Event sources. Each has NAME (status key), LABEL (shown on the page) and
fetch(ctx) -> list of model.make_event dicts, raising net.FetchError or
sources.base.SourceError when it can't be read. Optional EVERY (timedelta):
collect.py reuses the last good result while it's younger than that."""

from sources import aces, library, ticketmaster, unr, wolfpack
from sources.tribe import TribeSource

DISCOVERY = TribeSource("discovery", "The Discovery", "https://nvdm.org", city="Reno",
                        place=("The Discovery", "490 S Center St, Reno, NV 89501"), family_all=True,
                        adult_categories={"adults-only"}, skip_categories={"members-only", "fundraiser"})
CARSON = TribeSource("carson", "Visit Carson City", "https://visitcarsoncity.com", city="Carson City")
SOUTH_TAHOE = TribeSource("southtahoe", "Visit Lake Tahoe", "https://visitlaketahoe.com", city="South Lake Tahoe",
                          family_categories={"kids & families"}, family_before=17)
VIRGINIA_CITY = TribeSource("vcity", "Virginia City", "https://visitvirginiacitynv.com", city="Virginia City")

ALL = [ticketmaster, unr, wolfpack, aces, library, DISCOVERY, CARSON, SOUTH_TAHOE, VIRGINIA_CITY]
