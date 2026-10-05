"""What every source shares."""

from dataclasses import dataclass, field
from datetime import datetime


class SourceError(Exception):
    """This source can't be read this run (unexpected response, not set up...)."""


@dataclass(frozen=True)
class Context:
    start: datetime                   # today 00:00, America/Los_Angeles
    end: datetime                     # start + 8 days (exclusive)
    env: dict = field(default_factory=dict)
