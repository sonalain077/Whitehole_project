"""Command-line interface."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from . import __version__
from .audit import audit_inputs
from .config import load_local_api_key
from .composition import compose_classifications
from .errors import ClassificationError, DataValidationError, RunError
from .evaluation import evaluate_annotations, prepare_evaluation
from .ingestion import load_news, load_universe
from .llm import ResponsesClient
from .pipeline import Pipeline
from .reference import prepare_reference, score_reference
from .runner import Classifier, preflight
from .scoring import export_scores
from .review import (ADDITIONS_ONLY_VERSION, ALIAS_CONFIG_PATH, REVIEW_VERSION, ReviewClassifier,
                     build_review_request, load_initial, review_reasons)
from .classification import strict_json
from .usage import format_usage, positive_decimal, summarize_usage


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aie2609",
        description="Validate and process the supplied company-news sentiment dataset.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser(
        "run", help="end to end: classify every article, review blocking alerts, write both CSV files")
    run.add_argument("--news", default="news.json")
    run.add_argument("--universe", default="sp500.csv")
    run.add_argument("--max-cost-usd", type=positive_decimal, help="explicit USD budget for the whole run")
    run.add_argument("--output-dir", type=Path,
                     help="new run directory (default: output/run-<UTC timestamp>)")
    run.add_argument("--dry-run", action="store_true", help="preview classification requests, no API or files")
    # Defaults are the retained configuration (measured best in review/reference-v1).
    run.add_argument("--max-attempts", type=int, choices=(1, 2, 3), default=3)
    run.add_argument("--max-output-tokens", type=int, default=4096)
    run.add_argument("--passes", type=int, choices=(1, 3, 5), default=3,
                     help="independent passes combined by majority vote (default 3; cost x passes)")
    usage = commands.add_parser("usage", help="summarize calls, tokens and cost of a run directory without API")
    usage.add_argument("--run-dir", type=Path, required=True,
                       help="a `run` directory or a single classify/review run directory")
    usage.add_argument("--json", action="store_true", help="print a machine-readable summary")
    audit = commands.add_parser("audit", help="validate inputs without calling an API")
    audit.add_argument("--news", default="news.json", help="path to the article JSON file")
    audit.add_argument("--universe", default="sp500.csv", help="path to the S&P 500 CSV file")
    audit.add_argument("--json", action="store_true", help="print a machine-readable report")
    classify = commands.add_parser("classify", help="classify a bounded selection; API calls require a budget")
    classify.add_argument("--news", default="news.json")
    classify.add_argument("--universe", default="sp500.csv")
    selection = classify.add_mutually_exclusive_group()
    selection.add_argument("--ids", nargs="+", help="explicit article IDs for the review sample")
    selection.add_argument("--limit", type=int, default=3, help="number of articles sorted by ID (default: 3)")
    classify.add_argument("--dry-run", action="store_true", help="preview requests and reservations, no API or files")
    classify.add_argument("--max-cost-usd", type=positive_decimal, help="explicit per-run USD budget")
    classify.add_argument("--output-dir", type=Path, help="new, separate run directory (must not exist)")
    classify.add_argument("--max-attempts", type=int, choices=(1, 2, 3), default=2)
    classify.add_argument("--max-output-tokens", type=int, default=4096)
    review = commands.add_parser("review", help="review alerted articles in an existing classifications file")
    review.add_argument("--news", default="news.json")
    review.add_argument("--universe", default="sp500.csv")
    review.add_argument("--classifications", type=Path, required=True)
    review_selection = review.add_mutually_exclusive_group()
    review_selection.add_argument("--all", action="store_true",
                                  help="review every baseline article instead of alerts only")
    review_selection.add_argument("--ids", nargs="+",
                                  help="review only these baseline article IDs")
    review.add_argument("--additions-only", action="store_true",
                        help="reject any removal or existing-label change")
    review.add_argument("--dry-run", action="store_true")
    review.add_argument("--max-cost-usd", type=positive_decimal)
    review.add_argument("--output-dir", type=Path)
    review.add_argument("--max-attempts", type=int, choices=(1, 2, 3), default=2)
    review.add_argument("--max-output-tokens", type=int, default=4096)
    compose = commands.add_parser("compose", help="compose validated reviews and audit conflicts without API")
    compose.add_argument("--news", default="news.json")
    compose.add_argument("--universe", default="sp500.csv")
    compose.add_argument("--baseline", type=Path, required=True)
    compose.add_argument("--review-dir", type=Path, action="append", default=[])
    compose.add_argument("--candidate", type=Path)
    compose.add_argument("--output-dir", type=Path, required=True)
    export = commands.add_parser("export", help="calculate scores and write final CSV files without API")
    export.add_argument("--news", default="news.json")
    export.add_argument("--universe", default="sp500.csv")
    export.add_argument("--composition-dir", type=Path, required=True)
    export.add_argument("--output-dir", type=Path, required=True)
    prepare = commands.add_parser(
        "prepare-evaluation", help="prepare disagreements and an editable human review sample")
    prepare.add_argument("--news", default="news.json")
    prepare.add_argument("--universe", default="sp500.csv")
    prepare.add_argument("--final", type=Path, required=True)
    prepare.add_argument("--candidate", type=Path, required=True)
    prepare.add_argument("--cases", nargs="+", required=True,
                         help="ARTICLE_ID:TICKER disagreements to include")
    prepare.add_argument("--output-dir", type=Path, required=True)
    evaluate = commands.add_parser(
        "evaluate", help="score final and candidate proposals against human decisions")
    evaluate.add_argument("--sample", type=Path, required=True)
    reference = commands.add_parser(
        "prepare-reference", help="blind cases: every disagreement between versions plus spot checks")
    reference.add_argument("--news", default="news.json")
    reference.add_argument("--universe", default="sp500.csv")
    reference.add_argument("--version", action="append", required=True, metavar="NAME=PATH",
                           help="a complete classifications.json; repeat for each version")
    reference.add_argument("--spot-checks", type=int, default=25)
    reference.add_argument("--seed", type=int, default=20260929)
    reference.add_argument("--output-dir", type=Path, required=True)
    score = commands.add_parser("score-reference", help="estimate each version's accuracy")
    score.add_argument("--dir", type=Path, required=True)
    return parser


def _print_human(report: dict[str, object]) -> None:
    companies = report["companies"]
    dates = report["article_dates"]
    assert isinstance(companies, dict) and isinstance(dates, dict)
    print("Input audit: OK")
    print(f"Articles: {report['articles']}")
    print(f"Companies: {companies['source_rows']} source rows, {companies['canonical']} canonical")
    print(f"Dates: {dates['earliest']} to {dates['latest']} ({dates['timezone']})")
    issues = report["issues"]
    assert isinstance(issues, list)
    print(f"Non-fatal issues: {len(issues)}")
    for issue in issues:
        assert isinstance(issue, dict)
        suffix = f" [{issue['record_id']}]" if "record_id" in issue else ""
        print(f"- {issue['code']}{suffix}: {issue['message']}")


def _usage_steps(run_dir: Path) -> tuple[dict[str, dict], int]:
    """Read the usage.json files of a `run` directory, or of one single-step run."""
    single = run_dir / "usage.json"
    passes = sorted(run_dir.glob("pass-*"), key=lambda path: int(path.name.split("-")[1]))
    paths = {"run": single} if single.exists() else {}
    for base, prefix in ([(path, path.name + "/") for path in passes] or [(run_dir, "")]):
        if single.exists():
            break
        paths[prefix + "classify"] = base / "classify" / "usage.json"
        paths.update({prefix + "review/" + path.parent.name: path
                      for path in sorted((base / "review").glob("*/usage.json"))})
    steps = {name: strict_json(path.read_text(encoding="utf-8")) for name, path in paths.items()}
    return steps, next(iter(steps.values()))["articles_requested"]


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare-reference":
            paths = {}
            for item in args.version:
                name, separator, path = item.partition("=")
                if not separator or not name or not path or name in paths:
                    raise ValueError("Each --version must be a unique NAME=PATH.")
                paths[name] = Path(path)
            news = load_news(args.news)
            report = prepare_reference(
                articles=list(news.articles), universe=load_universe(args.universe),
                version_paths=paths, spot_checks=args.spot_checks, seed=args.seed,
                output_dir=args.output_dir)
            print(json.dumps({"status": "completed", "output_dir": str(args.output_dir),
                              **{k: v for k, v in report.items() if k != "versions"}}, indent=2))
            return 0
        if args.command == "score-reference":
            print(json.dumps(score_reference(args.dir), indent=2))
            return 0
        if args.command == "usage":
            summary = summarize_usage(*_usage_steps(args.run_dir))
            print(json.dumps(summary, indent=2) if args.json else format_usage(summary))
            return 0
        if args.command == "run":
            news = load_news(args.news)
            universe = load_universe(args.universe)
            articles = sorted(news.articles, key=lambda a: a.id)
            if args.dry_run:
                print(json.dumps(preflight(articles, universe, args.max_output_tokens), indent=2))
                return 0
            if args.max_cost_usd is None:
                raise ValueError("A run requires --max-cost-usd; use --dry-run first.")
            output_dir = args.output_dir or Path("output") / f"run-{datetime.now(UTC):%Y%m%dT%H%M%SZ}"
            load_local_api_key()
            pipeline = Pipeline(ResponsesClient(), universe, args.max_cost_usd,
                                max_attempts=args.max_attempts,
                                max_output_tokens=args.max_output_tokens)
            report = pipeline.run(articles, output_dir, Path(args.news), Path(args.universe),
                                  passes=args.passes)
            print(f"Status: {report['status']} "
                  f"(blocking alerts: {report['composition']['blocking_alerts']})")
            print(f"Entities: {report['outputs']['entities_csv']} ({report['outputs']['entities']} rows)")
            print(f"Scores: {report['outputs']['scores_csv']} ({report['outputs']['tickers']} tickers)")
            print(format_usage(report["cost"]))
            print(f"Details: {output_dir / 'run_report.json'}")
            return 0
        if args.command == "evaluate":
            print(json.dumps(evaluate_annotations(args.sample), indent=2))
            return 0
        if args.command == "prepare-evaluation":
            news = load_news(args.news)
            universe = load_universe(args.universe)
            articles = list(news.articles)
            final = load_initial(args.final, articles, universe)
            candidate = load_initial(args.candidate, articles, universe)
            report = prepare_evaluation(
                articles=articles, final=final, candidate=candidate,
                cases=args.cases, output_dir=args.output_dir)
            print(json.dumps({"status": "completed", "output_dir": str(args.output_dir),
                              **report}, indent=2))
            return 0
        if args.command == "export":
            news_path = Path(args.news)
            universe_path = Path(args.universe)
            news = load_news(news_path)
            universe = load_universe(universe_path)
            report = export_scores(
                articles=list(news.articles), universe=universe,
                composition_dir=args.composition_dir, output_dir=args.output_dir,
                news_path=news_path, universe_path=universe_path)
            print(json.dumps({"status": "completed", "output_dir": str(args.output_dir),
                              **report["counts"]}, indent=2))
            return 0
        if args.command == "compose":
            news = load_news(args.news)
            universe = load_universe(args.universe)
            report = compose_classifications(
                articles=list(news.articles), universe=universe,
                baseline_path=args.baseline, review_dirs=args.review_dir,
                candidate_path=args.candidate, output_dir=args.output_dir)
            print(json.dumps({"status": "completed", "output_dir": str(args.output_dir),
                              "ready_for_scoring": report["ready_for_scoring"],
                              **report["counts"]}, indent=2))
            return 0
        if args.command == "review":
            news = load_news(args.news)
            universe = load_universe(args.universe)
            initial = load_initial(args.classifications, list(news.articles), universe)
            articles = sorted((a for a in news.articles if a.id in initial), key=lambda a:a.id)
            if args.ids:
                requested = set(args.ids)
                if len(requested) != len(args.ids) or requested - set(initial):
                    raise ValueError("Review IDs must be unique and present in the classifications file.")
                articles = [article for article in articles if article.id in requested]
            elif not args.all:
                articles = [a for a in articles if review_reasons(a, initial[a.id], universe)]
            if args.dry_run:
                preview = preflight(articles, universe, args.max_output_tokens,
                    request_builder=lambda a:build_review_request(
                        a, universe, initial[a.id], args.max_output_tokens,
                        args.additions_only),
                    prompt_version=(ADDITIONS_ONLY_VERSION
                                    if args.additions_only else REVIEW_VERSION))
                print(json.dumps(preview, indent=2))
                return 0
            if not articles:
                print(json.dumps({'status':'no_review_needed', 'articles':0, 'api_calls':0}))
                return 0
            if args.max_cost_usd is None or args.output_dir is None:
                raise ValueError("Review calls require --max-cost-usd and --output-dir; use --dry-run first.")
            load_local_api_key()
            runner = ReviewClassifier(ResponsesClient(), universe, Path('.cache/reviews'),
                                      args.max_cost_usd, initial=initial,
                                      additions_only=args.additions_only,
                                      max_attempts=args.max_attempts, max_output_tokens=args.max_output_tokens)
            report = runner.run(articles, args.output_dir,
                                [Path(args.news), Path(args.universe), args.classifications,
                                 ALIAS_CONFIG_PATH])
            print(json.dumps({'status':'completed', 'articles':report['articles_completed'],
                              'api_calls':report['api_calls'], 'total_cost_usd':report['total_cost_usd'],
                              'output_dir':str(args.output_dir)}, indent=2))
            return 0
        if args.command == "audit":
            report = audit_inputs(args.news, args.universe).to_dict()
            if args.json:
                print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                _print_human(report)
            return 0
        if args.command == "classify":
            news = load_news(args.news)
            universe = load_universe(args.universe)
            articles = sorted(news.articles, key=lambda a: a.id)
            if args.ids:
                if len(set(args.ids)) != len(args.ids) or set(args.ids) - {a.id for a in articles}:
                    raise ValueError("Requested IDs must be unique and present in news.json.")
                articles = [a for a in articles if a.id in set(args.ids)]
            else:
                if args.limit < 1 or args.limit > len(articles):
                    raise ValueError("limit must be between 1 and the number of input articles.")
                articles = articles[:args.limit]
            preview = preflight(articles, universe, args.max_output_tokens)
            if args.dry_run:
                print(json.dumps(preview, indent=2))
                return 0
            if args.max_cost_usd is None or args.output_dir is None:
                raise ValueError("Actual calls require --max-cost-usd and --output-dir; use --dry-run first.")
            load_local_api_key()
            classifier = Classifier(ResponsesClient(), universe, Path(".cache/classifications"),
                                    args.max_cost_usd, max_attempts=args.max_attempts,
                                    max_output_tokens=args.max_output_tokens)
            report = classifier.run(articles, args.output_dir, [Path(args.news), Path(args.universe)])
            print(json.dumps({"status": "completed", "output_dir": str(args.output_dir),
                              "articles": report["articles_completed"], "api_calls": report["api_calls"],
                              "total_cost_usd": report["total_cost_usd"]}, indent=2))
            return 0
    except DataValidationError as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2
    except (RunError, ClassificationError, ValueError) as exc:
        print(f"Run error: {exc}", file=sys.stderr)
        return 2
    except OSError:
        print("Run error: cannot read/write artifacts; choose a new writable output directory.", file=sys.stderr)
        return 2
    parser.error(f"unsupported command: {args.command}")
    return 2
