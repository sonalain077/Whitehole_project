"""Sequential classification, validated cache and durable usage checkpoints."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from decimal import Decimal
from pathlib import Path
from typing import Callable, Protocol

from .classification import (
    MODEL, PROMPT_VERSION, build_request, cache_key, json_text, strict_json, validate_entities,
)
from .errors import ClassificationError, RunError
from .llm import TransportError, response_text
from .models import Article, Universe
from .usage import Budget, Pricing, TokenUsage

# Progress log: ids, steps, statuses and costs only, never article text or the key.
LOG = logging.getLogger("aie2609")


class Client(Protocol):
    def create(self, payload: dict) -> dict: ...


def write_json(path: Path, value: object) -> None:
    """Atomically replace one generated file (directories belong to this run)."""
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def with_validation_feedback(request: dict, reason: str) -> dict:
    """Retry payload: the original request plus our fixed validator diagnostic.

    ``reason`` comes from our validators (fixed messages), never from model text, so no
    rejected output is echoed back. The cache key stays that of the original request.
    """
    feedback = {"validation_feedback": (
        f"The application rejected your previous answer: {reason} Return the complete "
        "corrected JSON object. Copy every evidence excerpt character for character from "
        "the headline or the body, and give always-neutral roles the neutral label.")}
    return {**request, "input": [*request["input"], {"role": "user", "content": json_text(feedback)}]}


def preflight(articles: list[Article], universe: Universe, max_output_tokens: int, *,
              request_builder: Callable[[Article], dict] | None = None,
              prompt_version: str = PROMPT_VERSION) -> dict:
    pricing = Pricing()
    rows = []
    for article in articles:
        request = (request_builder(article) if request_builder else
                   build_request(article, universe, max_output_tokens))
        estimate, reservation = pricing.reservation(request)
        rows.append({"id": article.id, "estimated_input_token_bound": estimate,
                     "reservation_usd": str(reservation), "cache_key": cache_key(request)})
    return {"model": MODEL, "prompt_version": prompt_version, "articles": rows,
            "first_attempt_reservation_usd": str(sum(
                (Decimal(row["reservation_usd"]) for row in rows), Decimal(0))),
            "pricing": pricing.to_dict(),
            "note": "Local conservative estimates, not guaranteed provider billing ceilings; retries are extra."}


class Classifier:
    prompt_version = PROMPT_VERSION
    log_label = "classify"
    log_each_article = True

    def request(self, article: Article) -> dict:
        return build_request(article, self.universe, self.max_output_tokens)

    def extra_artifacts(self, articles: list[Article], results: list[dict]) -> dict:
        return {}

    def __init__(self, client: Client, universe: Universe, cache_dir: Path,
                 maximum: Decimal, *, max_attempts: int = 2,
                 max_output_tokens: int = 4096, replica: int = 0) -> None:
        if type(max_attempts) is not int or not 1 <= max_attempts <= 3:
            raise ValueError("max_attempts must be between 1 and 3.")
        if type(replica) is not int or replica < 0:
            raise ValueError("replica must be a non-negative integer.")
        self.replica = replica
        self.client = client
        self.universe = universe
        self.cache_dir = cache_dir
        self.budget = Budget(maximum)
        self.pricing = Pricing()
        self.max_attempts = max_attempts
        self.max_output_tokens = max_output_tokens
        self.attempts: list[dict] = []
        self.cache_hits = 0

    def usage_report(self, article_count: int, completed: int) -> dict:
        known_cost = sum((Decimal(a["cost_usd"]) for a in self.attempts
                          if a.get("cost_usd") is not None), Decimal(0))
        unknown = sum(a.get("cost_usd") is None for a in self.attempts)
        totals = {name: sum(a.get("usage", {}).get(name, 0) for a in self.attempts)
                  for name in ("input_tokens", "cached_tokens", "cache_write_tokens", "output_tokens")}
        # A cached replay is not a measurement of the original complete classification cost.
        full_cost = (str(known_cost / article_count)
                     if article_count and completed == article_count and not unknown and not self.cache_hits
                     else None)
        return {"schema_version": 1, "model": MODEL, "pricing": self.pricing.to_dict(), "api_calls": len(self.attempts),
                "local_cache_hits": self.cache_hits, "articles_requested": article_count,
                "articles_completed": completed, "known_token_totals": totals,
                "unknown_cost_attempts": unknown, "known_cost_usd": str(known_cost),
                "total_cost_usd": None if unknown else str(known_cost),
                "full_uncached_run_cost_per_article_usd": full_cost,
                "budget_usd": str(self.budget.maximum),
                "budget_committed_usd": str(self.budget.committed), "attempts": self.attempts}

    def _validate_response(self, response: dict, article: Article) -> list[dict[str, str]]:
        # The model page currently lists this exact identifier only; no silent substitution.
        if response.get("model") != MODEL:
            raise RunError("Unexpected response model; run stopped without fallback.")
        if response.get("service_tier") != "default":
            raise RunError("Unexpected billing tier; run stopped.")
        return validate_entities(strict_json(response_text(response)), article, self.universe,
                                 require_role=True)

    def cache_key(self, request: dict) -> str:
        """Replica 0 shares the ordinary cache; other replicas are independent samples."""
        key = cache_key(request)
        if self.replica:
            key = hashlib.sha256(f"{key}:replica-{self.replica}".encode("utf-8")).hexdigest()
        return key

    def classify(self, article: Article, checkpoint) -> list[dict[str, str]]:
        request = self.request(article)
        key = self.cache_key(request)
        cached_path = self.cache_dir / f"{key}.json"
        if cached_path.exists():
            try:
                cached = strict_json(cached_path.read_text(encoding="utf-8"))
                if not isinstance(cached, dict) or set(cached) != {"version", "key", "response"}:
                    raise ClassificationError("Invalid cache structure.")
                if cached["version"] != 1 or cached["key"] != key:
                    raise ClassificationError("Cache version or fingerprint mismatch.")
                response = cached["response"]
                if not isinstance(response, dict):
                    raise ClassificationError("Invalid cached response.")
                TokenUsage.from_response(response)
                result = self._validate_response(response, article)
            except (ClassificationError, UnicodeError, RunError) as exc:
                raise RunError("Cache validation failed; inspect or move that cache entry before retrying.") from exc
            self.cache_hits += 1
            checkpoint()
            return result

        estimated_input, reservation = self.pricing.reservation(request)
        payload = request
        for number in range(1, self.max_attempts + 1):
            self.budget.reserve(reservation)
            attempt = {"article_id": article.id, "attempt": number, "status": "in_flight",
                       "reservation_usd": str(reservation), "cost_usd": None,
                       "cache_key": key}
            self.attempts.append(attempt)
            checkpoint()  # Persist reservation BEFORE sending: interrupted calls stay visible.
            started = time.monotonic()
            try:
                response = self.client.create(payload)
            except TransportError as exc:
                attempt.update(status="transport_error", duration_seconds=round(time.monotonic() - started, 3))
                checkpoint()
                if exc.retryable and number < self.max_attempts:
                    # Unknown consumption remains reserved, never silently treated as free.
                    LOG.warning("%s %s: rate limited, retrying", self.log_label, article.id)
                    time.sleep(min(2 ** (number - 1), 4))
                    continue
                raise

            attempt["duration_seconds"] = round(time.monotonic() - started, 3)
            try:
                tokens = TokenUsage.from_response(response)
                attempt["usage"] = tokens.to_dict()
                if response.get("model") != MODEL or response.get("service_tier") != "default":
                    raise RunError("Unexpected model or billing tier; cost is unknown.")
                cost = self.pricing.cost(tokens)
                attempt["cost_usd"] = str(cost)
                response_id = response.get("id")
                if isinstance(response_id, str) and response_id.startswith("resp_") and len(response_id) < 200:
                    attempt["response_id"] = response_id
                self.budget.settle(reservation, cost)
                if tokens.input_tokens > estimated_input or tokens.output_tokens > self.max_output_tokens:
                    raise RunError("API usage exceeded request estimate or output cap; run stopped.")
            except RunError:
                attempt["status"] = "accounting_error"
                checkpoint()
                raise

            try:
                entities = self._validate_response(response, article)
            except ClassificationError as exc:
                attempt["status"] = "invalid_response"
                # Validators emit fixed diagnostics, never provider text or evidence.
                attempt["validation_error"] = str(exc)
                checkpoint()
                if number < self.max_attempts:
                    LOG.warning("%s %s: answer rejected (%s); retrying with the reason",
                                self.log_label, article.id, exc)
                    payload = with_validation_feedback(request, str(exc))
                    continue
                raise ClassificationError(
                    f"Article classification failed after bounded attempts: {exc}"
                ) from None

            attempt["status"] = "validated"
            checkpoint()
            # Keep only the validated text and usage, never reasoning or request credentials.
            compact = {"model": MODEL, "service_tier": "default", "status": "completed",
                       "usage": response["usage"], "output": [{"type": "message", "role": "assistant",
                       "content": [{"type": "output_text", "text": json_text({"entities": entities})}]}]}
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            write_json(cached_path, {"version": 1, "key": key, "response": compact})
            return entities
        raise RunError("Classification attempts exhausted.")

    def run(self, articles: list[Article], output_dir: Path, source_paths: list[Path]) -> dict:
        if not articles or len({a.id for a in articles}) != len(articles):
            raise ValueError("A run needs nonempty articles with unique IDs.")
        output = output_dir.resolve()
        cache = self.cache_dir.resolve()
        if output == cache or output in cache.parents or cache in output.parents:
            raise RunError("Run and cache directories must be separate.")
        for source in source_paths:
            resolved = source.resolve()
            if (resolved == output or output in resolved.parents
                    or resolved == cache or cache in resolved.parents):
                raise RunError("Run/cache paths must not contain or overwrite an input file.")
        # Calculate/validate all payloads before creating artifacts or making any call.
        preview = preflight(articles, self.universe, self.max_output_tokens,
                            request_builder=self.request, prompt_version=self.prompt_version)
        hashes = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in source_paths}
        output.mkdir(parents=True, exist_ok=False)
        results = []
        manifest = {"schema_version": 1, "status": "running", "model": MODEL,
                    "prompt_version": self.prompt_version, "replica": self.replica,
                    "source_sha256": hashes,
                    "article_ids": [a.id for a in articles], "preflight": preview}

        def checkpoint() -> None:
            write_json(output / "usage.json", self.usage_report(len(articles), len(results)))

        try:
            write_json(output / "run_manifest.json", manifest)
            checkpoint()
            for article in articles:
                calls, hits = len(self.attempts), self.cache_hits
                entities = self.classify(article, checkpoint)
                results.append({"id": article.id, "entities": entities})
                checkpoint()
                if self.log_each_article:
                    source = ("local cache" if self.cache_hits > hits
                              else f"{len(self.attempts) - calls} call(s)")
                    LOG.info("%s %d/%d %s: %d companies (%s; %s USD this step)",
                             self.log_label, len(results), len(articles), article.id,
                             len(entities), source,
                             self.usage_report(len(articles), len(results))["known_cost_usd"])
            for name, artifact in self.extra_artifacts(articles, results).items():
                write_json(output / name, artifact)
            write_json(output / "classifications.json", {"schema_version": 1, "articles": results})
            manifest["status"] = "completed"
            write_json(output / "run_manifest.json", manifest)
            return self.usage_report(len(articles), len(results))
        except BaseException:
            manifest["status"] = "failed"
            checkpoint()
            write_json(output / "run_manifest.json", manifest)
            raise
