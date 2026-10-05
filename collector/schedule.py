"""Each hourly run decides whether to refresh and whether to send the digest
(spec: "Each run decides what to do")."""

from dataclasses import dataclass
from datetime import timedelta, timezone

REFRESH_EVERY = timedelta(hours=2, minutes=50)
DIGEST_FROM, DIGEST_UNTIL = 7, 11      # local hours: try from 07:00, give up after 10:59


@dataclass(frozen=True)
class Decision:
    refresh: bool
    digest: bool


def decide(now, last_refresh, digest_date, digest_enabled=True, force_digest=False):
    """now: aware Reno datetime. last_refresh: aware datetime or None.
    digest_date: 'YYYY-MM-DD' the digest was last sent, or None."""
    digest = force_digest or (digest_enabled and DIGEST_FROM <= now.hour < DIGEST_UNTIL
                              and digest_date != now.date().isoformat())
    # Subtract in UTC: two datetimes sharing the same ZoneInfo subtract by wall clock.
    stale = (last_refresh is None or
             now.astimezone(timezone.utc) - last_refresh.astimezone(timezone.utc) >= REFRESH_EVERY)
    return Decision(refresh=digest or stale, digest=digest)
