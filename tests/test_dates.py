from __future__ import annotations

import unittest
from datetime import timedelta

from aie2609.dates import parse_new_york_datetime
from aie2609.errors import DataValidationError


class NewYorkDateTests(unittest.TestCase):
    def test_parses_regular_local_time(self) -> None:
        parsed = parse_new_york_datetime("2026-09-28T16:20")
        self.assertEqual(parsed.utcoffset(), -timedelta(hours=4))

    def test_rejects_bad_format_and_bad_calendar_date(self) -> None:
        for value in ("2026-9-28T16:20", "2026-02-30T10:00"):
            with self.subTest(value=value), self.assertRaises(DataValidationError):
                parse_new_york_datetime(value)

    def test_rejects_nonexistent_spring_time(self) -> None:
        with self.assertRaisesRegex(DataValidationError, "Nonexistent"):
            parse_new_york_datetime("2026-03-08T02:30")

    def test_rejects_ambiguous_fall_time(self) -> None:
        with self.assertRaisesRegex(DataValidationError, "Ambiguous"):
            parse_new_york_datetime("2026-11-01T01:30")


if __name__ == "__main__":
    unittest.main()
