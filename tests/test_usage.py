from decimal import Decimal
import unittest

from aie2609.errors import RunError
from aie2609.usage import Budget, Pricing, TokenUsage, positive_decimal
from tests.test_classification import api_response


class UsageTests(unittest.TestCase):
    def test_cost_has_three_disjoint_input_categories(self) -> None:
        # 70 ordinary * $2 + 20 read * $0.20 + 10 write * $2.50 + 30 output * $12.
        self.assertEqual(Pricing().cost(TokenUsage(100, 20, 10, 30)), Decimal("0.000529"))

    def test_missing_cache_write_usage_cannot_be_assumed_zero(self) -> None:
        response = api_response()
        del response["usage"]["input_tokens_details"]["cache_write_tokens"]
        with self.assertRaises(RunError):
            TokenUsage.from_response(response)

    def test_invalid_usage_is_rejected(self) -> None:
        for field, value in [("input_tokens", True), ("output_tokens", -1), ("input_tokens", 5)]:
            response = api_response()
            response["usage"][field] = value
            with self.subTest(field=field), self.assertRaises(RunError):
                TokenUsage.from_response(response)

    def test_budget_reserves_then_settles_actual_usage(self) -> None:
        budget = Budget(Decimal("1"))
        budget.reserve(Decimal("0.7"))
        with self.assertRaises(RunError):
            budget.reserve(Decimal("0.4"))
        budget.settle(Decimal("0.7"), Decimal("0.1"))
        self.assertEqual(budget.committed, Decimal("0.1"))
        budget.reserve(Decimal("0.9"))

    def test_budget_values_must_be_positive_finite(self) -> None:
        for value in ("NaN", "Infinity", "-1", "0", "abc"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                positive_decimal(value)

    def test_actual_cost_exceeding_estimate_stops_run(self) -> None:
        budget = Budget(Decimal("1"))
        budget.reserve(Decimal("0.1"))
        with self.assertRaises(RunError):
            budget.settle(Decimal("0.1"), Decimal("0.2"))
        self.assertEqual(budget.committed, Decimal("0.2"))
