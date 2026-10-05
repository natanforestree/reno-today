"""Shared test setup: puts collector/ on the import path, loads fixtures."""

import json
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "collector"))

LA = ZoneInfo("America/Los_Angeles")


def fixture_path(name):
    return os.path.join(HERE, "fixtures", name)


def fixture_text(name):
    with open(fixture_path(name), encoding="utf-8") as f:
        return f.read()


def fixture_json(name):
    return json.loads(fixture_text(name))


def la(y, m, d, hh=0, mm=0):
    """An aware America/Los_Angeles datetime."""
    return datetime(y, m, d, hh, mm, tzinfo=LA)
