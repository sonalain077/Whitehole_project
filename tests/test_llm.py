import io
import http.client
import json
import os
import unittest
import urllib.error
from unittest.mock import patch, MagicMock

from aie2609.classification import build_request
from aie2609.errors import RunError
from aie2609.llm import ENDPOINT, NoRedirect, ResponsesClient, TransportError
from tests.test_classification import api_response, sample_article, sample_universe


class TransportTests(unittest.TestCase):
    def test_key_is_required_without_network(self) -> None:
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(RunError):
            ResponsesClient()

    def client(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-only-placeholder"}):
            client = ResponsesClient()
        client._opener = MagicMock()
        return client

    def test_request_uses_fixed_endpoint_and_authorization(self) -> None:
        client = self.client()
        client._opener.open.return_value.__enter__.return_value.read.return_value = json.dumps(api_response()).encode()
        result = client.create(build_request(sample_article(), sample_universe()))
        sent = client._opener.open.call_args.args[0]
        self.assertEqual(sent.full_url, ENDPOINT)
        self.assertEqual(sent.get_header("Authorization"), "Bearer test-only-placeholder")
        self.assertEqual(result["status"], "completed")

    def test_http_error_hides_provider_body(self) -> None:
        client = self.client()
        client._opener.open.side_effect = urllib.error.HTTPError(
            ENDPOINT, 401, "secret-body", {}, io.BytesIO(b"test-only-placeholder"))
        with self.assertRaises(TransportError) as caught:
            client.create(build_request(sample_article(), sample_universe()))
        self.assertNotIn("test-only-placeholder", str(caught.exception))
        self.assertNotIn("secret-body", str(caught.exception))
        self.assertFalse(caught.exception.retryable)

    def test_timeout_is_not_retried_by_adapter(self) -> None:
        client = self.client()
        client._opener.open.side_effect = TimeoutError()
        with self.assertRaises(TransportError):
            client.create(build_request(sample_article(), sample_universe()))
        self.assertEqual(client._opener.open.call_count, 1)

    def test_redirect_cannot_forward_credentials(self) -> None:
        with self.assertRaises(TransportError):
            NoRedirect().redirect_request(None, None, 307, "redirect", {}, "https://example.com")

    def test_truncated_response_has_safe_error_without_resend(self) -> None:
        client = self.client()
        client._opener.open.return_value.__enter__.return_value.read.side_effect = (
            http.client.IncompleteRead(b"test-only-placeholder")
        )
        with self.assertRaises(TransportError) as caught:
            client.create(build_request(sample_article(), sample_universe()))
        self.assertNotIn("test-only-placeholder", str(caught.exception))
        self.assertFalse(caught.exception.retryable)
        self.assertEqual(client._opener.open.call_count, 1)
