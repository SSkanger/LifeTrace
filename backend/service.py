"""Shared LifeTrace page generation service functions."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from llm_client import DEFAULT_MAX_TOKENS, OpenAICompatibleClient
from mock_payload import build_mock_page_payload
from page_contract import (
    ALLOWED_ICONS,
    ALLOWED_INSIGHT_TYPES,
    ALLOWED_SOURCE_TYPES,
    ALLOWED_TONES,
    ALLOWED_UNITS,
    DISPLAY_KEYS,
    FRONTEND_HINT_KEYS,
    INSIGHT_KEYS,
    QUICK_FACT_KEYS,
    RANKING_ITEM_KEYS,
    RANKING_SECTION_KEYS,
    SUMMARY_KEYS,
    TIMELINE_KEYS,
    TOP_LEVEL_KEYS,
    validate_page_payload,
)
from prompts import build_messages
from vivo_client import VivoBlueLMClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_INPUTS = {
    "daily": {
        "data": PROJECT_ROOT / "data" / "lifetrace_daily_short_final.json",
        "guide": PROJECT_ROOT / "data" / "lifetrace_read_guide_final.json",
        "out": PROJECT_ROOT / "outputs" / "lifetrace_daily_page_payload.json",
    },
    "month": {
        "data": PROJECT_ROOT / "data" / "lifetrace_month_summary_data.json",
        "guide": PROJECT_ROOT / "data" / "lifetrace_month_read_guide.json",
        "out": PROJECT_ROOT / "outputs" / "lifetrace_month_page_payload.json",
    },
    "week": {
        "data": PROJECT_ROOT / "data" / "lifetrace_week_daily_data.json",
        "guide": PROJECT_ROOT / "data" / "lifetrace_week_read_guide.json",
        "out": PROJECT_ROOT / "outputs" / "lifetrace_week_page_payload.json",
    },
}


def generate_page_payload(
    mode: str,
    data: dict[str, Any] | None = None,
    read_guide: dict[str, Any] | None = None,
    mock: bool = False,
    temperature: float = 0.2,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    timeout: int = 90,
) -> dict[str, Any]:
    """Generate and validate a frontend page payload."""

    if mode not in DEFAULT_INPUTS:
        raise ValueError("mode must be 'daily', 'month', or 'week'")

    if data is None or read_guide is None:
        default_data, default_guide = load_default_inputs(mode)
        data = data or default_data
        read_guide = read_guide or default_guide

    if mock:
        payload = build_mock_page_payload(mode, data)
    else:
        messages = build_messages(mode, data, read_guide)
        client = build_chat_client(timeout=timeout)
        payload = client.create_json_payload(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    payload = normalize_page_payload(payload, mode)
    validate_page_payload(payload, mode)
    return payload


def normalize_page_payload(payload: dict[str, Any], mode: str) -> dict[str, Any]:
    """Apply conservative repairs for common LLM over-generation."""

    if not isinstance(payload, dict):
        return payload

    _keep_keys(payload, TOP_LEVEL_KEYS)

    summary = payload.get("summary")
    if isinstance(summary, dict):
        _keep_keys(summary, SUMMARY_KEYS)
        _clip_list(summary, "tags", 6)

    _clip_list(payload, "quickFacts", 6)
    for item in _dict_items(payload.get("quickFacts")):
        _keep_keys(item, QUICK_FACT_KEYS)

    if mode != "daily" and isinstance(payload.get("timeline"), list):
        payload["timeline"] = []
    else:
        _clip_list(payload, "timeline", 8)
    for item in _dict_items(payload.get("timeline")):
        _keep_keys(item, TIMELINE_KEYS)
        _clip_list(item, "evidence", 4)
        _clip_list(item, "sourceTypes", 8)
        _filter_allowed(item, "sourceTypes", ALLOWED_SOURCE_TYPES)
        display = item.get("display")
        if isinstance(display, dict):
            _keep_keys(display, DISPLAY_KEYS)
            _default_if_invalid(display, "icon", ALLOWED_ICONS, "sparkles")
            _default_if_invalid(display, "tone", ALLOWED_TONES, "blue")

    _clip_list(payload, "rankingSections", 6)
    for section in _dict_items(payload.get("rankingSections")):
        _keep_keys(section, RANKING_SECTION_KEYS)
        _default_if_invalid(section, "unit", ALLOWED_UNITS, "mixed")
        _clip_list(section, "items", 8)
        for item in _dict_items(section.get("items")):
            _keep_keys(item, RANKING_ITEM_KEYS)

    _clip_list(payload, "insightCards", 8)
    for insight in _dict_items(payload.get("insightCards")):
        _keep_keys(insight, INSIGHT_KEYS)
        _clip_list(insight, "evidence", 5)
        _default_if_invalid(insight, "type", ALLOWED_INSIGHT_TYPES, "highlight")

    _clip_list(payload, "memoryQuestions", 4)

    frontend_hints = payload.get("frontendHints")
    if isinstance(frontend_hints, dict):
        _keep_keys(frontend_hints, FRONTEND_HINT_KEYS)
        frontend_hints["defaultView"] = "timeline" if mode == "daily" else "overview"
        frontend_hints["density"] = "comfortable"
        _default_if_invalid(frontend_hints, "accent", ALLOWED_TONES, "blue")

    return payload


def _keep_keys(obj: dict[str, Any], allowed_keys: set[str]) -> None:
    for key in list(obj.keys()):
        if key not in allowed_keys:
            del obj[key]


def _clip_list(parent: dict[str, Any], key: str, max_len: int) -> None:
    value = parent.get(key)
    if isinstance(value, list) and len(value) > max_len:
        parent[key] = value[:max_len]


def _dict_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _filter_allowed(parent: dict[str, Any], key: str, allowed_values: set[str]) -> None:
    value = parent.get(key)
    if not isinstance(value, list):
        return
    filtered = [item for item in value if item in allowed_values]
    if filtered:
        parent[key] = filtered


def _default_if_invalid(parent: dict[str, Any], key: str, allowed_values: set[str], fallback: str) -> None:
    if parent.get(key) not in allowed_values:
        parent[key] = fallback


def build_chat_client(timeout: int = 90) -> OpenAICompatibleClient | VivoBlueLMClient:
    provider = os.getenv("LIFETRACE_LLM_PROVIDER", "openai").strip().lower()
    if provider in {"vivo", "bluelm", "blue_lm"}:
        return VivoBlueLMClient(timeout_seconds=timeout)
    return OpenAICompatibleClient(timeout_seconds=timeout)


def build_prompt_messages(
    mode: str,
    data: dict[str, Any] | None = None,
    read_guide: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    """Build the final prompt messages for inspection or debugging."""

    if data is None or read_guide is None:
        default_data, default_guide = load_default_inputs(mode)
        data = data or default_data
        read_guide = read_guide or default_guide
    return build_messages(mode, data, read_guide)


def load_default_inputs(mode: str) -> tuple[dict[str, Any], dict[str, Any]]:
    defaults = DEFAULT_INPUTS[mode]
    return read_json(defaults["data"]), read_json(defaults["guide"])


def default_output_path(mode: str) -> Path:
    return DEFAULT_INPUTS[mode]["out"]


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")
