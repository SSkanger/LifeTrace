"""Print safe diagnostics for vivo BlueLM environment configuration."""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from vivo_client import VivoBlueLMClient  # noqa: E402


def main() -> None:
    names = [
        "LIFETRACE_LLM_PROVIDER",
        "LIFETRACE_VIVO_BASE_URL",
        "LIFETRACE_VIVO_APP_ID",
        "LIFETRACE_VIVO_APP_KEY",
        "LIFETRACE_VIVO_MODEL",
        "LIFETRACE_VIVO_USE_MESSAGES",
    ]
    for name in names:
        value = os.getenv(name)
        print(f"{name}: {_describe(name, value)}")

    try:
        client = VivoBlueLMClient()
        headers = client._sign_headers("POST", "/vivogpt/completions", {"requestId": "diagnose-request"})
    except Exception as exc:
        print(f"client: ERROR {type(exc).__name__}: {exc}")
        return

    print("client: OK")
    print(f"clean_app_id_len: {len(client.app_id or '')}")
    print(f"clean_app_key_len: {len(client.app_key or '')}")
    print(f"clean_base_url: {client.base_url}")
    print(f"clean_model: {client.model}")
    print(f"signed_headers: {headers['X-AI-GATEWAY-SIGNED-HEADERS']}")
    print(f"signature_len: {len(headers['X-AI-GATEWAY-SIGNATURE'])}")


def _describe(name: str, value: str | None) -> str:
    if value is None:
        return "MISSING"
    raw_len = len(value)
    trimmed = value.strip()
    sha = hashlib.sha256(trimmed.encode("utf-8")).hexdigest()[:10]
    flags = []
    if value != trimmed:
        flags.append("has_outer_whitespace")
    if trimmed.startswith(("'", '"')) or trimmed.endswith(("'", '"')):
        flags.append("contains_quote_char")
    if "APP_KEY" in name:
        return f"set raw_len={raw_len} trimmed_len={len(trimmed)} sha10={sha} {' '.join(flags)}".strip()
    return f"{trimmed!r} raw_len={raw_len} trimmed_len={len(trimmed)} {' '.join(flags)}".strip()


if __name__ == "__main__":
    main()
