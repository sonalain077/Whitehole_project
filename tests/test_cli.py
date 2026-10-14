from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr

from aie2609.cli import main


class CliTests(unittest.TestCase):
    def test_missing_input_returns_data_error_code(self) -> None:
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            exit_code = main(
                ["audit", "--news", "missing-news.json", "--universe", "missing-universe.csv"]
            )
        self.assertEqual(exit_code, 2)
        self.assertIn("Input error:", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
