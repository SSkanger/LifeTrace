"""Small OpenAI-compatible chat completion client for LifeTrace."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


class LLMConfigError(RuntimeError):
    """Raised when the LLM client is missing required configuration."""


class LLMRequestError(RuntimeError):
    """Raised when the LLM provider returns an error or malformed response."""


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


DEFAULT_MAX_TOKENS = _env_int("LIFETRACE_LLM_MAX_TOKENS", 6000)


class OpenAICompatibleClient:
    """Call OpenAI-compatible chat and embeddings endpoints using stdlib only."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout_seconds: int = 90,
        json_mode: bool | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("LIFETRACE_LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("LIFETRACE_LLM_MODEL") or os.getenv("OPENAI_MODEL")
        self.embedding_model = os.getenv("LIFETRACE_EMBEDDING_MODEL") or os.getenv("OPENAI_EMBEDDING_MODEL")
        self.base_url = (base_url or os.getenv("LIFETRACE_LLM_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        self.embedding_api_key = (
            os.getenv("LIFETRACE_EMBEDDING_API_KEY")
            or os.getenv("OPENAI_EMBEDDING_API_KEY")
            or self.api_key
        )
        self.embedding_base_url = (
            os.getenv("LIFETRACE_EMBEDDING_BASE_URL")
            or os.getenv("OPENAI_EMBEDDING_BASE_URL")
            or self.base_url
        ).rstrip("/")
        self.timeout_seconds = timeout_seconds

        if json_mode is None:
            json_mode_env = os.getenv("LIFETRACE_LLM_JSON_MODE", "true").strip().lower()
            json_mode = json_mode_env not in {"0", "false", "no", "off"}
        self.json_mode = json_mode

        if not self.api_key:
            raise LLMConfigError("Missing LIFETRACE_LLM_API_KEY or OPENAI_API_KEY")
        if not self.model:
            raise LLMConfigError("Missing LIFETRACE_LLM_MODEL or OPENAI_MODEL")

    def create_json_payload(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> dict[str, Any]:
        """Request a JSON response and parse it into a Python dict."""

        request_payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if self.json_mode:
            request_payload["response_format"] = {"type": "json_object"}

        raw_text = self._post_chat_completions(request_payload)
        return parse_json_object(raw_text)

    def create_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Request vector embeddings for a batch of texts."""

        if not texts:
            return []
        if not self.embedding_model:
            raise LLMConfigError("Missing LIFETRACE_EMBEDDING_MODEL or OPENAI_EMBEDDING_MODEL")
        if not self.embedding_api_key:
            raise LLMConfigError("Missing LIFETRACE_EMBEDDING_API_KEY or OPENAI_EMBEDDING_API_KEY")

        request_payload = {
            "model": self.embedding_model,
            "input": texts,
        }
        body = json.dumps(request_payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            f"{self.embedding_base_url}/embeddings",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.embedding_api_key}",
                "Content-Type": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                response_body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise LLMRequestError(f"Embedding HTTP {exc.code}: {error_body}") from exc
        except urllib.error.URLError as exc:
            raise LLMRequestError(f"Embedding request failed: {exc.reason}") from exc

        try:
            parsed = json.loads(response_body)
            rows = sorted(parsed["data"], key=lambda row: row.get("index", 0))
            embeddings = [row["embedding"] for row in rows]
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise LLMRequestError(f"Unexpected embedding response shape: {response_body[:500]}") from exc

        if len(embeddings) != len(texts):
            raise LLMRequestError("Embedding response count did not match input count")
        return embeddings

    def _post_chat_completions(self, payload: dict[str, Any]) -> str:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                response_body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise LLMRequestError(f"LLM HTTP {exc.code}: {error_body}") from exc
        except urllib.error.URLError as exc:
            raise LLMRequestError(f"LLM request failed: {exc.reason}") from exc

        try:
            parsed = json.loads(response_body)
            choice = parsed["choices"][0]
            finish_reason = choice.get("finish_reason")
            content = choice["message"]["content"]
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise LLMRequestError(f"Unexpected LLM response shape: {response_body[:500]}") from exc

        if finish_reason == "length":
            raise LLMRequestError(
                "LLM response was cut off by max_tokens. "
                "Rerun with --max-tokens 6000 or higher, or reduce the prompt/input size."
            )
        if not isinstance(content, str) or not content.strip():
            raise LLMRequestError("LLM response content is empty")
        return content


def parse_json_object(text: str) -> dict[str, Any]:
    """Parse a JSON object, tolerating accidental text around the object."""

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise LLMRequestError("LLM response did not contain a JSON object")
        try:
            parsed = json.loads(text[start : end + 1])
        except json.JSONDecodeError as exc:
            raise LLMRequestError(
                "LLM returned malformed JSON. If you are using DeepSeek, try rerunning with "
                "--max-tokens 6000 or higher; if it still fails, lower --temperature to 0."
            ) from exc

    if not isinstance(parsed, dict):
        raise LLMRequestError("LLM response must be a JSON object")
    return parsed
