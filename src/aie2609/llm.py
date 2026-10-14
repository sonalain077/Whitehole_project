"""Small Responses HTTP adapter; no implicit retries, redirects or alternate providers."""

from __future__ import annotations

import json
import http.client
import os
import urllib.error
import urllib.request

from .classification import MODEL, json_text, strict_json
from .errors import ClassificationError, RunError

ENDPOINT = "https://api.openai.com/v1/responses"
MAX_RESPONSE_BYTES = 2_000_000


class TransportError(RunError):
    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise TransportError("Unexpected API redirect refused.")


class ResponsesClient:
    def __init__(self, timeout: float = 60) -> None:
        key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not key:
            raise RunError("OPENAI_API_KEY is absent. Set it in the environment or local .env file.")
        if any(ord(char) < 33 or ord(char) > 126 for char in key):
            raise RunError("OPENAI_API_KEY contains invalid characters.")
        self._key = key
        self.timeout = timeout
        self._opener = urllib.request.build_opener(NoRedirect())

    def create(self, payload: dict) -> dict:
        if payload.get("model") != MODEL:
            raise RunError("Only the project model is allowed.")
        request = urllib.request.Request(
            ENDPOINT, data=json_text(payload).encode("utf-8"), method="POST",
            headers={"Authorization": f"Bearer {self._key}", "Content-Type": "application/json"},
        )
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise TransportError("API response exceeded size limit; billing is unknown.")
            parsed = strict_json(raw.decode("utf-8"))
            if not isinstance(parsed, dict):
                raise TransportError("API envelope is invalid; billing is unknown.")
            return parsed
        except urllib.error.HTTPError as exc:
            # Never print the provider body: it could echo input or credentials.
            retryable = False
            if exc.code == 429:
                try:
                    details = json.loads(exc.read(65536))
                    retryable = details.get("error", {}).get("code") == "rate_limit_exceeded"
                except (ValueError, AttributeError, OSError, http.client.HTTPException):
                    pass
            raise TransportError(f"OpenAI HTTP {exc.code}; no model fallback.",
                                 retryable=retryable) from None
        except (urllib.error.URLError, OSError, TimeoutError, http.client.HTTPException):
            raise TransportError("API connection failed; billing is unknown. No automatic resend.") from None
        except (ClassificationError, UnicodeDecodeError):
            raise TransportError("API response could not be decoded; billing is unknown.") from None


def response_text(response: dict) -> str:
    if response.get("status") != "completed":
        raise ClassificationError("API response is incomplete or failed.")
    output = response.get("output")
    if not isinstance(output, list):
        raise ClassificationError("API response has no valid output list.")
    parts = []
    for item in output:
        if not isinstance(item, dict):
            raise ClassificationError("Invalid output item.")
        if item.get("type") == "reasoning":
            continue
        if item.get("type") != "message" or item.get("role") != "assistant":
            raise ClassificationError("Unexpected API output item.")
        if not isinstance(item.get("content"), list):
            raise ClassificationError("Invalid assistant content.")
        for content in item["content"]:
            if not isinstance(content, dict) or content.get("type") != "output_text":
                raise ClassificationError("API refusal or unexpected content.")
            if not isinstance(content.get("text"), str):
                raise ClassificationError("API output text is invalid.")
            parts.append(content["text"])
    if len(parts) != 1:
        raise ClassificationError("Expected exactly one structured output text.")
    return parts[0]
