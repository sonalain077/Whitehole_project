"""Decimal accounting, provider cache categories and conservative reservations."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation

from .classification import json_text
from .errors import RunError

PRICING_SOURCE = "https://developers.openai.com/api/docs/models/gpt-5.6-terra"
PRICING_CHECKED = "2026-10-12"


def positive_decimal(value: str) -> Decimal:
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("Budget must be a positive finite USD amount.") from exc
    if not result.is_finite() or result <= 0:
        raise ValueError("Budget must be a positive finite USD amount.")
    return result


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int
    cached_tokens: int
    cache_write_tokens: int
    output_tokens: int

    @classmethod
    def from_response(cls, response: dict) -> TokenUsage:
        try:
            usage = response["usage"]
            details = usage["input_tokens_details"]
            values = (usage["input_tokens"], details["cached_tokens"],
                      details["cache_write_tokens"], usage["output_tokens"])
            if not all(type(v) is int and v >= 0 for v in values):
                raise ValueError
            if values[1] + values[2] > values[0]:
                raise ValueError
            return cls(*values)
        except (KeyError, TypeError, ValueError) as exc:
            raise RunError("Missing or invalid API token usage; cost is unknown. Run stopped.") from exc

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Pricing:
    # Standard tier, short context; cache writes are a separate input category.
    input_usd: Decimal = Decimal("2")
    cached_usd: Decimal = Decimal("0.20")
    cache_write_usd: Decimal = Decimal("2.50")
    output_usd: Decimal = Decimal("12")

    def cost(self, usage: TokenUsage) -> Decimal:
        if usage.input_tokens > 272000:
            raise RunError("Long-context billing is outside this run's pricing policy.")
        ordinary = usage.input_tokens - usage.cached_tokens - usage.cache_write_tokens
        return (ordinary * self.input_usd + usage.cached_tokens * self.cached_usd
                + usage.cache_write_tokens * self.cache_write_usd
                + usage.output_tokens * self.output_usd) / Decimal(1_000_000)

    def reservation(self, request: dict) -> tuple[int, Decimal]:
        # UTF-8 bytes plus framing allowance deliberately overestimates ordinary text.
        # This is a local estimate, not a provider-enforced billing ceiling.
        estimated_input = len(json_text(request).encode("utf-8")) + 4096
        if estimated_input > 200000:
            raise RunError("Request exceeds the conservative short-context input limit.")
        amount = (estimated_input * max(self.input_usd, self.cache_write_usd)
                  + request["max_output_tokens"] * self.output_usd) / Decimal(1_000_000)
        return estimated_input, amount

    def to_dict(self) -> dict:
        return {"usd_per_million_tokens": {k: str(v) for k, v in asdict(self).items()},
                "source": PRICING_SOURCE, "checked_on": PRICING_CHECKED,
                "service_tier": "default", "context": "short"}


TOKEN_FIELDS = ("input_tokens", "cached_tokens", "cache_write_tokens", "output_tokens")


def summarize_usage(steps: dict[str, dict], article_count: int) -> dict:
    """Aggregate the usage.json reports of one run: calls, retries, tokens and cost."""
    if not steps or article_count < 1:
        raise ValueError("A usage summary needs at least one step and one article.")
    tokens = {name: sum(report["known_token_totals"][name] for report in steps.values())
              for name in TOKEN_FIELDS}
    attempts = [attempt for report in steps.values() for attempt in report["attempts"]]
    known = sum((Decimal(report["known_cost_usd"]) for report in steps.values()), Decimal(0))
    unknown = sum(report["unknown_cost_attempts"] for report in steps.values())
    pricing = Pricing()
    ordinary = tokens["input_tokens"] - tokens["cached_tokens"] - tokens["cache_write_tokens"]
    by_category = {"input": ordinary * pricing.input_usd,
                   "cached_input": tokens["cached_tokens"] * pricing.cached_usd,
                   "cache_write": tokens["cache_write_tokens"] * pricing.cache_write_usd,
                   "output": tokens["output_tokens"] * pricing.output_usd}
    return {"articles": article_count,
            "api_calls": sum(report["api_calls"] for report in steps.values()),
            "retries": sum(attempt["attempt"] > 1 for attempt in attempts),
            "local_cache_hits": sum(report["local_cache_hits"] for report in steps.values()),
            "unknown_cost_attempts": unknown,
            "api_seconds": round(sum(attempt.get("duration_seconds", 0) for attempt in attempts), 1),
            "token_totals": tokens,
            "cost_by_category_usd": {name: str(value / Decimal(1_000_000))
                                     for name, value in by_category.items()},
            "known_cost_usd": str(known),
            "total_cost_usd": None if unknown else str(known),
            "cost_per_article_usd": None if unknown else str(known / article_count),
            "steps": {name: {"api_calls": report["api_calls"],
                             "known_cost_usd": report["known_cost_usd"]}
                      for name, report in steps.items()}}


def format_usage(summary: dict) -> str:
    """Render a usage summary for the terminal."""
    tokens = summary["token_totals"]
    ordinary = tokens["input_tokens"] - tokens["cached_tokens"] - tokens["cache_write_tokens"]
    costs = summary["cost_by_category_usd"]
    lines = [
        f"Articles: {summary['articles']}",
        f"API calls: {summary['api_calls']} (retries {summary['retries']}, local cache replays "
        f"{summary['local_cache_hits']}, unknown-cost attempts {summary['unknown_cost_attempts']})",
        f"API time: {summary['api_seconds']} s",
        f"Input tokens: {tokens['input_tokens']:,} (cache read {tokens['cached_tokens']:,}, "
        f"cache write {tokens['cache_write_tokens']:,}, ordinary {ordinary:,})",
        f"Output tokens: {tokens['output_tokens']:,}",
        f"Cost USD: total {summary['total_cost_usd'] or 'unknown (known ' + summary['known_cost_usd'] + ')'}"
        f", per article {summary['cost_per_article_usd'] or 'unknown'}",
        f"  by category: input {costs['input']} | cache read {costs['cached_input']} | "
        f"cache write {costs['cache_write']} | output {costs['output']}",
    ]
    if summary["local_cache_hits"]:
        lines.append(f"  warning: not a full uncached run; {summary['local_cache_hits']} result(s) "
                     "were replayed from the local cache and paid in an earlier run")
    lines.append("By step:")
    lines += [f"  {name:<16} {step['api_calls']:>4} call{'' if step['api_calls'] == 1 else 's'}"
              f"  {step['known_cost_usd']} USD" for name, step in summary["steps"].items()]
    return "\n".join(lines)


class Budget:
    def __init__(self, maximum: Decimal) -> None:
        if not maximum.is_finite() or maximum <= 0:
            raise ValueError("Budget must be positive and finite.")
        self.maximum = maximum
        self.committed = Decimal(0)

    def reserve(self, amount: Decimal) -> None:
        if self.committed + amount > self.maximum:
            raise RunError("Budget cannot cover another request; no call was made.")
        self.committed += amount

    def settle(self, reservation: Decimal, actual: Decimal) -> None:
        self.committed += actual - reservation
        if actual > reservation or self.committed > self.maximum:
            raise RunError("API consumption exceeded its local estimate; no further calls allowed.")
