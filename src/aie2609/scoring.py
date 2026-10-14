"""Deterministic time decay and final CSV export from an approved composition."""

from __future__ import annotations

import csv
import hashlib
import io
import math
import os
from datetime import UTC
from pathlib import Path

from .classification import strict_json
from .dates import AS_OF_TEXT, as_of_datetime
from .errors import ClassificationError, RunError
from .models import Article, Universe
from .review import load_initial
from .runner import write_json

SCORING_VERSION = "time-decay-v1"
HALF_LIFE_DAYS = 7
LABEL_VALUES = {"positive": 1, "neutral": 0, "negative": -1}


def calculate_scores(articles: list[Article], classifications: dict[str, list[dict]]) \
        -> tuple[list[dict[str, str]], dict[str, float]]:
    """Return stable entity rows and the exact required per-ticker weighted sums."""
    by_id = {article.id: article for article in articles}
    if set(classifications) != set(by_id):
        raise ClassificationError("Scoring requires exactly one classification for every article.")
    reference = as_of_datetime().astimezone(UTC)
    rows: list[dict[str, str]] = []
    contributions: dict[str, list[float]] = {}
    for article_id in sorted(classifications):
        article = by_id[article_id]
        elapsed = (reference - article.published_at.astimezone(UTC)).total_seconds()
        if elapsed < 0:
            raise ClassificationError("An article is later than the fixed scoring reference time.")
        days = elapsed / 86400
        weight = 0.5 ** (days / HALF_LIFE_DAYS)
        for entity in classifications[article_id]:
            ticker = entity["ticker"]
            rows.append({"id": article_id, "ticker": ticker, "label": entity["label"]})
            contributions.setdefault(ticker, []).append(LABEL_VALUES[entity["label"]] * weight)
    scores = {}
    for ticker in sorted(contributions):
        value = math.fsum(contributions[ticker])
        scores[ticker] = 0.0 if value == 0.0 else value
    return rows, scores


def _csv_text(header: list[str], rows: list[list[str]]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return stream.getvalue()


def _write_text(path: Path, content: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export_scores(*, articles: list[Article], universe: Universe,
                  composition_dir: Path, output_dir: Path,
                  news_path: Path, universe_path: Path, allow_alerts: bool = False) -> dict:
    """Validate composition provenance, calculate scores and atomically write deliverables.

    ``allow_alerts`` lets the end-to-end run export a composition that still has
    blocking alerts; the manifest then records ``ready_for_scoring: false``.
    """
    classifications_path = composition_dir / "classifications.json"
    report_path = composition_dir / "composition_report.json"
    try:
        report = strict_json(report_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RunError("Composition report is missing or unreadable.") from exc
    if (not isinstance(report, dict) or report.get("schema_version") != 1
            or not isinstance(report.get("ready_for_scoring"), bool)
            or not isinstance(report.get("composition_version"), str)
            or not isinstance(report.get("output_classifications_sha256"), str)):
        raise RunError("Composition report is invalid.")
    if not report["ready_for_scoring"] and not allow_alerts:
        raise RunError("Composition is not approved for scoring.")
    try:
        actual_hash = _hash(classifications_path)
    except OSError as exc:
        raise RunError("Composed classifications are missing or unreadable.") from exc
    if actual_hash != report["output_classifications_sha256"]:
        raise RunError("Composed classifications do not match their approved report.")

    classifications = load_initial(classifications_path, articles, universe)
    entity_rows, scores = calculate_scores(articles, classifications)
    entities_text = _csv_text(
        ["id", "ticker", "label"],
        [[row["id"], row["ticker"], row["label"]] for row in entity_rows],
    )
    scores_text = _csv_text(
        ["ticker", "value"],
        [[ticker, "0" if value == 0.0 else repr(value)] for ticker, value in scores.items()],
    )

    output = output_dir.resolve()
    if output.exists():
        raise RunError("Score output directory must not already exist.")
    for path in (news_path, universe_path, classifications_path, report_path):
        resolved = path.resolve()
        if resolved == output or output in resolved.parents:
            raise RunError("Score output must not contain or overwrite an input.")

    output_dir.mkdir(parents=True, exist_ok=False)
    entities_path = output_dir / "entities.csv"
    scores_path = output_dir / "scores.csv"
    _write_text(entities_path, entities_text)
    _write_text(scores_path, scores_text)
    manifest = {
        "schema_version": 1,
        "status": "completed",
        "scoring_version": SCORING_VERSION,
        "composition_version": report["composition_version"],
        "ready_for_scoring": report["ready_for_scoring"],
        "as_of": AS_OF_TEXT,
        "timezone": "America/New_York",
        "half_life_days": HALF_LIFE_DAYS,
        "counts": {"articles": len(articles), "entities": len(entity_rows),
                   "tickers": len(scores)},
        "source_sha256": {str(path): _hash(path) for path in
                          (news_path, universe_path, classifications_path, report_path)},
        "output_sha256": {"entities.csv": _hash(entities_path),
                          "scores.csv": _hash(scores_path)},
    }
    write_json(output_dir / "run_manifest.json", manifest)
    return manifest
