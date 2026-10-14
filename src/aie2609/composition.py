"""Deterministic composition, provenance and quality gates before scoring."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from .classification import strict_json
from .errors import ClassificationError, RunError
from .models import Article, Universe
from .review import coverage_hints, load_alias_config, load_initial, review_reasons
from .runner import write_json

COMPOSITION_VERSION = "classification-composition-v1"

_ANALYST_ROLE_PATTERN = re.compile(
    r"\b(?:analysts?|broker(?:age)?|downgrad(?:e|ed|es|ing)|"
    r"upgrad(?:e|ed|es|ing)|price target|target price|rating)\b",
    re.I,
)


def _name_patterns(ticker: str, universe: Universe) -> list[re.Pattern[str]]:
    company = next((company for company in universe.companies if company.ticker == ticker), None)
    if company is None:
        return []
    config = load_alias_config(universe)
    blocked = {name.casefold() for name in config["blocked_generated_names"]}
    name = re.sub(r"\s*\((?:The|Class [AB])\)\s*", " ", company.security,
                  flags=re.I).strip()
    base = re.sub(r"(?:[,\s]+(?:Inc\.?|Corp\.?|Corporation|Company|Co\.?|plc|Ltd\.?))+$",
                  "", name, flags=re.I).strip()
    names = {name}
    if base.casefold() not in blocked:
        names.add(base)
    for row in config["aliases"]:
        if row["type"] != "ambiguous" and ticker in row["tickers"]:
            names.update(row["names"])
    patterns = [re.compile(r"(?<!\w)" + re.escape(value) + r"(?!\w)", re.I)
                for value in names if value]
    ticker_names = set(company.aliases) | {company.ticker}
    ticker_names.update(alias for alias, parent in universe.ticker_aliases.items()
                        if parent == ticker)
    for symbol in ticker_names:
        escaped = re.escape(symbol)
        if len(symbol) >= 2:
            patterns.append(re.compile(r"(?<![A-Z0-9.])" + escaped + r"(?![A-Z0-9.])"))
        else:
            patterns.append(re.compile(
                r"(?:\$" + escaped + r"(?![\w.])|\((?:NYSE|NASDAQ:\s*)?" + escaped
                + r"\)|\b(?:ticker|symbol)\s+" + escaped + r"(?![\w.]))", re.I))
    return patterns


def has_anchor(text: str, ticker: str, universe: Universe) -> bool:
    """Require an exact company, ticker or curated alias mention, never a substring."""
    return any(pattern.search(text) for pattern in _name_patterns(ticker, universe))


def quality_alerts(article: Article, entities: list[dict], universe: Universe) -> dict[str, list[str]]:
    """Return stable blocking/advisory alerts without changing a model decision."""
    blocking: set[str] = set()
    advisory: set[str] = set()
    for reason in review_reasons(article, entities, universe):
        target = advisory if reason.startswith("ambiguous:") else blocking
        target.add(reason)
    full_text = article.headline + "\n" + article.body
    config = load_alias_config(universe)
    for entity in entities:
        ticker = entity["ticker"]
        evidence_anchored = has_anchor(entity["evidence"], ticker, universe)
        article_anchored = has_anchor(full_text, ticker, universe)
        if not article_anchored:
            advisory.add("unanchored_entity:" + ticker)
        elif not evidence_anchored:
            advisory.add("unanchored_evidence:" + ticker)
        if (entity["label"] != "neutral" and not evidence_anchored
                and _ANALYST_ROLE_PATTERN.search(entity["evidence"])):
            advisory.add("possible_role_transfer:" + ticker)
        if not evidence_anchored:
            for forbidden in config["forbidden_aliases"]:
                if (forbidden["ticker"] == ticker
                        and re.search(r"(?<!\w)" + re.escape(forbidden["name"]) + r"(?!\w)",
                                      entity["evidence"], re.I)):
                    blocking.add("forbidden_alias:" + ticker + ":" + forbidden["name"])
    return {"blocking": sorted(blocking), "advisory": sorted(advisory)}


def _load_complete(path: Path, articles: list[Article], universe: Universe) -> dict[str, list[dict]]:
    result = load_initial(path, articles, universe)
    expected = {article.id for article in articles}
    if set(result) != expected:
        raise ClassificationError("A baseline or candidate must contain every input article exactly once.")
    return result


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_review(review_dir: Path, baseline_hash: str, articles: list[Article],
                 universe: Universe) -> tuple[dict[str, list[dict]], dict, dict[str, dict]]:
    manifest_path = review_dir / "run_manifest.json"
    changes_path = review_dir / "review_changes.json"
    classifications_path = review_dir / "classifications.json"
    manifest = strict_json(manifest_path.read_text(encoding="utf-8"))
    changes = strict_json(changes_path.read_text(encoding="utf-8"))
    if (not isinstance(manifest, dict) or manifest.get("status") != "completed"
            or not isinstance(manifest.get("prompt_version"), str)
            or not isinstance(manifest.get("source_sha256"), dict)
            or baseline_hash not in manifest["source_sha256"].values()):
        raise RunError("Review manifest is incomplete or does not reference this baseline.")
    if (not isinstance(changes, dict) or changes.get("schema_version") != 2
            or not isinstance(changes.get("articles"), list)):
        raise ClassificationError("Invalid review changes document.")
    reviewed = load_initial(classifications_path, articles, universe)
    rows: dict[str, dict] = {}
    for row in changes["articles"]:
        if (not isinstance(row, dict) or not isinstance(row.get("id"), str)
                or row["id"] in rows or not isinstance(row.get("unresolved_hints_after"), list)
                or not all(isinstance(value, str) for value in row["unresolved_hints_after"])
                or not isinstance(row.get("added"), list)
                or not isinstance(row.get("removed"), list)
                or not isinstance(row.get("label_changes"), list)):
            raise ClassificationError("Invalid review change row.")
        rows[row["id"]] = row
    if set(rows) != set(reviewed):
        raise ClassificationError("Review changes and classifications cover different articles.")
    unresolved = {article_id: rows[article_id]["unresolved_hints_after"]
                  for article_id in rows if rows[article_id]["unresolved_hints_after"]}
    if unresolved:
        raise RunError("Review still contains unresolved reliable coverage hints.")
    return reviewed, {"directory": str(review_dir),
                      "prompt_version": manifest["prompt_version"],
                      "classifications_sha256": _hash(classifications_path),
                      "manifest_sha256": _hash(manifest_path),
                      "changes_sha256": _hash(changes_path),
                      "article_ids": sorted(reviewed)}, rows


def _diff(before: list[dict], after: list[dict]) -> dict | None:
    left = {entity["ticker"]: entity["label"] for entity in before}
    right = {entity["ticker"]: entity["label"] for entity in after}
    if left == right:
        return None
    return {"added": sorted(right.keys() - left.keys()),
            "removed": sorted(left.keys() - right.keys()),
            "label_changes": [{"ticker": ticker, "before": left[ticker],
                               "after": right[ticker]}
                              for ticker in sorted(left.keys() & right.keys())
                              if left[ticker] != right[ticker]]}


def compose_classifications(*, articles: list[Article], universe: Universe,
                            baseline_path: Path, review_dirs: list[Path],
                            candidate_path: Path | None, output_dir: Path) -> dict:
    """Apply validated review overlays and block scoring while quality conflicts remain."""
    inputs = [baseline_path, *(path / "classifications.json" for path in review_dirs)]
    if candidate_path is not None:
        inputs.append(candidate_path)
    output = output_dir.resolve()
    if output.exists():
        raise RunError("Composition output directory must not already exist.")
    for path in inputs:
        resolved = path.resolve()
        if resolved == output or output in resolved.parents:
            raise RunError("Composition output must not contain or overwrite an input.")

    baseline = _load_complete(baseline_path, articles, universe)
    baseline_hash = _hash(baseline_path)
    composed = {article_id: list(entities) for article_id, entities in baseline.items()}
    provenance = {article.id: {"source": "baseline", "path": str(baseline_path)}
                  for article in articles}
    overlays = []
    for review_dir in review_dirs:
        reviewed, metadata, reported = _load_review(
            review_dir, baseline_hash, articles, universe)
        for article_id, entities in reviewed.items():
            if provenance[article_id]["source"] != "baseline":
                raise RunError("More than one review overlay replaces the same article.")
            difference = _diff(composed[article_id], entities) or {
                "added": [], "removed": [], "label_changes": []}
            declared = {key: reported[article_id][key]
                        for key in ("added", "removed", "label_changes")}
            if declared != difference:
                raise RunError("Review change report does not match its classifications.")
            if (metadata["prompt_version"].endswith("-additions-only")
                    and (difference["removed"] or difference["label_changes"])):
                raise RunError("Additions-only review contains a forbidden change.")
            composed[article_id] = entities
            provenance[article_id] = {"source": "review", "path": str(review_dir)}
        overlays.append(metadata)

    by_id = {article.id: article for article in articles}
    quality = []
    for article_id in sorted(composed):
        alerts = quality_alerts(by_id[article_id], composed[article_id], universe)
        quality.append({"id": article_id, "provenance": provenance[article_id], **alerts})

    candidate_changes = []
    candidate_quality = []
    candidate_hash = None
    if candidate_path is not None:
        candidate = _load_complete(candidate_path, articles, universe)
        candidate_hash = _hash(candidate_path)
        for article_id in sorted(composed):
            alerts = quality_alerts(by_id[article_id], candidate[article_id], universe)
            candidate_quality.append({"id": article_id, **alerts})
            difference = _diff(composed[article_id], candidate[article_id])
            if difference is not None:
                candidate_changes.append({"id": article_id, **difference})

    blocking_count = sum(len(row["blocking"]) for row in quality)
    candidate_blocking_count = sum(len(row["blocking"]) for row in candidate_quality)
    ready = blocking_count == 0 and candidate_blocking_count == 0 and not candidate_changes
    rows = [{"id": article_id, "entities": composed[article_id]}
            for article_id in sorted(composed)]
    entity_count = sum(len(row["entities"]) for row in rows)
    report = {"schema_version": 1, "composition_version": COMPOSITION_VERSION,
              "ready_for_scoring": ready,
              "baseline": {"path": str(baseline_path), "sha256": baseline_hash},
              "review_overlays": overlays,
              "candidate": None if candidate_path is None else
                           {"path": str(candidate_path), "sha256": candidate_hash},
              "counts": {"articles": len(rows), "entities": entity_count,
                         "reviewed_articles": sum(item["source"] == "review"
                                                  for item in provenance.values()),
                         "blocking_alerts": blocking_count,
                         "advisory_alerts": sum(len(row["advisory"]) for row in quality),
                         "candidate_blocking_alerts": candidate_blocking_count,
                         "candidate_advisory_alerts": sum(
                             len(row["advisory"]) for row in candidate_quality),
                         "candidate_conflicts": len(candidate_changes)},
              "quality": quality, "candidate_quality": candidate_quality,
              "candidate_changes": candidate_changes}
    output_dir.mkdir(parents=True, exist_ok=False)
    classifications_output = output_dir / "classifications.json"
    write_json(classifications_output, {"schema_version": 1, "articles": rows})
    report["output_classifications_sha256"] = _hash(classifications_output)
    write_json(output_dir / "composition_report.json", report)
    return report
