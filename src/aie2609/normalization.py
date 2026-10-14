"""Conservative normalization for untrusted provider text."""

from __future__ import annotations

import unicodedata

ZERO_WIDTH_SPACE = "\u200b"


def normalize_text(value: str) -> tuple[str, int]:
    """Return a normalized copy and the number of removed U+200B characters."""
    normalized_lines = value.replace("\r\n", "\n").replace("\r", "\n")
    removed = normalized_lines.count(ZERO_WIDTH_SPACE)
    normalized = unicodedata.normalize("NFC", normalized_lines.replace(ZERO_WIDTH_SPACE, ""))
    return normalized, removed


def normalize_identifier(value: str) -> str:
    """Normalize a structured identifier without changing internal punctuation."""
    normalized, _ = normalize_text(value)
    return normalized.strip()
