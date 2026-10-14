import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aie2609.config import load_local_api_key
from aie2609.errors import RunError


class LocalConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / ".env"
        environment = patch.dict(os.environ, {}, clear=True)
        environment.start()
        self.addCleanup(environment.stop)

    def test_loads_plain_or_quoted_key_with_bom_and_comments(self) -> None:
        for value in ["test-only-placeholder", "'test-only-placeholder'", '"test-only-placeholder"']:
            with self.subTest(value=value):
                os.environ.pop("OPENAI_API_KEY", None)
                self.path.write_text(f"# local config\n\nOPENAI_API_KEY = {value}\n", encoding="utf-8-sig")
                load_local_api_key(self.path)
                self.assertEqual(os.environ["OPENAI_API_KEY"], "test-only-placeholder")

    def test_environment_takes_priority_without_reading_file(self) -> None:
        os.environ["OPENAI_API_KEY"] = "existing-test-value"
        with patch.object(Path, "open", side_effect=AssertionError("File must not be read")):
            load_local_api_key(self.path)
        self.assertEqual(os.environ["OPENAI_API_KEY"], "existing-test-value")

    def test_missing_or_empty_file_does_not_supply_a_key(self) -> None:
        load_local_api_key(self.path)
        self.assertNotIn("OPENAI_API_KEY", os.environ)
        self.path.write_text("OPENAI_API_KEY=\n", encoding="utf-8")
        load_local_api_key(self.path)
        self.assertNotIn("OPENAI_API_KEY", os.environ)

    def test_invalid_file_errors_never_expose_values_or_partially_load(self) -> None:
        for text in ["OPENAI_API_KEY='private-test-value", "OPENAI_API_KEY=private test value",
                     "OPENAI_API_KEY=private-test-value\nOPENAI_API_KEY=duplicate"]:
            with self.subTest():
                self.path.write_text(text, encoding="utf-8")
                with self.assertRaises(RunError) as caught:
                    load_local_api_key(self.path)
                self.assertNotIn("private", str(caught.exception))
                self.assertNotIn("OPENAI_API_KEY", os.environ)

    def test_other_settings_are_ignored_and_interpolation_is_not_executed(self) -> None:
        self.path.write_text("MODEL=another-model\nOPENAI_API_KEY=${OTHER_KEY}\n", encoding="utf-8")
        load_local_api_key(self.path)
        self.assertNotIn("MODEL", os.environ)
        self.assertEqual(os.environ["OPENAI_API_KEY"], "${OTHER_KEY}")

    def test_invalid_encoding_is_reported_without_file_contents(self) -> None:
        self.path.write_bytes(b"OPENAI_API_KEY=private-test-value\xff")
        with self.assertRaises(RunError) as caught:
            load_local_api_key(self.path)
        self.assertNotIn("private", str(caught.exception))
