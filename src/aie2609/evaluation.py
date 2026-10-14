"""Prepare and score a small human review set without changing classifications."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

from .errors import ClassificationError, RunError
from .models import Article

EVALUATION_VERSION = "human-evaluation-v1"
ABSENT = "absent"
DECISIONS = {"", "positive", "neutral", "negative", ABSENT, "uncertain"}
SAMPLE_FIELDS = [
    "id", "ticker", "headline", "article_text", "final_label", "final_evidence",
    "candidate_label", "candidate_evidence", "human_decision", "human_notes",
]
DISAGREEMENT_FIELDS = [
    "id", "ticker", "headline", "final_label", "final_evidence",
    "candidate_label", "candidate_evidence",
]


def disagreement_rows(articles: list[Article], final: dict[str, list[dict]],
                      candidate: dict[str, list[dict]]) -> list[dict[str, str]]:
    """Expand entity presence and label differences into stable review decisions."""
    by_id = {article.id: article for article in articles}
    if set(final) != set(by_id) or set(candidate) != set(by_id):
        raise ClassificationError("Comparison inputs must cover every article exactly once.")
    rows = []
    for article_id in sorted(by_id):
        left = {entity["ticker"]: entity for entity in final[article_id]}
        right = {entity["ticker"]: entity for entity in candidate[article_id]}
        for ticker in sorted(left.keys() | right.keys()):
            final_label = left.get(ticker, {}).get("label", ABSENT)
            candidate_label = right.get(ticker, {}).get("label", ABSENT)
            if final_label == candidate_label:
                continue
            article = by_id[article_id]
            rows.append({
                "id": article_id,
                "ticker": ticker,
                "headline": article.headline,
                "article_text": article.body,
                "final_label": final_label,
                "final_evidence": left.get(ticker, {}).get("evidence", ""),
                "candidate_label": candidate_label,
                "candidate_evidence": right.get(ticker, {}).get("evidence", ""),
                "human_decision": "",
                "human_notes": "",
            })
    return rows


def _safe_csv_cell(value: str) -> str:
    """Prevent spreadsheet formula execution in article-derived text cells."""
    return "'" + value if value.startswith(("=", "+", "-", "@")) else value


def _csv_text(fields: list[str], rows: list[dict[str, str]]) -> str:
    from io import StringIO

    stream = StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: _safe_csv_cell(row.get(field, "")) for field in fields})
    return stream.getvalue()


def _write_text(path: Path, content: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def _sample_markdown(rows: list[dict[str, str]]) -> str:
    parts = [
        "# Human review sample",
        "",
        "Read the article without assuming either version is correct. For each pair,",
        "fill `human_decision` in `sample.csv` with `positive`, `neutral`, `negative`,",
        "`absent` or `uncertain`. `absent` means the ticker should not be listed for",
        "this article.",
        "Read the text and choose your label before comparing the two versions.",
        "This sample measures disputed cases only, not overall accuracy.",
        "",
    ]
    for index, row in enumerate(rows, 1):
        parts.extend([
            f"## {index}. {row['id']} — {row['ticker']}",
            "",
            f"**Headline:** {row['headline']}",
            "",
            f"**Current final version:** `{row['final_label']}`",
            "",
            f"> {row['final_evidence'] or '(no evidence: entity absent)'}",
            "",
            f"**Candidate version:** `{row['candidate_label']}`",
            "",
            f"> {row['candidate_evidence'] or '(no evidence: entity absent)'}",
            "",
            "**Full article:**",
            "",
            row["article_text"],
            "",
            "---",
            "",
        ])
    return "\n".join(parts)


def prepare_evaluation(*, articles: list[Article], final: dict[str, list[dict]],
                       candidate: dict[str, list[dict]], cases: list[str],
                       output_dir: Path) -> dict:
    """Write all disagreements plus a user-selected, editable review sample."""
    if output_dir.exists():
        raise RunError("Evaluation output directory must not already exist.")
    rows = disagreement_rows(articles, final, candidate)
    indexed = {(row["id"], row["ticker"]): row for row in rows}
    selected = []
    seen = set()
    for case in cases:
        if ":" not in case:
            raise ValueError("Evaluation cases must use ARTICLE_ID:TICKER.")
        key = tuple(case.split(":", 1))
        if key in seen or key not in indexed:
            raise ValueError("Evaluation cases must be unique existing disagreements.")
        seen.add(key)
        selected.append(indexed[key])
    if not selected:
        raise ValueError("At least one evaluation case is required.")

    output_dir.mkdir(parents=True, exist_ok=False)
    _write_text(output_dir / "disagreements.csv", _csv_text(DISAGREEMENT_FIELDS, rows))
    _write_text(output_dir / "sample.csv", _csv_text(SAMPLE_FIELDS, selected))
    _write_text(output_dir / "SAMPLE_GUIDE.md", _sample_markdown(selected))
    manifest = {
        "schema_version": 1,
        "evaluation_version": EVALUATION_VERSION,
        "disagreements": len(rows),
        "disagreement_articles": len({row["id"] for row in rows}),
        "sample_cases": len(selected),
        "cases": [f"{row['id']}:{row['ticker']}" for row in selected],
    }
    _write_text(output_dir / "manifest.json", json.dumps(
        manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    return manifest


def evaluate_annotations(path: Path) -> dict:
    """Validate human decisions and compare both proposals on answered cases."""
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != SAMPLE_FIELDS:
                raise ClassificationError("Invalid human evaluation columns.")
            rows = list(reader)
    except OSError as exc:
        raise RunError("Human evaluation file is missing or unreadable.") from exc
    if not rows:
        raise ClassificationError("Human evaluation file must contain at least one case.")
    seen = set()
    for row in rows:
        key = (row["id"], row["ticker"])
        if key in seen or row["human_decision"] not in DECISIONS:
            raise ClassificationError("Invalid duplicate case or human decision.")
        seen.add(key)
    answered = [row for row in rows if row["human_decision"] not in {"", "uncertain"}]
    uncertain = sum(row["human_decision"] == "uncertain" for row in rows)
    final_correct = sum(row["final_label"] == row["human_decision"] for row in answered)
    candidate_correct = sum(
        row["candidate_label"] == row["human_decision"] for row in answered)
    denominator = len(answered)
    return {
        "schema_version": 1,
        "evaluation_version": EVALUATION_VERSION,
        "cases": len(rows),
        "answered": denominator,
        "uncertain": uncertain,
        "remaining": len(rows) - denominator - uncertain,
        "final_correct": final_correct,
        "candidate_correct": candidate_correct,
        "final_accuracy": None if not denominator else final_correct / denominator,
        "candidate_accuracy": None if not denominator else candidate_correct / denominator,
    }
