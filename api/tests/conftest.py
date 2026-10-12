"""Shared test setup: no test may call Gemini. AI-backed code is tested with stand-ins and stubs."""

import os

os.environ["REACHPOINT_AI"] = "off"
