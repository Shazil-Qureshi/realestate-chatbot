r"""
test_rate_limit.py - Task 3.5, unit tests for backend/ratelimit.py

No server, no API key and no network needed. Run from the project folder:

    pytest tests\test_rate_limit.py -v

Time is passed in by each test instead of really waiting, so a test of a
24-hour window finishes instantly and always gives the same answer.
"""

import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
import ratelimit  # noqa: E402

# Always reached through the module (ratelimit.RateLimited, not a name imported
# here): two tests below reload the module to try different settings, and a
# reload builds a NEW class object. A name imported once would still point at
# the old class, and `pytest.raises` would not recognise the new one.
SlidingWindow = ratelimit.SlidingWindow


@pytest.fixture(autouse=True)
def clean_counters():
    """Every test starts with empty counters."""
    ratelimit.reset_all()
    yield
    ratelimit.reset_all()


class FakeRequest:
    """Stands in for a FastAPI request: just headers and a client address."""

    class _Client:
        def __init__(self, host):
            self.host = host

    def __init__(self, headers=None, host="10.0.0.1"):
        self.headers = headers or {}
        self.client = self._Client(host) if host else None


# ---------------------------------------------------------------------------
# The counter itself
# ---------------------------------------------------------------------------


def test_RL_01_under_the_limit_is_allowed():
    """RL-01: requests below the limit all go through."""
    window = SlidingWindow(limit=3, period=60)
    for i in range(3):
        allowed, retry = window.check("visitor", now=1000.0 + i)
        assert allowed is True
        assert retry == 0


def test_RL_02_the_one_over_the_limit_is_refused():
    """RL-02: the fourth request of three is refused."""
    window = SlidingWindow(limit=3, period=60)
    for i in range(3):
        window.check("visitor", now=1000.0 + i)
    allowed, retry = window.check("visitor", now=1003.0)
    assert allowed is False
    assert retry >= 1


def test_RL_03_refusal_says_how_long_to_wait():
    """RL-03: the wait is the time until the oldest request leaves the window."""
    window = SlidingWindow(limit=2, period=60)
    window.check("visitor", now=1000.0)   # leaves the window at 1060
    window.check("visitor", now=1030.0)
    allowed, retry = window.check("visitor", now=1040.0)
    assert allowed is False
    # 1060 - 1040 = 20 seconds, rounded up.
    assert 20 <= retry <= 21


def test_RL_04_allowed_again_once_the_window_passes():
    """RL-04: the allowance comes back after the period."""
    window = SlidingWindow(limit=2, period=60)
    window.check("visitor", now=1000.0)
    window.check("visitor", now=1001.0)
    assert window.check("visitor", now=1002.0)[0] is False
    # 61 seconds after the first one, it has dropped out of the window.
    assert window.check("visitor", now=1061.0)[0] is True


def test_RL_05_visitors_are_counted_separately():
    """RL-05: one visitor using up their allowance does not block another."""
    window = SlidingWindow(limit=2, period=60)
    window.check("first", now=1000.0)
    window.check("first", now=1001.0)
    assert window.check("first", now=1002.0)[0] is False
    assert window.check("second", now=1002.0)[0] is True


def test_RL_06_a_refused_request_is_not_counted():
    """
    RL-06: hammering a closed door must not push the wait further out.

    If refusals were recorded, a visitor who kept retrying would never get
    back in.
    """
    window = SlidingWindow(limit=1, period=60)
    window.check("visitor", now=1000.0)
    for t in range(1001, 1030):
        window.check("visitor", now=float(t))
    # The single recorded request still leaves the window at 1060.
    assert window.check("visitor", now=1061.0)[0] is True


def test_RL_07_remaining_counts_down_without_recording():
    """RL-07: remaining() reports the allowance and changes nothing."""
    window = SlidingWindow(limit=3, period=60)
    assert window.remaining("visitor", now=1000.0) == 3
    window.check("visitor", now=1000.0)
    assert window.remaining("visitor", now=1000.0) == 2
    assert window.remaining("visitor", now=1000.0) == 2


def test_RL_08_tracked_keys_do_not_grow_without_limit():
    """RL-08: memory is bounded - the least recently used key is dropped."""
    window = SlidingWindow(limit=5, period=60, max_keys=50)
    for i in range(500):
        window.check(f"visitor-{i}", now=1000.0 + i)
    assert len(window._hits) <= 50


# ---------------------------------------------------------------------------
# The gates used by the endpoints
# ---------------------------------------------------------------------------


def test_RL_09_chat_refuses_after_the_per_minute_limit():
    """RL-09: a visitor asking too fast is refused with a clear message."""
    for i in range(ratelimit.CHAT_PER_MINUTE):
        ratelimit.check_chat("1.2.3.4", now=2000.0 + i)
    with pytest.raises(ratelimit.RateLimited) as caught:
        ratelimit.check_chat("1.2.3.4", now=2000.0 + ratelimit.CHAT_PER_MINUTE)
    assert "wait" in caught.value.message.lower()
    assert caught.value.retry_after >= 1


def test_RL_10_chat_refuses_after_the_per_day_limit():
    """RL-10: a visitor is stopped at the daily limit even if slowly paced."""
    # One request every 90 seconds never trips the per-minute gate.
    for i in range(ratelimit.CHAT_PER_DAY):
        ratelimit.check_chat("5.6.7.8", now=3000.0 + i * 90)
    with pytest.raises(ratelimit.RateLimited) as caught:
        ratelimit.check_chat("5.6.7.8", now=3000.0 + ratelimit.CHAT_PER_DAY * 90)
    assert "tomorrow" in caught.value.message.lower()


def test_RL_11_whole_service_cap_stops_a_brand_new_visitor():
    """
    RL-11: the gate that actually protects the Gemini quota.

    Spread over many addresses so no single visitor hits their own limit.
    A visitor never seen before is still refused once the demo's day is spent.
    """
    total = ratelimit.CHAT_TOTAL_PER_DAY
    for i in range(total):
        ratelimit.check_chat(f"9.9.{i // 250}.{i % 250}", now=4000.0 + i * 10)
    with pytest.raises(ratelimit.RateLimited) as caught:
        ratelimit.check_chat("200.200.200.200", now=4000.0 + total * 10)
    assert caught.value.message == ratelimit.BUSY_MESSAGE


def test_RL_12_lead_limit_is_separate_from_chat():
    """RL-12: using up the form allowance does not stop the visitor asking questions."""
    for i in range(ratelimit.LEAD_PER_MINUTE):
        ratelimit.check_lead("4.4.4.4", now=5000.0 + i)
    with pytest.raises(ratelimit.RateLimited):
        ratelimit.check_lead("4.4.4.4", now=5000.0 + ratelimit.LEAD_PER_MINUTE)
    # Chat is untouched.
    ratelimit.check_chat("4.4.4.4", now=5000.0 + ratelimit.LEAD_PER_MINUTE)


# ---------------------------------------------------------------------------
# Working out who is asking
# ---------------------------------------------------------------------------


def test_RL_13_visitor_is_read_from_the_forwarded_header():
    """RL-13: behind Render, the visitor is the first X-Forwarded-For entry."""
    request = FakeRequest(
        headers={"x-forwarded-for": "203.0.113.7, 10.1.1.1, 10.1.1.2"},
        host="10.0.0.1",
    )
    assert ratelimit.visitor_key(request) == "203.0.113.7"


def test_RL_14_falls_back_to_the_direct_address():
    """RL-14: with no proxy header, the connecting address is used."""
    assert ratelimit.visitor_key(FakeRequest(host="198.51.100.4")) == "198.51.100.4"


def test_RL_15_unknown_when_there_is_no_address_at_all():
    """RL-15: a request with neither is counted under one shared key, not crashed."""
    assert ratelimit.visitor_key(FakeRequest(host=None)) == "unknown"


def test_RL_16_blank_forwarded_header_is_ignored():
    """RL-16: an empty header must not become the key."""
    request = FakeRequest(headers={"x-forwarded-for": "   "}, host="198.51.100.9")
    assert ratelimit.visitor_key(request) == "198.51.100.9"


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


def test_RL_17_limits_can_be_turned_off(monkeypatch):
    """RL-17: RATE_LIMIT_ENABLED=false lets everything through."""
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    reloaded = importlib.reload(ratelimit)
    try:
        assert reloaded.ENABLED is False
        for i in range(reloaded.CHAT_PER_MINUTE * 3):
            reloaded.check_chat("7.7.7.7", now=6000.0 + i)
    finally:
        monkeypatch.delenv("RATE_LIMIT_ENABLED", raising=False)
        importlib.reload(ratelimit)


def test_RL_18_limits_can_be_changed_by_environment(monkeypatch):
    """RL-18: a number from the environment replaces the default."""
    monkeypatch.setenv("RATE_CHAT_PER_MINUTE", "2")
    reloaded = importlib.reload(ratelimit)
    try:
        assert reloaded.CHAT_PER_MINUTE == 2
        reloaded.check_chat("8.8.8.8", now=7000.0)
        reloaded.check_chat("8.8.8.8", now=7001.0)
        with pytest.raises(reloaded.RateLimited):
            reloaded.check_chat("8.8.8.8", now=7002.0)
    finally:
        monkeypatch.delenv("RATE_CHAT_PER_MINUTE", raising=False)
        importlib.reload(ratelimit)


def test_RL_19_a_nonsense_setting_falls_back_to_the_default(monkeypatch):
    """RL-19: a typo in an environment variable must not disable the limit."""
    monkeypatch.setenv("RATE_CHAT_PER_MINUTE", "ten")
    monkeypatch.setenv("RATE_CHAT_PER_DAY", "-5")
    reloaded = importlib.reload(ratelimit)
    try:
        assert reloaded.CHAT_PER_MINUTE == 10
        assert reloaded.CHAT_PER_DAY == 100
    finally:
        monkeypatch.delenv("RATE_CHAT_PER_MINUTE", raising=False)
        monkeypatch.delenv("RATE_CHAT_PER_DAY", raising=False)
        importlib.reload(ratelimit)


# ---------------------------------------------------------------------------
# Requests from the same machine
# ---------------------------------------------------------------------------


def test_RL_20_local_requests_are_not_limited():
    """
    RL-20: the test suite and local development are not rate limited.

    test_chat.py sends 13 questions in well under a minute, which is more than
    the public per-minute limit. Without this they would fail for the wrong
    reason.
    """
    for i in range(ratelimit.CHAT_PER_MINUTE * 3):
        ratelimit.check_chat("127.0.0.1", now=8000.0 + i)
    for i in range(ratelimit.LEAD_PER_MINUTE * 3):
        ratelimit.check_lead("::1", now=8000.0 + i)


def test_RL_21_local_requests_do_not_use_up_the_whole_service_cap():
    """RL-21: a local run must not eat the daily allowance meant for visitors."""
    for i in range(50):
        ratelimit.check_chat("127.0.0.1", now=9000.0 + i)
    # A real visitor still has the full whole-service allowance.
    assert ratelimit._chat_total_day.remaining(
        ratelimit.GLOBAL_KEY, now=9100.0
    ) == ratelimit.CHAT_TOTAL_PER_DAY


def test_RL_22_an_outside_address_is_still_limited():
    """RL-22: the exemption must apply to loopback only."""
    for i in range(ratelimit.CHAT_PER_MINUTE):
        ratelimit.check_chat("203.0.113.9", now=9500.0 + i)
    with pytest.raises(ratelimit.RateLimited):
        ratelimit.check_chat("203.0.113.9", now=9500.0 + ratelimit.CHAT_PER_MINUTE)
