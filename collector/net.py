"""HTTP for the collector: our User-Agent, gzip, a timeout and one retry.
A JSON request that gets something else back (a bot check, a maintenance page)
is also asked again once, after a pause.

Errors name the host and path but never the query string (API keys live
there), and callers can pass `label` to hide the URL entirely (the Discord
webhook's token is in its path)."""

import gzip
import http.client
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib

UA = "reno-today/1.0 (+https://github.com/natanforestree/reno-today)"
TIMEOUT = 20
RETRY_PAUSE = 2.0
NOT_JSON_PAUSE = 5.0
BOT_CHECK = re.compile(rb"captcha|just a moment|challenge|are you a robot|cf-chl|access denied", re.I)


class FetchError(Exception):
    """A request that failed for good. `status` is the HTTP status, or None."""

    def __init__(self, where, message, status=None):
        super().__init__(f"{message} ({where})")
        self.status = status


HIDDEN = "address hidden"   # a malformed URL is never echoed: a secret may be in it


def _where(url, label):
    if label:
        return label
    try:
        parts = urllib.parse.urlsplit(url)
    except ValueError:
        return HIDDEN
    if not (parts.scheme and parts.netloc):
        return HIDDEN
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def request(url, **kw):
    """(status, body bytes). Network errors and 5xx are retried once; 4xx fail at once."""
    status, _, body = _request(url, **kw)
    return status, body


def _request(url, *, data=None, headers=None, method=None, timeout=TIMEOUT, retries=1, label=None):
    """(status, content type, body bytes) for request()."""
    sent = {"User-Agent": UA, "Accept-Encoding": "gzip"}
    sent.update(headers or {})
    where = _where(url, label)
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, data=data, headers=sent, method=method)
        except ValueError:              # "unknown url type: '<the whole URL>'"
            raise FetchError(label or HIDDEN, "invalid URL") from None
        try:
            with urllib.request.urlopen(req, timeout=timeout) as res:
                body = res.read()
                if res.headers.get("Content-Encoding") == "gzip":
                    body = gzip.decompress(body)
                return res.status, res.headers.get_content_type() if res.headers.get("Content-Type") else None, body
        except urllib.error.HTTPError as err:
            err.close()
            if err.code < 500 or attempt == retries:
                raise FetchError(where, f"HTTP {err.code}", err.code) from None
        except (EOFError, zlib.error, gzip.BadGzipFile):   # truncated or corrupt gzip body
            if attempt == retries:
                raise FetchError(where, "broken gzip body") from None
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


def _what(body):
    """What came back instead of JSON, in a few words; never the body itself (it may hold tokens)."""
    head = body[:20000].lstrip()
    if not head:
        return "an empty reply"
    if BOT_CHECK.search(head):
        return "a bot-check page"
    if head.startswith(b"<"):
        return "a web page"
    if head[:1] in (b"{", b"["):
        return "broken JSON"
    return "something else"


def get_json(url, **kw):
    retries = kw.get("retries", 1)
    for attempt in range(retries + 1):
        status, ctype, body = _request(url, **kw)
        try:
            return json.loads(body)
        except ValueError:
            if attempt == retries:
                raise FetchError(_where(url, kw.get("label")),
                                 f"not JSON: {_what(body)} (HTTP {status}, {ctype or 'no type'}, {len(body)} bytes)",
                                 status) from None
        time.sleep(NOT_JSON_PAUSE)
    raise AssertionError("unreachable")


def post_json(url, payload, **kw):
    """POST a JSON body; returns the HTTP status (FetchError on 4xx/5xx)."""
    data = json.dumps(payload).encode("utf-8")
    return request(url, data=data, headers={"Content-Type": "application/json"},
                   method="POST", **kw)[0]
