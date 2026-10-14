"""Offline test suite."""

import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
# The supplied inputs are not published with the public repository: tests that read
# them are reported as skipped, never as passed, when the files are absent.
HAS_SUPPLIED_DATA = (PROJECT_ROOT / "news.json").is_file() and (PROJECT_ROOT / "sp500.csv").is_file()
requires_supplied_data = unittest.skipUnless(
    HAS_SUPPLIED_DATA, "news.json and sp500.csv are not present in the repository root")
