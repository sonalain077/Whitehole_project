import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from aie2609.cli import main
from tests import requires_supplied_data


ROOT = Path(__file__).resolve().parents[1]


@requires_supplied_data
class ClassifyCliTests(unittest.TestCase):
    def args(self, *extra):
        return ["classify", "--news", str(ROOT / "news.json"),
                "--universe", str(ROOT / "sp500.csv"), *extra]

    def test_real_input_preview_needs_no_key_client_or_output(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "run"
            stream = io.StringIO()
            with patch("aie2609.cli.ResponsesClient") as client, redirect_stdout(stream), \
                    patch("aie2609.cli.load_local_api_key") as load_key:
                code = main(self.args("--ids", "N027", "N001", "--dry-run",
                                      "--output-dir", str(output)))
            self.assertEqual(code, 0)
            client.assert_not_called()
            load_key.assert_not_called()
            self.assertFalse(output.exists())
            report = json.loads(stream.getvalue())
            self.assertEqual([a["id"] for a in report["articles"]], ["N001", "N027"])

    def test_missing_budget_and_bad_selection_never_create_client(self) -> None:
        for extra in [[], ["--ids", "MISSING"], ["--ids", "N001", "N001"],
                      ["--limit", "0"], ["--max-output-tokens", "1", "--dry-run"]]:
            with self.subTest(extra=extra), patch("aie2609.cli.ResponsesClient") as client:
                with redirect_stderr(io.StringIO()):
                    self.assertEqual(main(self.args(*extra)), 2)
                client.assert_not_called()

    def test_nonfinite_or_negative_budget_is_rejected_by_cli(self) -> None:
        for budget in ["NaN", "Infinity", "-1", "0"]:
            with self.subTest(budget=budget), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as caught:
                    main(self.args("--max-cost-usd", budget))
                self.assertEqual(caught.exception.code, 2)
