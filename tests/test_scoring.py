import hashlib
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from aie2609.dates import parse_new_york_datetime
from aie2609.errors import ClassificationError, RunError
from aie2609.scoring import calculate_scores, export_scores
from tests.test_classification import sample_article, sample_entities, sample_universe


class ScoringTests(unittest.TestCase):
    def test_half_life_at_zero_seven_and_fourteen_days(self):
        base = sample_article()
        articles = [replace(base, id=f"T{index}",
                            published_at=parse_new_york_datetime(date), date_raw=date)
                    for index, date in enumerate(("2026-09-29T00:00",
                                                  "2026-09-22T00:00",
                                                  "2026-09-15T00:00"), 1)]
        classifications = {article.id: [{"ticker": "AAPL", "label": "positive",
                                          "evidence": article.headline}]
                           for article in articles}
        _, scores = calculate_scores(articles, classifications)
        self.assertEqual(scores["AAPL"], 1.75)

    def test_fractional_day_negative_and_neutral_zero(self):
        base = sample_article()
        article = replace(base, published_at=parse_new_york_datetime("2026-09-25T12:00"),
                          date_raw="2026-09-25T12:00")
        entities = [
            {"ticker": "AAPL", "label": "negative", "evidence": article.headline},
            {"ticker": "JPM", "label": "neutral", "evidence": article.body},
        ]
        _, scores = calculate_scores([article], {article.id: entities})
        self.assertAlmostEqual(scores["AAPL"], -(0.5 ** 0.5))
        self.assertEqual(scores["JPM"], 0.0)

    def test_future_article_is_rejected(self):
        article = replace(sample_article(),
                          published_at=parse_new_york_datetime("2026-09-29T00:01"),
                          date_raw="2026-09-29T00:01")
        with self.assertRaisesRegex(ClassificationError, "later"):
            calculate_scores([article], {article.id: sample_entities()["entities"]})

    def test_utc_elapsed_time_crosses_dst_and_equal_opposites_cancel(self):
        base = sample_article()
        before = replace(base, id="DST1",
                         published_at=parse_new_york_datetime("2026-03-07T12:00"),
                         date_raw="2026-03-07T12:00")
        after = replace(base, id="DST2",
                        published_at=parse_new_york_datetime("2026-03-08T12:00"),
                        date_raw="2026-03-08T12:00")
        rows = {
            "DST1": [{"ticker": "AAPL", "label": "positive", "evidence": before.headline}],
            "DST2": [{"ticker": "JPM", "label": "positive", "evidence": after.body}],
        }
        _, scores = calculate_scores([before, after], rows)
        self.assertAlmostEqual(scores["JPM"] / scores["AAPL"], 2 ** (23 / (24 * 7)))

        twin = replace(before, id="DST3")
        cancel = {
            "DST1": [{"ticker": "AAPL", "label": "positive", "evidence": before.headline}],
            "DST3": [{"ticker": "AAPL", "label": "negative", "evidence": twin.headline}],
        }
        _, cancelled = calculate_scores([before, twin], cancel)
        self.assertEqual(cancelled["AAPL"], 0.0)

    def test_export_requires_matching_approved_composition_and_writes_contract(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            composition = root / "composition"
            composition.mkdir()
            article = sample_article()
            classifications = {"schema_version": 1, "articles": [
                {"id": article.id, "entities": sample_entities()["entities"]}]}
            classifications_path = composition / "classifications.json"
            classifications_path.write_text(json.dumps(classifications), encoding="utf-8")
            digest = hashlib.sha256(classifications_path.read_bytes()).hexdigest()
            (composition / "composition_report.json").write_text(json.dumps({
                "schema_version": 1, "composition_version": "test",
                "ready_for_scoring": True, "output_classifications_sha256": digest,
            }), encoding="utf-8")
            news = root / "news.json"
            universe_path = root / "sp500.csv"
            news.write_text("source", encoding="utf-8")
            universe_path.write_text("source", encoding="utf-8")
            output = root / "out"
            manifest = export_scores(
                articles=[article], universe=sample_universe(), composition_dir=composition,
                output_dir=output, news_path=news, universe_path=universe_path)
            self.assertEqual((output / "entities.csv").read_text(encoding="utf-8").splitlines()[0],
                             "id,ticker,label")
            self.assertEqual((output / "scores.csv").read_text(encoding="utf-8").splitlines()[0],
                             "ticker,value")
            self.assertEqual(manifest["counts"], {"articles": 1, "entities": 2, "tickers": 2})
            report = json.loads((composition / "composition_report.json").read_text())
            report["ready_for_scoring"] = False
            (composition / "composition_report.json").write_text(json.dumps(report))
            with self.assertRaisesRegex(RunError, "not approved"):
                export_scores(articles=[article], universe=sample_universe(),
                              composition_dir=composition, output_dir=root / "other",
                              news_path=news, universe_path=universe_path)


if __name__ == "__main__":
    unittest.main()
