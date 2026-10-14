import csv
import tempfile
import unittest
from pathlib import Path

from aie2609.evaluation import disagreement_rows, evaluate_annotations, prepare_evaluation
from tests.test_classification import sample_article, sample_entities


class HumanEvaluationTests(unittest.TestCase):
    def test_disagreements_include_label_changes_and_absence(self):
        article = sample_article()
        final = {article.id: sample_entities()["entities"]}
        candidate = {article.id: [
            {"ticker": "AAPL", "label": "neutral", "evidence": article.headline},
        ]}
        rows = disagreement_rows([article], final, candidate)
        self.assertEqual([(row["ticker"], row["final_label"], row["candidate_label"])
                          for row in rows],
                         [("AAPL", "positive", "neutral"),
                          ("JPM", "neutral", "absent")])

    def test_prepare_and_score_partial_human_review(self):
        article = sample_article()
        final = {article.id: sample_entities()["entities"]}
        candidate = {article.id: [
            {"ticker": "AAPL", "label": "neutral", "evidence": article.headline},
        ]}
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "evaluation"
            report = prepare_evaluation(
                articles=[article], final=final, candidate=candidate,
                cases=[f"{article.id}:AAPL", f"{article.id}:JPM"], output_dir=output)
            self.assertEqual(report["disagreements"], 2)
            sample = output / "sample.csv"
            with sample.open("r", encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
                fields = list(rows[0])
            rows[0]["human_decision"] = "neutral"
            rows[1]["human_decision"] = "uncertain"
            with sample.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)
            result = evaluate_annotations(sample)
            self.assertEqual(result["answered"], 1)
            self.assertEqual(result["uncertain"], 1)
            self.assertEqual(result["final_correct"], 0)
            self.assertEqual(result["candidate_correct"], 1)

if __name__ == "__main__":
    unittest.main()
