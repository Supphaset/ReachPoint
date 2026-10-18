"""Small, shared limits for the single judging instance."""

from __future__ import annotations

import ipaddress
import math
import threading
import time
from dataclasses import dataclass

from fastapi import HTTPException

WINDOW_S = 15 * 60   # longer caps are only against spam and runaway cost, so they reset every 15 minutes


def client_ip(request) -> str:
    first = request.headers.get("x-forwarded-for", "").split(",", 1)[0].strip()
    try:
        return str(ipaddress.ip_address(first))
    except ValueError:
        return request.client.host if request.client else "unknown"


def limited(seconds: int):
    return HTTPException(429, detail={"error": "rate_limited", "retryAfter": seconds},
                         headers={"Retry-After": str(seconds)})


@dataclass
class Bucket:
    tokens: float
    at: float
    expires: float


class Limits:
    def __init__(self, clock=time.monotonic, wall=time.time):
        self.clock, self.wall = clock, wall
        self.lock = threading.Lock()
        self.buckets = {}
        self.daily = {}
        self.calls = {}
        self.cleaned = 0.0

    def take(self, rules):
        """Check every bucket before spending any tokens."""
        now = self.clock()
        with self.lock:
            if now - self.cleaned >= 60:
                self.buckets = {k: b for k, b in self.buckets.items() if b.expires > now}
                day = int(self.wall() // WINDOW_S)
                self.daily = {k: v for k, v in self.daily.items() if v[0] == day}
                self.cleaned = now
            waiting, ready = 0, []
            for key, cap, seconds in rules:
                b = self.buckets.get(key, Bucket(cap, now, now + seconds))
                tokens = min(cap, b.tokens + (now - b.at) * cap / seconds)
                waiting = max(waiting, math.ceil((1 - tokens) * seconds / cap))
                ready.append((key, Bucket(tokens - 1, now, now + seconds)))
            if waiting > 0:
                return waiting
            for key, b in ready:
                self.buckets[key] = b
            return 0

    def day(self, key, cap):
        now = self.wall()
        day = int(now // WINDOW_S)
        with self.lock:
            self.daily = {k: v for k, v in self.daily.items() if v[0] == day}
            old_day, count = self.daily.get(key, (day, 0))
            count = count if old_day == day else 0
            if count >= cap:
                return max(1, math.ceil((day + 1) * WINDOW_S - now))
            self.daily[key] = (day, count + 1)
            return 0

    def voice(self, ip):
        with self.lock:
            if len(self.calls) >= 3 or ip in self.calls:
                return False
            self.calls[ip] = self.clock()
            return True

    def release(self, ip):
        with self.lock:
            self.calls.pop(ip, None)


limits = Limits()


def http_limit(method, path, ip, room, body, creating=False):
    rules = []
    if method == "GET":
        name, cap = "get", 600
    elif method == "POST":
        if path.endswith("/turn") and "/sessions/" in path:
            name, cap = "chat", 30
            sid = path.split("/sessions/", 1)[1].split("/", 1)[0]
            rules.append((("session", room, sid), 20, 60))
        elif path.endswith("/sessions"):
            name, cap = "sessions", 20
        elif path.endswith("/copilot"):
            name, cap = "copilot", 8
        elif path == "/api/demo/reset" or (path == "/api/v2/clock" and body.get("action") == "reset"):
            name, cap = "room", 10
        else:
            name, cap = "post", 120
    else:
        return 0
    rules += [((name, ip), cap, 60), ((name, ip, room), cap, 60)]
    if creating:
        rules.append((("room", ip), 10, 60))
    retry = limits.take(rules)
    if not retry and method == "POST" and path.endswith("/copilot"):
        retry = limits.day(("copilot", ip), 30)
    return retry
