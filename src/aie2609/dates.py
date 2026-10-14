"""Strict handling of New York local publication times."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .errors import DataValidationError

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$")
NEW_YORK_ZONE = "America/New_York"
AS_OF_TEXT = "2026-09-29T00:00"


def get_new_york_zone() -> ZoneInfo:
    try:
        return ZoneInfo(NEW_YORK_ZONE)
    except ZoneInfoNotFoundError as exc:
        raise DataValidationError(
            "Timezone data for America/New_York is unavailable; install the tzdata package."
        ) from exc


def parse_new_york_datetime(value: str) -> datetime:
    """Parse a local time, rejecting malformed, ambiguous and nonexistent values."""
    if not DATE_PATTERN.fullmatch(value):
        raise DataValidationError(
            f"Invalid date {value!r}; expected YYYY-MM-DDTHH:MM in New York local time."
        )
    try:
        naive = datetime.strptime(value, "%Y-%m-%dT%H:%M")
    except ValueError as exc:
        raise DataValidationError(f"Invalid calendar date {value!r}.") from exc

    zone = get_new_york_zone()
    candidates: list[datetime] = []
    for fold in (0, 1):
        aware = naive.replace(tzinfo=zone, fold=fold)
        round_trip = aware.astimezone(UTC).astimezone(zone).replace(tzinfo=None)
        if round_trip == naive:
            candidates.append(aware)

    if not candidates:
        raise DataValidationError(f"Nonexistent New York local time {value!r}.")
    if len(candidates) == 2 and candidates[0].utcoffset() != candidates[1].utcoffset():
        raise DataValidationError(f"Ambiguous New York local time {value!r}.")
    return candidates[0]


def as_of_datetime() -> datetime:
    return parse_new_york_datetime(AS_OF_TEXT)
