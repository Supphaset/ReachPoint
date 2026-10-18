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


import pytest


@pytest.fixture(autouse=True)
def isolated_limits(monkeypatch):
    # Each test is a separate visitor run, with no paid work.
    from api.v2 import limits
    from api.ai import usage
    monkeypatch.setattr(limits, "limits", limits.Limits())
    monkeypatch.setattr(usage, "usage", usage.Usage())
