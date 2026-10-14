"""Strict input loading and audit logic."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from io import StringIO
from pathlib import Path
from typing import Any

from .dates import as_of_datetime, parse_new_york_datetime
from .errors import DataValidationError
from .models import Article, AuditIssue, Company, NewsDataset, Universe
from .normalization import normalize_identifier, normalize_text

NEWS_FIELDS = frozenset({"id", "date", "headline", "body"})
UNIVERSE_FIELDS = ("symbol", "security", "gics_sector", "headquarters", "date_added")
CLASS_ALIASES = {"GOOG": "GOOGL", "FOX": "FOXA", "NWS": "NWSA"}


def _read_utf8(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except FileNotFoundError as exc:
        raise DataValidationError(f"Input file does not exist: {path}") from exc
    except UnicodeDecodeError as exc:
        raise DataValidationError(f"Input is not valid UTF-8: {path}") from exc
    except OSError as exc:
        raise DataValidationError(f"Cannot read input file {path}: {exc}") from exc


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DataValidationError(f"Duplicate JSON key {key!r}.")
        result[key] = value
    return result


def load_news(path: str | Path) -> NewsDataset:
    source = Path(path)
    text = _read_utf8(source)
    try:
        payload = json.loads(text, object_pairs_hook=_strict_object)
    except DataValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise DataValidationError(
            f"Invalid JSON in {source} at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc

    if not isinstance(payload, list) or not payload:
        raise DataValidationError(f"{source} must contain a non-empty JSON array.")

    articles: list[Article] = []
    issues: list[AuditIssue] = []
    seen_ids: set[str] = set()
    normalized_content: dict[tuple[str, str], list[str]] = defaultdict(list)
    as_of = as_of_datetime()

    for index, item in enumerate(payload):
        location = f"{source}[{index}]"
        if not isinstance(item, dict):
            raise DataValidationError(f"{location} must be a JSON object.")
        missing = NEWS_FIELDS - item.keys()
        if missing:
            raise DataValidationError(f"{location} is missing fields: {', '.join(sorted(missing))}.")
        extras = item.keys() - NEWS_FIELDS
        if extras:
            issues.append(
                AuditIssue(
                    "extra_news_fields",
                    f"Ignored extra fields: {', '.join(sorted(extras))}.",
                    str(source),
                    str(item.get("id", index)),
                )
            )
        for field in NEWS_FIELDS:
            if not isinstance(item[field], str) or not item[field].strip():
                raise DataValidationError(f"{location}.{field} must be a non-empty string.")

        article_id = normalize_identifier(item["id"])
        if article_id in seen_ids:
            raise DataValidationError(f"Duplicate article id {article_id!r} in {source}.")
        seen_ids.add(article_id)
        published_at = parse_new_york_datetime(item["date"].strip())
        if published_at > as_of:
            raise DataValidationError(
                f"Article {article_id!r} is later than the fixed as-of time {as_of.isoformat()}."
            )

        headline, headline_removed = normalize_text(item["headline"])
        body, body_removed = normalize_text(item["body"])
        removed = headline_removed + body_removed
        if removed:
            issues.append(
                AuditIssue(
                    "removed_zero_width_space",
                    f"Removed {removed} U+200B character(s) from the normalized copy.",
                    str(source),
                    article_id,
                )
            )
        normalized_content[(headline.strip(), body.strip())].append(article_id)
        articles.append(
            Article(
                id=article_id,
                published_at=published_at,
                date_raw=item["date"],
                headline_raw=item["headline"],
                body_raw=item["body"],
                headline=headline,
                body=body,
            )
        )

    for article_ids in normalized_content.values():
        if len(article_ids) > 1:
            issues.append(
                AuditIssue(
                    "duplicate_article_content",
                    f"Equivalent normalized content found for ids: {', '.join(article_ids)}.",
                    str(source),
                )
            )
    return NewsDataset(tuple(articles), tuple(issues))


def load_universe(path: str | Path) -> Universe:
    source = Path(path)
    text = _read_utf8(source)
    try:
        rows = list(csv.reader(StringIO(text, newline=""), strict=True))
    except csv.Error as exc:
        raise DataValidationError(f"Malformed CSV in {source}: {exc}") from exc
    if not rows:
        raise DataValidationError(f"{source} is empty.")

    header = [normalize_identifier(value) for value in rows[0]]
    if len(header) != len(set(header)):
        raise DataValidationError(f"Duplicate CSV column in {source}.")
    missing = set(UNIVERSE_FIELDS) - set(header)
    if missing:
        raise DataValidationError(f"{source} is missing columns: {', '.join(sorted(missing))}.")
    extras = sorted(set(header) - set(UNIVERSE_FIELDS))
    issues: list[AuditIssue] = []
    if extras:
        issues.append(
            AuditIssue("extra_universe_columns", f"Ignored extra columns: {', '.join(extras)}.", str(source))
        )

    positions = {name: header.index(name) for name in UNIVERSE_FIELDS}
    source_companies: dict[str, dict[str, str]] = {}
    for line_number, row in enumerate(rows[1:], start=2):
        if len(row) != len(header):
            raise DataValidationError(
                f"{source}:{line_number} has {len(row)} columns; expected {len(header)}."
            )
        values = {name: normalize_identifier(row[position]) for name, position in positions.items()}
        for field, value in values.items():
            if not value:
                raise DataValidationError(f"{source}:{line_number}.{field} must not be empty.")
        symbol = values["symbol"]
        if symbol in source_companies:
            raise DataValidationError(f"Duplicate symbol {symbol!r} in {source}.")
        source_companies[symbol] = values

    for alias, canonical in CLASS_ALIASES.items():
        if alias in source_companies and canonical not in source_companies:
            raise DataValidationError(
                f"Class alias {alias!r} is present but canonical ticker {canonical!r} is absent."
            )

    grouped_aliases: dict[str, list[str]] = defaultdict(list)
    for symbol in source_companies:
        grouped_aliases[CLASS_ALIASES.get(symbol, symbol)].append(symbol)

    companies: list[Company] = []
    for canonical, aliases in sorted(grouped_aliases.items()):
        values = source_companies[canonical]
        companies.append(
            Company(
                ticker=canonical,
                security=values["security"],
                gics_sector=values["gics_sector"],
                headquarters=values["headquarters"],
                date_added=values["date_added"],
                aliases=tuple(sorted(aliases)),
            )
        )
    return Universe(
        companies=tuple(companies),
        source_row_count=len(source_companies),
        ticker_aliases={
            alias: canonical
            for alias, canonical in CLASS_ALIASES.items()
            if alias in source_companies
        },
        issues=tuple(issues),
    )
