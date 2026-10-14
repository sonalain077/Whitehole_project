"""Blind human adjudication of version disagreements, with spot checks of consensus.

Every (article, ticker) pair proposed by at least one version is either unanimous
(same label, or same absence, in every version) or disputed. The annotator decides
all disputed pairs plus a random sample of unanimous ones, without seeing which
version proposed what. Scoring estimates each version's pair-level accuracy.
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
from io import StringIO
from pathlib import Path

from .errors import ClassificationError, RunError
from .evaluation import ABSENT, _safe_csv_cell, _write_text
from .models import Article, Universe
from .review import load_initial

REFERENCE_VERSION = "reference-adjudication-v1"
# Short rows on purpose: the article text and excerpts are in GUIDE.md, so the CSV
# stays easy to edit by hand.
CASE_FIELDS = ["case", "id", "ticker", "company", "human_decision", "human_notes"]
DECISIONS = {"", "positive", "neutral", "negative", ABSENT, "uncertain"}

GUIDE_HEADER = """# Référence arbitrée à l'aveugle

Pour chaque cas, lis l'article et renseigne `human_decision` dans `cases.csv` :
`positive`, `neutral`, `negative`, `absent` ou `uncertain`. Tu ne vois pas quelle
version a proposé quoi : c'est voulu. Ne pas ouvrir `key.json` avant la fin.

Applique les définitions du sujet, pas une intuition de marché :

> For every (article, company) pair, the implication of the article for the
> company's value at publication time. An article can be positive for one company
> and negative for another.
> - **positive** — e.g. upgrade with a higher price target, contract win, favourable ruling.
> - **negative** — e.g. downgrade, guidance cut, lawsuit, recall.
> - **neutral** — mentioned without implication: the bank issuing the rating, a media
>   source, a customer, a location, a size comparison.

Repères :

- Juge à partir de l'article seul, au moment de sa publication.
- Une action citée seulement pour comparer (performance passée, autre titre qui
  « a aussi monté ») est `neutral`, sauf si l'article établit une conséquence
  propre à cette entreprise.
- `absent` : l'entreprise n'est pas réellement mentionnée, ou le rattachement est
  faux (par exemple le réseau social X n'est pas Block).
- `uncertain` : à réserver aux cas vraiment indécidables ; ils sont exclus du score.
- Si une entreprise du référentiel manque, note-la dans `human_notes`
  (`missing: TICKER`).

Certains cas sont des contrôles tirés au hasard parmi les décisions unanimes : ils
servent à mesurer les erreurs que toutes les versions partagent.
"""


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _csv_text(rows: list[dict[str, str]]) -> str:
    stream = StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=CASE_FIELDS, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: _safe_csv_cell(row[field]) for field in CASE_FIELDS})
    return stream.getvalue()


def _pairs(versions: dict[str, dict[str, list[dict]]]) -> dict[tuple[str, str], dict[str, dict]]:
    pairs: dict[tuple[str, str], dict[str, dict]] = {}
    for name, classifications in versions.items():
        for article_id, entities in classifications.items():
            for entity in entities:
                pairs.setdefault((article_id, entity["ticker"]), {})[name] = entity
    return pairs


def prepare_reference(*, articles: list[Article], universe: Universe,
                      version_paths: dict[str, Path], spot_checks: int, seed: int,
                      output_dir: Path) -> dict:
    """Write blind cases, a hidden answer key and a readable guide."""
    if len(version_paths) < 2:
        raise ValueError("A reference needs at least two versions to compare.")
    if spot_checks < 0:
        raise ValueError("spot_checks must not be negative.")
    if output_dir.exists():
        raise RunError("Reference output directory must not already exist.")
    expected = {article.id for article in articles}
    versions = {}
    for name, path in version_paths.items():
        versions[name] = load_initial(path, articles, universe)
        if set(versions[name]) != expected:
            raise ClassificationError(f"Version {name} must cover every article exactly once.")
    pairs = _pairs(versions)
    disputed, unanimous = [], []
    for key in sorted(pairs):
        labels = {name: pairs[key][name]["label"] if name in pairs[key] else ABSENT
                  for name in versions}
        (disputed if len(set(labels.values())) > 1 else unanimous).append((key, labels))
    sampled = random.Random(seed).sample(unanimous, min(spot_checks, len(unanimous)))
    cases = sorted([(key, labels, "disputed") for key, labels in disputed]
                   + [(key, labels, "spot_check") for key, labels in sampled])

    by_id = {article.id: article for article in articles}
    names = {company.ticker: company.security for company in universe.companies}
    rows, key_rows, guide = [], [], [GUIDE_HEADER]
    current = None
    for number, ((article_id, ticker), labels, kind) in enumerate(cases, 1):
        case = f"R{number:03d}"
        article = by_id[article_id]
        excerpts = sorted({entity["evidence"] for entity in pairs[(article_id, ticker)].values()})
        rows.append({"case": case, "id": article_id, "ticker": ticker,
                     "company": names[ticker], "human_decision": "", "human_notes": ""})
        key_rows.append({"case": case, "id": article_id, "ticker": ticker,
                         "kind": kind, "labels": labels})
        if article_id != current:
            current = article_id
            guide += ["---", "", f"## {article_id} — {article.headline}", "",
                      f"*Publié le {article.date_raw.strip()} (New York)*", "", article.body, ""]
        guide += [f"**{case} — {ticker} ({names[ticker]})**", ""]
        guide += [f"> {excerpt}" for excerpt in excerpts] + [""]

    output_dir.mkdir(parents=True, exist_ok=False)
    _write_text(output_dir / "cases.csv", _csv_text(rows))
    _write_text(output_dir / "GUIDE.md", "\n".join(guide) + "\n")
    manifest = {"schema_version": 1, "reference_version": REFERENCE_VERSION,
                "versions": {name: {"path": str(path), "sha256": _hash(path)}
                             for name, path in version_paths.items()},
                "seed": seed, "pairs": len(pairs), "unanimous_pairs": len(unanimous),
                "disputed_pairs": len(disputed), "spot_checks": len(sampled),
                "cases": len(cases)}
    _write_text(output_dir / "key.json", json.dumps(
        {**manifest, "cases": key_rows}, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    _write_text(output_dir / "manifest.json", json.dumps(
        manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    return manifest


def score_reference(reference_dir: Path) -> dict:
    """Validate human decisions and estimate each version's pair-level accuracy."""
    try:
        with (reference_dir / "cases.csv").open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != CASE_FIELDS:
                raise ClassificationError("Invalid reference case columns.")
            rows = list(reader)
        key = json.loads((reference_dir / "key.json").read_text(encoding="utf-8"))
    except OSError as exc:
        raise RunError("Reference cases or key are missing or unreadable.") from exc
    expected = {row["case"]: row for row in key["cases"]}
    if [row["case"] for row in rows] != list(expected):
        raise ClassificationError("Reference cases do not match their key.")
    invalid = [f"{row['case']}={row['human_decision']!r}" for row in rows
               if row["human_decision"].strip().lower() not in DECISIONS]
    if invalid:
        raise ClassificationError("Invalid human decisions: " + ", ".join(invalid))

    decided = {row["case"]: row["human_decision"].strip().lower() for row in rows
               if row["human_decision"].strip().lower() not in {"", "uncertain"}}
    uncertain = sum(row["human_decision"].strip().lower() == "uncertain" for row in rows)
    spot = [case for case in decided if expected[case]["kind"] == "spot_check"]
    spot_agree = sum(next(iter(expected[case]["labels"].values())) == decided[case]
                     for case in spot)
    consensus_accuracy = spot_agree / len(spot) if spot else None
    unanimous = key["unanimous_pairs"]
    report = {"schema_version": 1, "reference_version": REFERENCE_VERSION,
              "cases": len(rows), "decided": len(decided), "uncertain": uncertain,
              "remaining": len(rows) - len(decided) - uncertain,
              "spot_checks": {"decided": len(spot), "agree_with_consensus": spot_agree,
                              "consensus_accuracy": consensus_accuracy},
              "versions": {}}
    disputed = [case for case in decided if expected[case]["kind"] == "disputed"]
    for name in key["versions"]:
        correct = sum(expected[case]["labels"][name] == decided[case] for case in disputed)
        errors = [{"case": case, "id": expected[case]["id"], "ticker": expected[case]["ticker"],
                   "version": expected[case]["labels"][name], "human": decided[case]}
                  for case in disputed + spot
                  if expected[case]["labels"][name] != decided[case]]
        estimate = None
        if consensus_accuracy is not None:
            # Unanimous pairs are scored at the measured consensus accuracy.
            estimate = ((unanimous * consensus_accuracy + correct)
                        / (unanimous + len(disputed)))
        report["versions"][name] = {"disputed_decided": len(disputed),
                                    "disputed_correct": correct,
                                    "estimated_pair_accuracy": estimate,
                                    "errors": errors}
    return report
