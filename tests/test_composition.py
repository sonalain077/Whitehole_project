import hashlib
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from aie2609.composition import compose_classifications, quality_alerts
from aie2609.errors import RunError
from aie2609.models import Company, Universe
from tests.test_classification import sample_article, sample_entities, sample_universe


class CompositionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def _write_bundle(self, unresolved=None):
        article = sample_article()
        entities = sample_entities()["entities"]
        baseline = self.root / "baseline.json"
        baseline.write_text(json.dumps({"schema_version": 1, "articles": [
            {"id": article.id, "entities": entities}]}), encoding="utf-8")
        review = self.root / "review"
        review.mkdir()
        (review / "classifications.json").write_text(json.dumps({
            "schema_version": 1, "articles": [{"id": article.id, "entities": entities}]
        }), encoding="utf-8")
        baseline_hash = hashlib.sha256(baseline.read_bytes()).hexdigest()
        (review / "run_manifest.json").write_text(json.dumps({
            "status": "completed", "prompt_version": "test-review",
            "source_sha256": {str(baseline): baseline_hash}
        }), encoding="utf-8")
        (review / "review_changes.json").write_text(json.dumps({
            "schema_version": 2, "articles": [{
                "id": article.id, "unresolved_hints_after": unresolved or [],
                "added": [], "removed": [], "label_changes": []}]
        }), encoding="utf-8")
        candidate = self.root / "candidate.json"
        changed = [dict(entity) for entity in entities]
        changed[0]["label"] = "neutral"
        candidate.write_text(json.dumps({"schema_version": 1, "articles": [
            {"id": article.id, "entities": changed}]}), encoding="utf-8")
        return article, baseline, review, candidate

    def test_anchor_rejects_social_x_but_accepts_full_block_name(self):
        universe = Universe((Company("XYZ", "Block, Inc.", "sector", "HQ", "2000-01-01",
                                     ("XYZ",)),), 1, {}, ())
        false_article = replace(sample_article(), headline="Tesla event",
                                body="The company posted the update on X.")
        false_entity = [{"ticker": "XYZ", "label": "neutral", "evidence": false_article.body}]
        alerts = quality_alerts(false_article, false_entity, universe)
        self.assertEqual(alerts["blocking"], ["forbidden_alias:XYZ:X"])
        self.assertEqual(alerts["advisory"], ["unanchored_entity:XYZ"])
        true_article = replace(sample_article(), headline="Block update",
                               body="Block, Inc. raised its earnings guidance.")
        true_entity = [{"ticker": "XYZ", "label": "positive", "evidence": true_article.body}]
        self.assertEqual(quality_alerts(true_article, true_entity, universe)["blocking"], [])

    def test_non_neutral_analyst_evidence_without_entity_anchor_is_advisory(self):
        article = replace(
            sample_article(),
            headline="JPMorgan issues a research note",
            body="Analysts at the bank downgraded Acme and cut its price target.",
        )
        entity = [{"ticker": "JPM", "label": "negative", "evidence": article.body}]
        alerts = quality_alerts(article, entity, sample_universe())
        self.assertIn("possible_role_transfer:JPM", alerts["advisory"])
        self.assertEqual(alerts["blocking"], [])

    def test_composition_applies_review_and_blocks_candidate_disagreement(self):
        article, baseline, review, candidate = self._write_bundle()
        output = self.root / "out"
        report = compose_classifications(
            articles=[article], universe=sample_universe(), baseline_path=baseline,
            review_dirs=[review], candidate_path=candidate, output_dir=output)
        self.assertFalse(report["ready_for_scoring"])
        self.assertEqual(report["counts"]["reviewed_articles"], 1)
        self.assertEqual(report["counts"]["candidate_conflicts"], 1)
        self.assertEqual(len(report["candidate_quality"]), 1)
        self.assertEqual(report["candidate_changes"][0]["label_changes"], [
            {"ticker": "AAPL", "before": "positive", "after": "neutral"}])
        saved = json.loads((output / "composition_report.json").read_text(encoding="utf-8"))
        self.assertEqual(saved, report)

    def test_unresolved_review_is_never_composed(self):
        article, baseline, review, candidate = self._write_bundle(["AAPL"])
        with self.assertRaisesRegex(RunError, "unresolved"):
            compose_classifications(
                articles=[article], universe=sample_universe(), baseline_path=baseline,
                review_dirs=[review], candidate_path=candidate, output_dir=self.root / "out")

    def test_mismatched_review_change_report_is_rejected(self):
        article, baseline, review, candidate = self._write_bundle()
        reviewed_path = review / "classifications.json"
        payload = json.loads(reviewed_path.read_text(encoding="utf-8"))
        payload["articles"][0]["entities"][0]["label"] = "neutral"
        reviewed_path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(RunError, "does not match"):
            compose_classifications(
                articles=[article], universe=sample_universe(), baseline_path=baseline,
                review_dirs=[review], candidate_path=None, output_dir=self.root / "out")


if __name__ == "__main__":
    unittest.main()
