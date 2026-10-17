"""Shared test setup: no test may call Gemini. AI-backed code is tested with stand-ins and stubs."""

import os

os.environ["REACHPOINT_AI"] = "off"

# Never discover developer credentials or read the private fallback file during
# collection/background warm-up. Individual model/route tests inject stand-ins.
from api.ai import gemini
from api.location import pinpoint


def _no_key():
    return None


def _no_credentials():
    return None, None


def _no_location_config(name):
    return None


gemini.api_key = _no_key
gemini._credentials = _no_credentials
pinpoint._config = _no_location_config
