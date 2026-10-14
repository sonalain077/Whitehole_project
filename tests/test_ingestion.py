from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aie2609.errors import DataValidationError
from aie2609.ingestion import load_news, load_universe


VALID_ARTICLE = {
    "id": "N001",
    "date": "2026-09-28T16:20",
    "headline": "Example headline",
    "body": "Example body",
}

CSV_HEADER = "symbol,security,gics_sector,headquarters,date_added\n"


class TemporaryInputTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)

    def tearDown(self) -> None:
        self.directory.cleanup()

    def write(self, name: str, content: str) -> Path:
        path = self.root / name
        path.write_text(content, encoding="utf-8")
        return path


class NewsLoadingTests(TemporaryInputTest):
    def write_news(self, payload: object) -> Path:
        return self.write("news.json", json.dumps(payload, ensure_ascii=False))

    def test_preserves_raw_text_and_normalizes_copy(self) -> None:
        article = dict(VALID_ARTICLE)
        article["headline"] = "Te\u200bsla\r\nupdate"
        dataset = load_news(self.write_news([article]))
        loaded = dataset.articles[0]
        self.assertEqual(loaded.headline_raw, "Te\u200bsla\r\nupdate")
        self.assertEqual(loaded.headline, "Tesla\nupdate")
        self.assertEqual(dataset.issues[0].code, "removed_zero_width_space")

    def test_rejects_duplicate_json_keys(self) -> None:
        path = self.write(
            "news.json",
            '[{"id":"N001","id":"N002","date":"2026-09-28T16:20",'
            '"headline":"h","body":"b"}]',
        )
        with self.assertRaisesRegex(DataValidationError, "Duplicate JSON key"):
            load_news(path)

    def test_rejects_duplicate_ids(self) -> None:
        with self.assertRaisesRegex(DataValidationError, "Duplicate article id"):
            load_news(self.write_news([VALID_ARTICLE, VALID_ARTICLE]))

    def test_rejects_missing_and_non_string_fields(self) -> None:
        missing = dict(VALID_ARTICLE)
        del missing["body"]
        invalid_type = dict(VALID_ARTICLE, body=42)
        for payload in ([missing], [invalid_type]):
            with self.subTest(payload=payload), self.assertRaises(DataValidationError):
                load_news(self.write_news(payload))

    def test_reports_extra_fields_and_duplicate_content(self) -> None:
        first = dict(VALID_ARTICLE, provider="example")
        second = dict(VALID_ARTICLE, id="N002")
        dataset = load_news(self.write_news([first, second]))
        self.assertEqual(
            [issue.code for issue in dataset.issues],
            ["extra_news_fields", "duplicate_article_content"],
        )

    def test_rejects_article_after_as_of(self) -> None:
        future = dict(VALID_ARTICLE, date="2026-09-29T00:01")
        with self.assertRaisesRegex(DataValidationError, "later than"):
            load_news(self.write_news([future]))


class UniverseLoadingTests(TemporaryInputTest):
    def test_canonicalizes_dual_classes(self) -> None:
        content = CSV_HEADER + (
            "GOOG,Alphabet Class C,Communication Services,California,2014-04-03\n"
            "GOOGL,Alphabet Class A,Communication Services,California,2014-04-03\n"
            "FOX,Fox Class B,Communication Services,New York,2019-03-04\n"
            "FOXA,Fox Class A,Communication Services,New York,2019-03-04\n"
            "NWS,News Class B,Communication Services,New York,2013-08-01\n"
            "NWSA,News Class A,Communication Services,New York,2013-08-01\n"
            "BRK.B,Berkshire Hathaway,Financials,Nebraska,2010-02-16\n"
        )
        universe = load_universe(self.write("sp500.csv", content))
        self.assertEqual(universe.source_row_count, 7)
        self.assertEqual(universe.tickers, frozenset({"GOOGL", "FOXA", "NWSA", "BRK.B"}))
        self.assertEqual(universe.canonicalize("GOOG"), "GOOGL")

    def test_rejects_alias_without_canonical_class(self) -> None:
        path = self.write(
            "sp500.csv",
            CSV_HEADER + "GOOG,Alphabet Class C,Communication Services,California,2014-04-03\n",
        )
        with self.assertRaisesRegex(DataValidationError, "canonical ticker"):
            load_universe(path)

    def test_rejects_duplicate_header_and_symbol(self) -> None:
        duplicate_header = self.write(
            "header.csv", "symbol,symbol,gics_sector,headquarters,date_added\n"
        )
        duplicate_symbol = self.write(
            "symbols.csv",
            CSV_HEADER
            + "AAPL,Apple,Information Technology,California,1982-11-30\n"
            + "AAPL,Apple,Information Technology,California,1982-11-30\n",
        )
        for path in (duplicate_header, duplicate_symbol):
            with self.subTest(path=path), self.assertRaises(DataValidationError):
                load_universe(path)

    def test_canonical_order_is_independent_of_row_order(self) -> None:
        rows = [
            "MSFT,Microsoft,Information Technology,Washington,1994-06-01",
            "AAPL,Apple,Information Technology,California,1982-11-30",
        ]
        first = load_universe(self.write("first.csv", CSV_HEADER + "\n".join(rows) + "\n"))
        second = load_universe(
            self.write("second.csv", CSV_HEADER + "\n".join(reversed(rows)) + "\n")
        )
        self.assertEqual(first.companies, second.companies)


if __name__ == "__main__":
    unittest.main()
