import csv
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from decimal import Decimal
from pathlib import Path

from aie2609.cli import main
from aie2609.errors import RunError
from aie2609.pipeline import Pipeline
from tests.test_classification import api_response, sample_article, sample_entities, sample_universe
from tests.test_runner import FakeClient

APPLE_ONLY = {"entities": [sample_entities()["entities"][0]]}
JPM_ONLY = {"entities": [sample_entities()["entities"][1]]}


class PipelineTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.news = self.root / "news.json"
        self.universe_path = self.root / "sp500.csv"
        self.news.write_text("source", encoding="utf-8")
        self.universe_path.write_text("source", encoding="utf-8")
        self.output = self.root / "run"

    def run_pipeline(self, responses: list) -> tuple[dict, FakeClient]:
        client = FakeClient(responses)
        pipeline = Pipeline(client, sample_universe(), Decimal("1"), cache_root=self.root / "cache")
        report = pipeline.run([sample_article()], self.output, self.news, self.universe_path)
        return report, client

    def entities(self) -> list[dict]:
        with (self.output / "final" / "entities.csv").open(encoding="utf-8", newline="") as stream:
            return list(csv.DictReader(stream))

    def test_clean_classification_needs_no_review_and_writes_both_csv(self):
        report, client = self.run_pipeline([api_response()])
        self.assertEqual(client.calls, 1)
        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["reviews"], [])
        self.assertEqual([row["ticker"] for row in self.entities()], ["AAPL", "JPM"])
        self.assertTrue((self.output / "final" / "scores.csv").exists())
        self.assertEqual(report["cost"]["cost_per_article_usd"], "0.000529")
        self.assertEqual(report["cost"]["token_totals"], {
            "input_tokens": 100, "cached_tokens": 20, "cache_write_tokens": 10, "output_tokens": 30})
        self.assertEqual(report["cost"]["cost_by_category_usd"], {
            "input": "0.00014", "cached_input": "0.000004", "cache_write": "0.000025",
            "output": "0.00036"})
        saved = json.loads((self.output / "run_report.json").read_text(encoding="utf-8"))
        self.assertEqual(saved, report)

    def test_missing_mention_is_added_by_an_additions_only_review(self):
        report, client = self.run_pipeline([api_response(APPLE_ONLY), api_response()])
        self.assertEqual(client.calls, 2)
        self.assertEqual(report["reviews"][0]["status"], "applied")
        self.assertTrue(report["reviews"][0]["mode"].endswith("-additions-only"))
        self.assertEqual(report["reviews"][0]["blocking_before"], ["missing:JPM"])
        self.assertEqual(report["status"], "completed")
        self.assertEqual([row["ticker"] for row in self.entities()], ["AAPL", "JPM"])
        self.assertEqual(report["cost"]["api_calls"], 2)
        self.assertEqual(set(report["cost"]["steps"]), {"classify", "review/T001"})

    def test_usage_command_summarizes_an_existing_run_without_api(self):
        self.run_pipeline([api_response(APPLE_ONLY), api_response()])
        stream = io.StringIO()
        with redirect_stdout(stream):
            self.assertEqual(main(["usage", "--run-dir", str(self.output)]), 0)
        text = stream.getvalue()
        self.assertIn("API calls: 2 (retries 0", text)
        self.assertIn("per article 0.001058", text)
        self.assertIn("review/T001", text)

    def test_rejected_review_keeps_first_pass_and_exports_with_alerts(self):
        # Removing AAPL violates additions-only twice: the review is rejected, not applied.
        report, client = self.run_pipeline([api_response(APPLE_ONLY), api_response(JPM_ONLY),
                                            api_response(JPM_ONLY)])
        self.assertEqual(client.calls, 3)
        self.assertEqual(report["reviews"][0]["status"], "rejected")
        self.assertEqual(report["status"], "completed_with_alerts")
        self.assertEqual(report["composition"]["blocking_alerts"], 1)
        self.assertEqual([row["ticker"] for row in self.entities()], ["AAPL"])
        manifest = json.loads((self.output / "final" / "run_manifest.json").read_text(encoding="utf-8"))
        self.assertFalse(manifest["ready_for_scoring"])

    def test_three_passes_use_independent_replicas_and_vote(self):
        # Pass 2 drops JPM and turns AAPL neutral: the majority keeps both original pairs.
        neutral_apple = {"entities": [dict(APPLE_ONLY["entities"][0], label="neutral")]}
        reviewed = {"entities": neutral_apple["entities"] + JPM_ONLY["entities"]}
        # Calls: pass 1, pass 2 (JPM missing), pass 2 additions-only review, pass 3.
        client = FakeClient([api_response(), api_response(neutral_apple),
                             api_response(reviewed), api_response()])
        pipeline = Pipeline(client, sample_universe(), Decimal("1"), cache_root=self.root / "cache")
        report = pipeline.run([sample_article()], self.output, self.news, self.universe_path,
                              passes=3)
        # Pass 2 needs an additions-only review for the missing JPM: 4 calls in total.
        self.assertEqual(client.calls, 4)
        self.assertEqual(report["vote"], {"unanimous": 1, "majority": 1, "label_tie": 0,
                                          "dropped_minority": 0})
        self.assertEqual([(row["ticker"], row["label"]) for row in self.entities()],
                         [("AAPL", "positive"), ("JPM", "neutral")])
        votes = json.loads((self.output / "vote" / "vote_report.json").read_text(encoding="utf-8"))
        self.assertEqual(votes["pairs"][0]["votes"], ["positive", "neutral", "positive"])
        stream = io.StringIO()
        with redirect_stdout(stream):
            self.assertEqual(main(["usage", "--run-dir", str(self.output)]), 0)
        self.assertIn("pass-2/review/T001", stream.getvalue())

    def test_existing_output_directory_is_refused_before_any_call(self):
        self.output.mkdir()
        with self.assertRaises(RunError):
            self.run_pipeline([])
        self.assertFalse((self.output / "run_report.json").exists())


if __name__ == "__main__":
    unittest.main()
