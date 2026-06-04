"""vivo BlueLM cloud API client for LifeTrace."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import random
import string
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from typing import Any

from llm_client import LLMConfigError, LLMRequestError, parse_json_object


VIVO_URI = "/vivogpt/completions"
SIGNED_HEADERS = "x-ai-gateway-app-id;x-ai-gateway-timestamp;x-ai-gateway-nonce"


class VivoBlueLMClient:
    """Call vivo BlueLM /vivogpt/completions with AI Gateway signing."""

    def __init__(
        self,
        app_id: str | None = None,
        app_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout_seconds: int = 90,
        use_messages: bool | None = None,
    ) -> None:
        self.app_id = _clean_secret(app_id or os.getenv("LIFETRACE_VIVO_APP_ID"))
        self.app_key = _clean_secret(app_key or os.getenv("LIFETRACE_VIVO_APP_KEY"))
        self.model = _clean_secret(model or os.getenv("LIFETRACE_VIVO_MODEL")) or "vivo-BlueLM-TB-Pro"
        self.base_url = (_clean_secret(base_url or os.getenv("LIFETRACE_VIVO_BASE_URL")) or "https://api-ai.vivo.com.cn").rstrip("/")
        self.timeout_seconds = timeout_seconds
        if use_messages is None:
            env_value = os.getenv("LIFETRACE_VIVO_USE_MESSAGES", "true").strip().lower()
            use_messages = env_value not in {"0", "false", "no", "off"}
        self.use_messages = use_messages

        if not self.app_id:
            raise LLMConfigError("Missing LIFETRACE_VIVO_APP_ID")
        if not self.app_key:
            raise LLMConfigError("Missing LIFETRACE_VIVO_APP_KEY")

    def create_json_payload(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 2400,
    ) -> dict[str, Any]:
        """Request a JSON response from BlueLM and parse it into a Python dict."""

        raw_text = self._post_vivogpt(messages=messages, temperature=temperature, max_tokens=max_tokens)
        return parse_json_object(raw_text)

    def _post_vivogpt(self, messages: list[dict[str, str]], temperature: float, max_tokens: int) -> str:
        request_id = str(uuid.uuid4())
        query = {"requestId": request_id}
        body_payload: dict[str, Any] = {
            "model": self.model,
            "sessionId": str(uuid.uuid4()),
            "extra": {
                "temperature": temperature,
            },
        }
        if self.use_messages:
            body_payload["messages"] = _normalize_messages(messages)
        else:
            body_payload["prompt"] = _messages_to_prompt(messages)

        body = json.dumps(body_payload, ensure_ascii=False).encode("utf-8")
        url = f"{self.base_url}{VIVO_URI}?{_canonical_query_string(query)}"
        headers = self._sign_headers(method="POST", uri=VIVO_URI, query=query)
        headers["Content-Type"] = "application/json"

        request = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers=headers,
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                response_body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise LLMRequestError(f"vivo BlueLM HTTP {exc.code}: {error_body}") from exc
        except urllib.error.URLError as exc:
            raise LLMRequestError(f"vivo BlueLM request failed: {exc.reason}") from exc

        try:
            parsed = json.loads(response_body)
        except json.JSONDecodeError as exc:
            raise LLMRequestError(f"vivo BlueLM returned non-JSON response: {response_body[:500]}") from exc

        if parsed.get("code") != 0:
            raise LLMRequestError(f"vivo BlueLM error: {response_body[:500]}")

        try:
            content = parsed["data"]["content"]
        except (KeyError, TypeError) as exc:
            raise LLMRequestError(f"Unexpected vivo BlueLM response shape: {response_body[:500]}") from exc

        if not isinstance(content, str) or not content.strip():
            raise LLMRequestError("vivo BlueLM response content is empty")
        return content

    def _sign_headers(self, method: str, uri: str, query: dict[str, str]) -> dict[str, str]:
        timestamp = str(int(time.time()))
        nonce = _nonce()
        signed_headers_string = (
            f"x-ai-gateway-app-id:{self.app_id}\n"
            f"x-ai-gateway-timestamp:{timestamp}\n"
            f"x-ai-gateway-nonce:{nonce}"
        )
        signing_string = "\n".join(
            [
                method.upper(),
                uri if uri.startswith("/") else f"/{uri}",
                _canonical_query_string(query),
                self.app_id,
                timestamp,
                signed_headers_string,
            ]
        )
        digest = hmac.new(self.app_key.encode("utf-8"), signing_string.encode("utf-8"), hashlib.sha256).digest()
        signature = base64.b64encode(digest).decode("utf-8")
        return {
            "X-AI-GATEWAY-APP-ID": self.app_id,
            "X-AI-GATEWAY-TIMESTAMP": timestamp,
            "X-AI-GATEWAY-NONCE": nonce,
            "X-AI-GATEWAY-SIGNED-HEADERS": SIGNED_HEADERS,
            "X-AI-GATEWAY-SIGNATURE": signature,
        }


def _normalize_messages(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    normalized = []
    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        if role not in {"system", "user", "assistant"}:
            role = "user"
        normalized.append({"role": role, "content": content})
    return normalized


def _messages_to_prompt(messages: list[dict[str, str]]) -> str:
    sections = []
    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        if content:
            sections.append(f"{role}:\n{content}")
    return "\n\n".join(sections)


def _canonical_query_string(query: dict[str, str]) -> str:
    if not query:
        return ""
    parts = []
    for key in sorted(query.keys()):
        encoded_key = urllib.parse.quote(str(key))
        encoded_value = urllib.parse.quote(str(query[key]))
        parts.append(f"{encoded_key}={encoded_value}")
    return "&".join(parts)


def _nonce(length: int = 8) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


def _clean_secret(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {"'", '"'}:
        cleaned = cleaned[1:-1].strip()
    return cleaned
