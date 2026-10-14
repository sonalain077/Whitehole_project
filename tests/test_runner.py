from __future__ import annotations

import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from aie2609.errors import ClassificationError, RunError
from aie2609.llm import TransportError
from aie2609.runner import Classifier
from tests.test_classification import api_response, sample_article, sample_universe


class FakeClient:
    def __init__(self, responses: list) -> None:
        self.responses = iter(responses)
        self.calls = 0

    def create(self, payload: dict) -> dict:
        self.calls += 1
        value = next(self.responses)
        if isinstance(value, BaseException):
            raise value
        return value


class RunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cache = self.root / "cache"
        self.output = self.root / "run"
        self.article = sample_article()
        self.universe = sample_universe()

    def classifier(self, responses: list, budget="1", **kwargs) -> Classifier:
        return Classifier(FakeClient(responses), self.universe, self.cache, Decimal(budget), **kwargs)

    def report(self) -> dict:
        return json.loads((self.output / "usage.json").read_text(encoding="utf-8"))

    def test_success_persists_validated_results_usage_and_completion(self) -> None:
        runner = self.classifier([api_response()])
        report = runner.run([self.article], self.output, [])
        self.assertEqual(report["api_calls"], 1)
        self.assertEqual(report["total_cost_usd"], "0.000529")
        self.assertEqual(report["full_uncached_run_cost_per_article_usd"], "0.000529")
        result = json.loads((self.output / "classifications.json").read_text())
        self.assertEqual(result["articles"][0]["id"], "T001")
        self.assertEqual(json.loads((self.output / "run_manifest.json").read_text())["status"], "completed")

    def test_cache_replay_is_validated_and_makes_no_calls(self) -> None:
        self.classifier([api_response()]).run([self.article], self.output, [])
        replay = self.classifier([])
        report = replay.run([self.article], self.root / "replay", [])
        self.assertEqual(report["api_calls"], 0)
        self.assertEqual(report["local_cache_hits"], 1)
        self.assertEqual(report["total_cost_usd"], "0")
        self.assertIsNone(report["full_uncached_run_cost_per_article_usd"])

    def test_tampered_cache_is_rejected_without_rebilling(self) -> None:
        self.classifier([api_response()]).run([self.article], self.output, [])
        cache_path = next(self.cache.glob("*.json"))
        cached = json.loads(cache_path.read_text())
        cached["response"]["output"][0]["content"][0]["text"] = '{"entities":[{"ticker":"FAKE"}]}'
        cache_path.write_text(json.dumps(cached))
        replay = self.classifier([])
        with self.assertRaisesRegex(RunError, "Cache validation"):
            replay.run([self.article], self.root / "replay", [])
        self.assertEqual(replay.client.calls, 0)

    def test_invalid_response_is_charged_before_retry(self) -> None:
        runner = self.classifier([api_response({"wrong": []}), api_response()])
        report = runner.run([self.article], self.output, [])
        self.assertEqual(report["api_calls"], 2)
        self.assertEqual(report["total_cost_usd"], "0.001058")
        self.assertEqual(report["attempts"][0]["status"], "invalid_response")

    def test_retry_sends_fixed_validator_feedback_but_caches_original_key(self) -> None:
        sent = []
        runner = self.classifier([api_response({"wrong": []}), api_response()])
        original_create = runner.client.create
        def create(payload):
            sent.append(payload)
            return original_create(payload)
        runner.client.create = create
        runner.run([self.article], self.output, [])
        self.assertEqual(len(sent[0]["input"]), 2)
        feedback = json.loads(sent[1]["input"][-1]["content"])["validation_feedback"]
        self.assertIn("Response must contain exactly the entities field.", feedback)
        self.assertNotIn("wrong", feedback)
        replay = self.classifier([])
        self.assertEqual(replay.run([self.article], self.root / "replay", [])["local_cache_hits"], 1)

    def test_repeated_invalid_responses_fail_without_final_artifact(self) -> None:
        runner = self.classifier([api_response({"wrong": []})] * 2)
        with self.assertRaises(ClassificationError):
            runner.run([self.article], self.output, [])
        self.assertFalse((self.output / "classifications.json").exists())
        self.assertEqual(self.report()["api_calls"], 2)
        self.assertEqual(json.loads((self.output / "run_manifest.json").read_text())["status"], "failed")

    def test_insufficient_budget_prevents_any_call(self) -> None:
        runner = self.classifier([], budget="0.000001")
        with self.assertRaisesRegex(RunError, "Budget"):
            runner.run([self.article], self.output, [])
        self.assertEqual(runner.client.calls, 0)

    def test_validation_failure_records_reason_without_model_text(self) -> None:
        payload = {"entities": [{"ticker": "AAPL", "role": "subject", "label": "positive",
                                  "evidence": "private-invalid-provider-excerpt"}]}
        runner = self.classifier([api_response(payload)], max_attempts=1)
        with self.assertRaisesRegex(ClassificationError, "not an exact excerpt") as caught:
            runner.run([self.article], self.output, [])
        report = self.report()
        self.assertEqual(report['attempts'][0]['validation_error'],
                         'Evidence is not an exact excerpt from this article.')
        self.assertNotIn('private-invalid-provider-excerpt', json.dumps(report))
        self.assertNotIn('private-invalid-provider-excerpt', str(caught.exception))

    def test_timeout_has_unknown_cost_retains_reservation_and_never_retries(self) -> None:
        runner = self.classifier([TransportError("timeout")])
        with self.assertRaises(TransportError):
            runner.run([self.article], self.output, [])
        report = self.report()
        self.assertEqual(report["api_calls"], 1)
        self.assertIsNone(report["total_cost_usd"])
        self.assertGreater(Decimal(report["budget_committed_usd"]), 0)

    def test_rate_limit_retry_keeps_unknown_consumption_reserved(self) -> None:
        runner = self.classifier([TransportError("rate limit", retryable=True), api_response()])
        with patch("aie2609.runner.time.sleep"):
            report = runner.run([self.article], self.output, [])
        self.assertEqual(report["api_calls"], 2)
        self.assertIsNone(report["total_cost_usd"])
        self.assertEqual(report["unknown_cost_attempts"], 1)

    def test_missing_usage_stops_even_with_valid_classification(self) -> None:
        response = api_response()
        del response["usage"]
        runner = self.classifier([response])
        with self.assertRaisesRegex(RunError, "token usage"):
            runner.run([self.article], self.output, [])
        self.assertIsNone(self.report()["total_cost_usd"])
        self.assertEqual(runner.client.calls, 1)

    def test_other_model_or_tier_is_rejected(self) -> None:
        for field, value in [("model", "another-model"), ("service_tier", "priority")]:
            response = api_response()
            response[field] = value
            with self.subTest(field=field), self.assertRaises(RunError):
                self.classifier([response]).run([self.article], self.root / field, [])

    def test_checkpoint_exists_before_client_call(self) -> None:
        runner = self.classifier([])
        def create(payload):
            self.assertEqual(self.report()["attempts"][0]["status"], "in_flight")
            raise KeyboardInterrupt
        runner.client.create = create
        with self.assertRaises(KeyboardInterrupt):
            runner.run([self.article], self.output, [])
        self.assertIsNone(self.report()["total_cost_usd"])

    def test_missing_billing_tier_is_not_assumed_free_or_standard(self) -> None:
        response = api_response()
        del response["service_tier"]
        runner = self.classifier([response])
        with self.assertRaises(RunError):
            runner.run([self.article], self.output, [])
        self.assertIsNone(self.report()["total_cost_usd"])
        self.assertEqual(runner.client.calls, 1)

    def test_existing_output_and_input_collisions_make_no_calls(self) -> None:
        self.output.mkdir()
        runner = self.classifier([])
        with self.assertRaises(FileExistsError):
            runner.run([self.article], self.output, [])
        with self.assertRaises(RunError):
            runner.run([self.article], self.root / "new", [self.root / "new" / "input.json"])
        with self.assertRaises(RunError):
            runner.run([self.article], self.cache / "nested", [])
        self.assertEqual(runner.client.calls, 0)
