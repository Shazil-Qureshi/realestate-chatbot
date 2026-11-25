"""
Rate limiting for the public demo (Task 3.5, NFR-04, AC-9).

Why this exists
---------------
The backend is public. Every /chat question costs two Gemini calls: one to
embed the question and one to write the answer. The free tier has a daily
quota, and Google does not publish the numbers (they are shown per account in
AI Studio), so this module does not try to match them. It sets its own
conservative caps instead:

  * a per-visitor limit, so one person cannot flood the demo, and
  * a whole-service daily limit, so the Gemini quota cannot be drained even if
    many visitors arrive at once.

Everything here is Python's standard library. No new package, so the Docker
image and requirements.lock.txt are unchanged.

How the counting works
----------------------
A "sliding window" counter. For each key (a visitor, or the whole service) we
keep the times of recent requests. To check a limit of N per P seconds we drop
every time older than P seconds and count what is left. If that is already N,
the request is refused and we can say exactly how long until the oldest one
falls out of the window - that is the Retry-After value.

This is fairer than resetting at a fixed moment: a visitor who is refused at
10:59 does not get a full fresh allowance one second later.
"""

from __future__ import annotations

import os
import threading
import time
from collections import OrderedDict, deque

# ---------------------------------------------------------------------------
# Settings, all overridable with environment variables
# ---------------------------------------------------------------------------


def _setting(name: str, default: int) -> int:
    """Read a whole number from the environment, falling back to a default."""
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


MINUTE = 60
DAY = 24 * 60 * 60

# Per visitor. A person asking questions sends one every few seconds at most.
CHAT_PER_MINUTE = _setting("RATE_CHAT_PER_MINUTE", 10)
CHAT_PER_DAY = _setting("RATE_CHAT_PER_DAY", 100)

# Per visitor, for the demo contact form.
LEAD_PER_MINUTE = _setting("RATE_LEAD_PER_MINUTE", 5)
LEAD_PER_DAY = _setting("RATE_LEAD_PER_DAY", 20)

# The whole service, all visitors together. This is the one that protects the
# Gemini quota, and the one a spoofed address cannot get around.
CHAT_TOTAL_PER_DAY = _setting("RATE_CHAT_TOTAL_PER_DAY", 500)

# Stops the memory growing without limit if many addresses appear.
MAX_TRACKED_KEYS = _setting("RATE_MAX_TRACKED_KEYS", 10_000)

# Set RATE_LIMIT_ENABLED=false to turn the whole thing off (used by tests of
# other features, and for local development).
ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").strip().lower() not in {
    "false",
    "0",
    "no",
    "off",
}


# ---------------------------------------------------------------------------
# The counter
# ---------------------------------------------------------------------------


class SlidingWindow:
    """
    Counts how many times each key was seen inside the last `period` seconds.

    Safe to call from several requests at once: every change is made while
    holding a lock, because uvicorn runs endpoints in a thread pool.
    """

    def __init__(self, limit: int, period: int, max_keys: int = MAX_TRACKED_KEYS):
        self.limit = limit
        self.period = period
        self.max_keys = max_keys
        self._hits: OrderedDict[str, deque[float]] = OrderedDict()
        self._lock = threading.Lock()

    def _prune(self, times: deque[float], now: float) -> None:
        cutoff = now - self.period
        while times and times[0] <= cutoff:
            times.popleft()

    def check(self, key: str, now: float | None = None) -> tuple[bool, int]:
        """
        Record one request against `key` and say whether it is allowed.

        Returns (allowed, retry_after_seconds). retry_after_seconds is 0 when
        the request is allowed. Nothing is recorded when a request is refused,
        so hammering a closed door does not extend the wait.
        """
        now = time.monotonic() if now is None else now
        with self._lock:
            times = self._hits.get(key)
            if times is None:
                times = deque()
                self._hits[key] = times
                # Forget the least recently used key if we are tracking too many.
                while len(self._hits) > self.max_keys:
                    self._hits.popitem(last=False)
            else:
                self._hits.move_to_end(key)

            self._prune(times, now)

            if len(times) >= self.limit:
                # The oldest request leaves the window at times[0] + period.
                wait = (times[0] + self.period) - now
                return False, max(1, int(wait) + 1)

            times.append(now)
            return True, 0

    def remaining(self, key: str, now: float | None = None) -> int:
        """How many requests `key` has left. Does not record anything."""
        now = time.monotonic() if now is None else now
        with self._lock:
            times = self._hits.get(key)
            if times is None:
                return self.limit
            self._prune(times, now)
            return max(0, self.limit - len(times))

    def reset(self) -> None:
        """Forget everything. Used by the tests."""
        with self._lock:
            self._hits.clear()


# ---------------------------------------------------------------------------
# The gates each endpoint goes through
# ---------------------------------------------------------------------------

GLOBAL_KEY = "*all*"

_chat_minute = SlidingWindow(CHAT_PER_MINUTE, MINUTE)
_chat_day = SlidingWindow(CHAT_PER_DAY, DAY)
_chat_total_day = SlidingWindow(CHAT_TOTAL_PER_DAY, DAY)
_lead_minute = SlidingWindow(LEAD_PER_MINUTE, MINUTE)
_lead_day = SlidingWindow(LEAD_PER_DAY, DAY)

# What the visitor is told. Plain language, no jargon, and it always says what
# to do next (AC-9).
BUSY_MESSAGE = (
    "This free demo has answered as many questions as it can today. "
    "Please try again tomorrow."
)
TOO_FAST_MESSAGE = (
    "Too many questions too quickly. Please wait {seconds} seconds and try again."
)
LEAD_TOO_FAST_MESSAGE = (
    "Too many form submissions. Please wait {seconds} seconds and try again."
)


# Requests from the same machine (the test suite, local development, the
# "python backend\\main.py" run) are not counted. On Render a real visitor never
# looks like this: Render always puts the visitor's address in
# X-Forwarded-For, so loopback means the request came from inside. This keeps
# the local test suite working without lowering the public limits. It is not a
# hole an outsider can use any more than faking any other address is, and the
# whole-service gate below still counts every single request either way.
LOOPBACK = {"127.0.0.1", "::1", "localhost", "testclient"}


def is_local(visitor: str) -> bool:
    return visitor in LOOPBACK


class RateLimited(Exception):
    """Raised when a request must be refused. Carries what to tell the visitor."""

    def __init__(self, message: str, retry_after: int):
        super().__init__(message)
        self.message = message
        self.retry_after = retry_after


def check_chat(visitor: str, now: float | None = None) -> None:
    """Let one /chat request through, or raise RateLimited."""
    if not ENABLED or is_local(visitor):
        return

    # The whole-service gate first: if the demo's day is spent, the visitor's
    # own allowance does not matter, and we should not spend it on a refusal.
    allowed, retry = _chat_total_day.check(GLOBAL_KEY, now)
    if not allowed:
        raise RateLimited(BUSY_MESSAGE, retry)

    allowed, retry = _chat_minute.check(visitor, now)
    if not allowed:
        raise RateLimited(TOO_FAST_MESSAGE.format(seconds=retry), retry)

    allowed, retry = _chat_day.check(visitor, now)
    if not allowed:
        raise RateLimited(
            "You have reached this demo's daily limit of "
            f"{CHAT_PER_DAY} questions. Please try again tomorrow.",
            retry,
        )


def check_lead(visitor: str, now: float | None = None) -> None:
    """Let one /lead request through, or raise RateLimited."""
    if not ENABLED or is_local(visitor):
        return

    allowed, retry = _lead_minute.check(visitor, now)
    if not allowed:
        raise RateLimited(LEAD_TOO_FAST_MESSAGE.format(seconds=retry), retry)

    allowed, retry = _lead_day.check(visitor, now)
    if not allowed:
        raise RateLimited(
            "This demo accepts a limited number of form submissions per day. "
            "Please try again tomorrow.",
            retry,
        )


def visitor_key(request) -> str:
    """
    Work out who is asking.

    Render sits in front of the app, so request.client.host is Render's own
    address and would make every visitor look like one person. The visitor's
    address is the first entry of the X-Forwarded-For header, which Render
    sets.

    Caveat, written down on purpose: the app cannot prove that header is
    genuine, so someone could change it to look like many visitors. That is
    why CHAT_TOTAL_PER_DAY exists - the whole-service gate counts every
    request no matter what address it claims.
    """
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        first = forwarded.split(",")[0].strip()
        if first:
            return first
    client = getattr(request, "client", None)
    return getattr(client, "host", None) or "unknown"


def settings_summary() -> dict:
    """What /health reports, so the live limits can be checked without guessing."""
    return {
        "enabled": ENABLED,
        "chat_per_minute": CHAT_PER_MINUTE,
        "chat_per_day": CHAT_PER_DAY,
        "chat_total_per_day": CHAT_TOTAL_PER_DAY,
        "lead_per_minute": LEAD_PER_MINUTE,
        "lead_per_day": LEAD_PER_DAY,
    }


def reset_all() -> None:
    """Forget every counter. Used by the tests."""
    for window in (
        _chat_minute,
        _chat_day,
        _chat_total_day,
        _lead_minute,
        _lead_day,
    ):
        window.reset()
