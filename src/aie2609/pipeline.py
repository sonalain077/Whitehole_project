"""End-to-end run: classify, review blocking alerts, compose and export in one command.

With ``passes > 1`` each pass is an independent classification + review + composition
(its own cache replica); a strict-majority vote then gives the final pairs and a
per-pair agreement level, and the vote is composed and exported like a single pass.
"""

from __future__ import annotations

from collections import Counter
from decimal import Decimal
from pathlib import Path

from .classification import MODEL, PROMPT_VERSION, strict_json
from .composition import compose_classifications, quality_alerts
from .errors import ClassificationError, RunError
from .models import Article, Universe
from .review import ALIAS_CONFIG_PATH, ReviewClassifier, load_initial
from .runner import LOG, Classifier, Client, write_json
from .scoring import export_scores
from .usage import summarize_usage

PIPELINE_VERSION = "end-to-end-v2"
VOTE_VERSION = "majority-vote-v1"
ABSENT = "absent"
_USAGE_FIELDS = ("api_calls", "local_cache_hits", "unknown_cost_attempts",
                 "known_cost_usd", "total_cost_usd")
_COMPOSITION_FIELDS = ("articles", "entities", "reviewed_articles",
                       "blocking_alerts", "advisory_alerts")


def _usage(report: dict) -> dict:
    return {name: report[name] for name in _USAGE_FIELDS}


def majority_vote(passes: list[dict[str, list[dict]]]) -> tuple[dict[str, list[dict]], dict]:
    """Keep a pair proposed by a strict majority of passes, with its majority label.

    When the passes that kept a pair are split on its label, the article supports no
    clear net direction for that company: the pair is kept as neutral and reported
    as a tie. Nothing is dropped or relabelled silently.
    """
    count = len(passes)
    if count < 3 or count % 2 == 0:
        raise ValueError("A majority vote needs an odd number of passes, at least three.")
    voted: dict[str, list[dict]] = {}
    pairs = []
    counts = Counter()
    for article_id in sorted(passes[0]):
        proposals: dict[str, dict[int, dict]] = {}
        for index, result in enumerate(passes):
            for entity in result[article_id]:
                proposals.setdefault(entity["ticker"], {})[index] = entity
        kept = []
        for ticker in sorted(proposals):
            votes = proposals[ticker]
            ballots = [votes[index]["label"] if index in votes else ABSENT
                       for index in range(count)]
            row = {"id": article_id, "ticker": ticker, "votes": ballots}
            if len(votes) * 2 < count:
                counts["dropped_minority"] += 1
                pairs.append({**row, "label": ABSENT, "agreement": "dropped_minority"})
                continue
            label, top = Counter(entity["label"] for entity in votes.values()).most_common(1)[0]
            if top * 2 <= len(votes):
                label, agreement = "neutral", "label_tie"
            elif top == count:
                agreement = "unanimous"
            else:
                agreement = "majority"
            counts[agreement] += 1
            # Evidence and role come from the first pass that chose this label.
            source = next((votes[index] for index in sorted(votes)
                           if votes[index]["label"] == label), votes[min(votes)])
            kept.append({**source, "label": label})
            pairs.append({**row, "label": label, "agreement": agreement})
        voted[article_id] = kept
    report = {"schema_version": 1, "vote_version": VOTE_VERSION, "passes": count,
              "counts": {name: counts[name] for name in
                         ("unanimous", "majority", "label_tie", "dropped_minority")},
              "pairs": pairs}
    return voted, report


class Pipeline:
    """Chain the existing steps; every step keeps its own artifacts and checks."""

    def __init__(self, client: Client, universe: Universe, maximum: Decimal, *,
                 cache_root: Path = Path(".cache"), max_attempts: int = 2,
                 max_output_tokens: int = 4096) -> None:
        if not maximum.is_finite() or maximum <= 0:
            raise ValueError("Budget must be positive and finite.")
        self.client = client
        self.universe = universe
        self.maximum = maximum
        self.cache_root = cache_root
        self.max_attempts = max_attempts
        self.max_output_tokens = max_output_tokens
        self.committed = Decimal(0)
        self.reports: dict[str, dict] = {}  # Full usage.json report of each paid step.

    def _remaining(self) -> Decimal:
        remaining = self.maximum - self.committed
        if remaining <= 0:
            raise RunError("Run budget is exhausted; no further call was made.")
        return remaining

    def _classify(self, articles: list[Article], output: Path, sources: list[Path],
                  step: str, replica: int, label: str) -> dict:
        classifier = Classifier(self.client, self.universe, self.cache_root / "classifications",
                                self._remaining(), max_attempts=self.max_attempts,
                                max_output_tokens=self.max_output_tokens, replica=replica)
        classifier.log_label = label + " classify"
        try:
            self.reports[step] = classifier.run(articles, output, sources)
            return self.reports[step]
        finally:
            self.committed += classifier.budget.committed

    def _review(self, article: Article, baseline: dict[str, list[dict]], blocking: list[str],
                output: Path, sources: list[Path], step: str, replica: int, label: str) -> dict:
        # A missing source only needs additions; a forbidden alias needs a review that may remove it.
        additions_only = not any(alert.startswith("forbidden_alias:") for alert in blocking)
        reviewer = ReviewClassifier(self.client, self.universe, self.cache_root / "reviews",
                                    self._remaining(), initial=baseline,
                                    additions_only=additions_only,
                                    max_attempts=self.max_attempts,
                                    max_output_tokens=self.max_output_tokens, replica=replica)
        reviewer.log_label = label + " review"
        row = {"id": article.id, "mode": reviewer.prompt_version, "blocking_before": blocking}
        try:
            usage = reviewer.run([article], output, sources)
        except ClassificationError as exc:
            # The validated first-pass result is kept; its alerts stay visible downstream.
            self.reports[step] = reviewer.usage_report(1, 0)
            row.update(status="rejected", reason=str(exc), **_usage(self.reports[step]))
            LOG.warning("%s review %s: rejected, first-pass result kept", label, article.id)
            return row
        finally:
            self.committed += reviewer.budget.committed
        self.reports[step] = usage
        changes = strict_json((output / "review_changes.json").read_text(encoding="utf-8"))
        unresolved = changes["articles"][0]["unresolved_hints_after"]
        row.update(status="rejected" if unresolved else "applied", **_usage(usage))
        if unresolved:
            row["reason"] = "Review left reliable coverage hints unresolved: " + ", ".join(unresolved)
        change = changes["articles"][0]
        LOG.info("%s review %s (%s): %s, added %s, removed %s", label, article.id,
                 ", ".join(blocking), row["status"], change["added"] or "none",
                 change["removed"] or "none")
        return row

    def _pass(self, articles: list[Article], base: Path, sources: list[Path],
              prefix: str, replica: int, label: str) -> dict:
        """One classification + targeted reviews + composition; returns its report."""
        LOG.info("%s: classifying %d articles", label, len(articles))
        result: dict = {"replica": replica}
        classification = self._classify(articles, base / "classify", sources,
                                        prefix + "classify", replica, label)
        result["classification"] = _usage(classification)
        baseline_path = base / "classify" / "classifications.json"
        baseline = load_initial(baseline_path, articles, self.universe)
        flagged = [(article, alerts) for article in sorted(articles, key=lambda item: item.id)
                   if (alerts := quality_alerts(article, baseline[article.id],
                                                self.universe)["blocking"])]
        LOG.info("%s: %d article(s) flagged for a targeted review", label, len(flagged))
        reviews = [self._review(article, baseline, blocking, base / "review" / article.id,
                                [*sources, baseline_path, ALIAS_CONFIG_PATH],
                                prefix + "review/" + article.id, replica, label)
                   for article, blocking in flagged]
        result["reviews"] = reviews
        composition = compose_classifications(
            articles=articles, universe=self.universe, baseline_path=baseline_path,
            review_dirs=[base / "review" / row["id"] for row in reviews if row["status"] == "applied"],
            candidate_path=None, output_dir=base / "compose")
        result["composition"] = {"ready_for_scoring": composition["ready_for_scoring"],
                                 **{name: composition["counts"][name]
                                    for name in _COMPOSITION_FIELDS}}
        LOG.info("%s: done, %d pairs, %d blocking alert(s)", label,
                 composition["counts"]["entities"], composition["counts"]["blocking_alerts"])
        return result

    def _vote(self, articles: list[Article], output_dir: Path, passes: int) -> dict:
        results = [load_initial(output_dir / f"pass-{index}" / "compose" / "classifications.json",
                                articles, self.universe) for index in range(1, passes + 1)]
        voted, report = majority_vote(results)
        vote_dir = output_dir / "vote"
        vote_dir.mkdir()
        write_json(vote_dir / "classifications.json", {"schema_version": 1, "articles": [
            {"id": article_id, "entities": voted[article_id]} for article_id in sorted(voted)]})
        write_json(vote_dir / "vote_report.json", report)
        composition = compose_classifications(
            articles=articles, universe=self.universe,
            baseline_path=vote_dir / "classifications.json", review_dirs=[],
            candidate_path=None, output_dir=output_dir / "compose")
        return {"counts": report["counts"],
                "composition": {"ready_for_scoring": composition["ready_for_scoring"],
                                **{name: composition["counts"][name]
                                   for name in _COMPOSITION_FIELDS}}}

    def run(self, articles: list[Article], output_dir: Path,
            news_path: Path, universe_path: Path, passes: int = 1) -> dict:
        if passes != 1 and (passes < 3 or passes % 2 == 0):
            raise ValueError("passes must be 1 or an odd number of at least three.")
        output = output_dir.resolve()
        if output.exists():
            raise RunError("Run output directory must not already exist.")
        for path in (news_path, universe_path):
            if output in path.resolve().parents:
                raise RunError("Run output must not contain an input file.")
        output_dir.mkdir(parents=True)
        report: dict = {"schema_version": 1, "pipeline_version": PIPELINE_VERSION,
                        "status": "running", "model": MODEL, "prompt_version": PROMPT_VERSION,
                        "articles": len(articles), "passes": passes,
                        "budget_usd": str(self.maximum)}
        step = "classify"
        try:
            sources = [news_path, universe_path]
            if passes == 1:
                report.update(self._pass(articles, output_dir, sources, "", 0, "pass 1/1"))
            else:
                report["pass_results"] = []
                for index in range(passes):
                    step = f"pass-{index + 1}"
                    report["pass_results"].append(self._pass(
                        articles, output_dir / step, sources, step + "/", index,
                        f"pass {index + 1}/{passes}"))
                step = "vote"
                vote = self._vote(articles, output_dir, passes)
                report["vote"] = vote["counts"]
                report["composition"] = vote["composition"]
                LOG.info("vote: %d unanimous, %d majority, %d tie(s), %d dropped",
                         *(vote["counts"][name] for name in
                           ("unanimous", "majority", "label_tie", "dropped_minority")))

            step = "export"
            final = output_dir / "final"
            export = export_scores(articles=articles, universe=self.universe,
                                   composition_dir=output_dir / "compose", output_dir=final,
                                   news_path=news_path, universe_path=universe_path,
                                   allow_alerts=True)
            LOG.info("export: %d rows in entities.csv, %d tickers in scores.csv",
                     export["counts"]["entities"], export["counts"]["tickers"])
            report["outputs"] = {"entities_csv": str(final / "entities.csv"),
                                 "scores_csv": str(final / "scores.csv"), **export["counts"]}
            summary = summarize_usage(self.reports, len(articles))
            # Replayed results were paid in an earlier run and are not counted here.
            report["cost"] = {**summary,
                              "includes_local_cache_replays": bool(summary["local_cache_hits"]),
                              "budget_committed_usd": str(self.committed)}
            report["status"] = ("completed" if report["composition"]["ready_for_scoring"]
                                else "completed_with_alerts")
        except BaseException:
            report.update(status="failed", failed_step=step,
                          budget_committed_usd=str(self.committed))
            write_json(output_dir / "run_report.json", report)
            raise
        write_json(output_dir / "run_report.json", report)
        return report
