"""HTTP for the collector: our User-Agent, gzip, a timeout and one retry.

Errors name the host and path but never the query string (API keys live
there), and callers can pass `label` to hide the URL entirely (the Discord
webhook's token is in its path)."""

import gzip
import http.client
import json
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "reno-today/1.0 (+https://github.com/natanforestree/reno-today)"
TIMEOUT = 20
RETRY_PAUSE = 2.0


class FetchError(Exception):
    """A request that failed for good. `status` is the HTTP status, or None."""

    def __init__(self, where, message, status=None):
        super().__init__(f"{message} ({where})")
        self.status = status


def _where(url, label):
    if label:
        return label
    parts = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def request(url, *, data=None, headers=None, method=None, timeout=TIMEOUT, retries=1, label=None):
    """(status, body bytes). Network errors and 5xx are retried once; 4xx fail at once."""
    sent = {"User-Agent": UA, "Accept-Encoding": "gzip"}
    sent.update(headers or {})
    where = _where(url, label)
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=data, headers=sent, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as res:
                body = res.read()
                if res.headers.get("Content-Encoding") == "gzip":
                    body = gzip.decompress(body)
                return res.status, body
        except urllib.error.HTTPError as err:
            err.close()
            if err.code < 500 or attempt == retries:
                raise FetchError(where, f"HTTP {err.code}", err.code) from None
        except (urllib.error.URLError, http.client.HTTPException, TimeoutError, ConnectionError, OSError) as err:
            if attempt == retries:
                reason = getattr(err, "reason", None) or type(err).__name__
                raise FetchError(where, f"network error: {reason}") from None
        time.sleep(RETRY_PAUSE)
    raise AssertionError("unreachable")


def get_bytes(url, **kw):
    return request(url, **kw)[1]


def get_text(url, **kw):
    return get_bytes(url, **kw).decode("utf-8", errors="replace")


def get_json(url, **kw):
    body = get_bytes(url, **kw)
    try:
        return json.loads(body)
    except ValueError as err:
        raise FetchError(_where(url, kw.get("label")), f"bad JSON: {err}") from None


def post_json(url, payload, **kw):
    """POST a JSON body; returns the HTTP status (FetchError on 4xx/5xx)."""
    data = json.dumps(payload).encode("utf-8")
    return request(url, data=data, headers={"Content-Type": "application/json"},
                   method="POST", **kw)[0]
