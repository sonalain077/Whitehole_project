"""Validated in-memory data structures."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class AuditIssue:
    code: str
    message: str
    source: str
    record_id: str | None = None

    def to_dict(self) -> dict[str, str]:
        result = {"code": self.code, "message": self.message, "source": self.source}
        if self.record_id is not None:
            result["record_id"] = self.record_id
        return result


@dataclass(frozen=True, slots=True)
class Article:
    id: str
    published_at: datetime
    date_raw: str
    headline_raw: str
    body_raw: str
    headline: str
    body: str


@dataclass(frozen=True, slots=True)
class Company:
    ticker: str
    security: str
    gics_sector: str
    headquarters: str
    date_added: str
    aliases: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Universe:
    companies: tuple[Company, ...]
    source_row_count: int
    ticker_aliases: dict[str, str]
    issues: tuple[AuditIssue, ...]

    @property
    def tickers(self) -> frozenset[str]:
        return frozenset(company.ticker for company in self.companies)

    def canonicalize(self, ticker: str) -> str:
        return self.ticker_aliases.get(ticker, ticker)


@dataclass(frozen=True, slots=True)
class NewsDataset:
    articles: tuple[Article, ...]
    issues: tuple[AuditIssue, ...]


@dataclass(frozen=True, slots=True)
class AuditReport:
    article_count: int
    source_company_count: int
    canonical_company_count: int
    earliest_article: str
    latest_article: str
    ticker_aliases: dict[str, str]
    issues: tuple[AuditIssue, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "ok",
            "articles": self.article_count,
            "companies": {
                "source_rows": self.source_company_count,
                "canonical": self.canonical_company_count,
            },
            "article_dates": {
                "earliest": self.earliest_article,
                "latest": self.latest_article,
                "timezone": "America/New_York",
            },
            "ticker_aliases": dict(sorted(self.ticker_aliases.items())),
            "issues": [issue.to_dict() for issue in self.issues],
        }
