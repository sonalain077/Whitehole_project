"""Read-only audit of both supplied inputs."""

from __future__ import annotations

from pathlib import Path

from .ingestion import load_news, load_universe
from .models import AuditReport


def audit_inputs(news_path: str | Path, universe_path: str | Path) -> AuditReport:
    news = load_news(news_path)
    universe = load_universe(universe_path)
    ordered = sorted(news.articles, key=lambda article: article.published_at)
    return AuditReport(
        article_count=len(news.articles),
        source_company_count=universe.source_row_count,
        canonical_company_count=len(universe.companies),
        earliest_article=ordered[0].date_raw.strip(),
        latest_article=ordered[-1].date_raw.strip(),
        ticker_aliases=universe.ticker_aliases,
        issues=news.issues + universe.issues,
    )
