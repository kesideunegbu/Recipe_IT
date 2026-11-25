"""A small in-memory rate limiter (sliding windows, per key).

Used to cap how often each user can call Gemini, which protects the API
quota and bill. Counts live in this process's memory, so they reset when the
server restarts, and separate server processes would each keep their own
counts. That's fine for one Waitress process (threads share it); a
multi-process deployment would need a shared store such as Redis.
"""

import math
import threading
import time
from collections import deque

# Forget users with no recent hits once this many keys are tracked.
_SWEEP_AT = 1000


class RateLimiter:
    def __init__(self, rules, clock=time.monotonic):
        """rules: list of (max_hits, window_seconds), e.g. [(10, 60), (100, 86400)]."""
        if not rules or any(limit < 1 or window <= 0 for limit, window in rules):
            raise ValueError("Each rule needs at least 1 hit and a positive window.")
        self._rules = list(rules)
        self._longest = max(window for _, window in rules)
        self._clock = clock
        self._hits = {}  # key -> deque of hit times, oldest first
        self._lock = threading.Lock()

    def hit(self, key):
        """Record a hit for `key` if every rule allows it.

        Returns (True, 0) when allowed, or (False, seconds_to_wait) when not.
        A blocked attempt is not recorded, so waiting it out always works.
        """
        now = self._clock()
        with self._lock:
            hits = self._hits.setdefault(key, deque())
            while hits and hits[0] <= now - self._longest:
                hits.popleft()

            wait = 0.0
            for limit, window in self._rules:
                recent = [t for t in hits if t > now - window]
                if len(recent) >= limit:
                    # Allowed again once the oldest of the last `limit` hits
                    # leaves the window.
                    wait = max(wait, recent[-limit] + window - now)

            if wait > 0:
                return False, max(1, math.ceil(wait))

            hits.append(now)
            if len(self._hits) > _SWEEP_AT:
                self._sweep(now)
            return True, 0

    def _sweep(self, now):
        cutoff = now - self._longest
        for key in [k for k, q in self._hits.items() if not q or q[-1] <= cutoff]:
            del self._hits[key]
