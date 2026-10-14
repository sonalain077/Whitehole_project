import csv
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from aie2609.errors import ClassificationError
from aie2609.reference import CASE_FIELDS, prepare_reference, score_reference
from tests.test_classification import sample_article, sample_entities, sample_universe


class ReferenceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        first = sample_article()
        second = replace(first, id="T002", headline="Alphabet expands.", body="Alphabet expands.")
        self.articles = [first, second]
        entities = sample_entities()["entities"]
        alphabet = [{"ticker": "GOOGL", "label": "positive", "evidence": "Alphabet expands."}]
        self.paths = {
            "a": self.write("a", {"T001": entities, "T002": alphabet}),
            # b drops JPM and makes AAPL neutral; GOOGL stays unanimous.
            "b": self.write("b", {"T001": [dict(entities[0], label="neutral")], "T002": alphabet}),
        }
        self.output = self.root / "reference"

    def write(self, name, rows):
        path = self.root / f"{name}.json"
        path.write_text(json.dumps({"schema_version": 1, "articles": [
            {"id": key, "entities": value} for key, value in rows.items()]}), encoding="utf-8")
        return path

    def prepare(self, spot_checks=1):
        return prepare_reference(articles=self.articles, universe=sample_universe(),
                                 version_paths=self.paths, spot_checks=spot_checks, seed=1,
                                 output_dir=self.output)

    def decide(self, decisions):
        path = self.output / "cases.csv"
        with path.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        for row in rows:
            row["human_decision"] = decisions[(row["id"], row["ticker"])]
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=CASE_FIELDS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    def test_cases_are_blind_and_cover_disagreements_plus_spot_checks(self):
        manifest = self.prepare()
        self.assertEqual((manifest["pairs"], manifest["disputed_pairs"],
                          manifest["unanimous_pairs"], manifest["spot_checks"]), (3, 2, 1, 1))
        text = (self.output / "cases.csv").read_text(encoding="utf-8")
        self.assertNotIn("positive", text)  # no version label leaks into the cases
        self.assertNotIn("neutral", text)
        self.assertIn("Alphabet expands.", (self.output / "GUIDE.md").read_text(encoding="utf-8"))

    def test_score_estimates_each_version_with_measured_consensus(self):
        self.prepare()
        self.decide({("T001", "AAPL"): "positive", ("T001", "JPM"): "absent",
                     ("T002", "GOOGL"): "positive"})
        report = score_reference(self.output)
        self.assertEqual(report["spot_checks"]["consensus_accuracy"], 1.0)
        self.assertEqual(report["versions"]["a"]["disputed_correct"], 1)
        self.assertEqual(report["versions"]["b"]["disputed_correct"], 1)
        self.assertAlmostEqual(report["versions"]["a"]["estimated_pair_accuracy"], 2 / 3)
        self.assertEqual(report["versions"]["a"]["errors"][0]["ticker"], "JPM")

    def test_typo_is_reported_with_its_case(self):
        self.prepare(spot_checks=0)
        self.decide({("T001", "AAPL"): "posi`", ("T001", "JPM"): ""})
        with self.assertRaisesRegex(ClassificationError, "R001='posi`'"):
            score_reference(self.output)


if __name__ == "__main__":
    unittest.main()
