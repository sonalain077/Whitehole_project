from __future__ import annotations

import unittest
from pathlib import Path

from aie2609.audit import audit_inputs
from tests import requires_supplied_data


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@requires_supplied_data
class SuppliedInputAuditTests(unittest.TestCase):
    def test_supplied_inputs_match_expected_contract(self) -> None:
        report = audit_inputs(PROJECT_ROOT / "news.json", PROJECT_ROOT / "sp500.csv")
        self.assertEqual(report.article_count, 100)
        self.assertEqual(report.source_company_count, 503)
        self.assertEqual(report.canonical_company_count, 500)
        self.assertEqual(report.earliest_article, "2026-08-25T06:53")
        self.assertEqual(report.latest_article, "2026-09-28T16:20")
        self.assertEqual(report.ticker_aliases, {"GOOG": "GOOGL", "FOX": "FOXA", "NWS": "NWSA"})
        zero_width_issues = [
            issue.record_id for issue in report.issues if issue.code == "removed_zero_width_space"
        ]
        self.assertEqual(zero_width_issues, ["N027", "N100"])


if __name__ == "__main__":
    unittest.main()
