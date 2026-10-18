"""Gemini reservations per 15-minute window, taken before model work starts.

The caps are only against spam and runaway cost, so they reset every 15 minutes and live in memory: a restart
starts a fresh window, which is fine for a cap this short, and no model call waits on a database.
"""

import os
import threading
import time

WINDOW_S = 15 * 60


class BudgetExceeded(RuntimeError):
    pass


def _caps():
    return (int(os.environ.get("RP_GEMINI_CALLS_15MIN", "400")),
            float(os.environ.get("RP_LIVE_MIN_15MIN", "45")))


class Usage:
    def __init__(self, clock=time.time):
        self.lock = threading.Lock()
        self.clock = clock
        self.data = {}

    def _window(self):
        return int(self.clock() // WINDOW_S)

    def _current(self):
        if self.data.get("window") != self._window():
            self.data = {"window": self._window(), "calls": 0, "liveMinutes": 0}
        return self.data

    def reserve(self, calls=1, minutes=0):
        with self.lock:
            d = self._current()
            cap, live_cap = _caps()
            if d["calls"] + calls > cap or d["liveMinutes"] + minutes > live_cap:
                raise BudgetExceeded("Gemini budget for this 15 minutes reached")
            d["calls"] += calls
            d["liveMinutes"] += minutes
            return d["window"]

    def finish_live(self, window, elapsed):
        # A call reserves its full 5 minutes up front; give back what it didn't use.
        with self.lock:
            d = self._current()
            if d["window"] == window:
                d["liveMinutes"] = max(0, d["liveMinutes"] - max(0, 5 - elapsed / 60))

    def status(self):
        with self.lock:
            d = self._current()
            cap, live_cap = _caps()
            return {"calls": d["calls"], "cap": cap, "capped": d["calls"] >= cap,
                    "liveMinutes": round(d["liveMinutes"], 1), "liveCap": live_cap,
                    "resetsInS": int((d["window"] + 1) * WINDOW_S - self.clock())}


usage = Usage()
