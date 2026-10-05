"""Event sources. Each has NAME (status key), LABEL (shown on the page) and
fetch(ctx) -> list of model.make_event dicts, raising net.FetchError or
sources.base.SourceError when it can't be read. Optional EVERY (timedelta):
collect.py reuses the last good result while it's younger than that."""

from sources import aces, unr, wolfpack

ALL = [unr, wolfpack, aces]
