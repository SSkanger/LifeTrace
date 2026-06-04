"""Validation helpers for the LifeTrace frontend page JSON contract."""

from __future__ import annotations

import re
from typing import Any


class ContractValidationError(ValueError):
    """Raised when a generated page payload does not match the frontend contract."""


TOP_LEVEL_KEYS = {
    "schemaVersion",
    "pageType",
    "sourceKey",
    "title",
    "subtitle",
    "dataQualityNote",
    "summary",
    "quickFacts",
    "timeline",
    "rankingSections",
    "insightCards",
    "memoryQuestions",
    "frontendHints",
}

SUMMARY_KEYS = {"headline", "paragraph", "tags"}
QUICK_FACT_KEYS = {"id", "label", "value", "description"}
TIMELINE_KEYS = {
    "id",
    "timeRange",
    "title",
    "category",
    "description",
    "evidence",
    "sourceTypes",
    "display",
}
DISPLAY_KEYS = {"icon", "tone"}
RANKING_SECTION_KEYS = {"id", "title", "unit", "items"}
RANKING_ITEM_KEYS = {"rank", "label", "value", "description"}
INSIGHT_KEYS = {"id", "title", "description", "evidence", "type"}
FRONTEND_HINT_KEYS = {"defaultView", "accent", "density"}

ALLOWED_ICONS = {
    "home",
    "book-open",
    "utensils",
    "laptop",
    "map-pin",
    "camera",
    "moon",
    "chart-bar",
    "sparkles",
    "alert-circle",
}
ALLOWED_TONES = {"blue", "green", "amber", "rose", "violet", "slate"}
ALLOWED_SOURCE_TYPES = {
    "app_usage",
    "location",
    "photo",
    "ocr",
    "summary",
    "stats",
    "highlight",
    "pattern",
}
ALLOWED_UNITS = {"minutes", "count", "mixed"}
ALLOWED_INSIGHT_TYPES = {"highlight", "pattern", "suggestion"}
ALLOWED_DEFAULT_VIEWS = {"timeline", "overview"}


def validate_page_payload(payload: Any, mode: str) -> None:
    """Validate a payload against the LifeTrace frontend page contract."""

    if mode not in {"daily", "month", "week"}:
        raise ContractValidationError("mode must be 'daily', 'month', or 'week'")
    if not isinstance(payload, dict):
        raise ContractValidationError("payload must be a JSON object")

    _require_exact_keys(payload, TOP_LEVEL_KEYS, "payload")

    _expect(payload["schemaVersion"] == "lifetrace.page.v1", "schemaVersion must be lifetrace.page.v1")
    expected_page_type = mode
    _expect(payload["pageType"] == expected_page_type, f"pageType must be {expected_page_type}")

    source_patterns = {
        "daily": r"^\d{4}-\d{2}-\d{2}$",
        "month": r"^\d{4}-\d{2}$",
        "week": r"^\d{4}-W\d{2}$",
    }
    source_pattern = source_patterns[mode]
    _expect(re.match(source_pattern, payload["sourceKey"]) is not None, "sourceKey has invalid format")

    for key in ("title", "subtitle", "dataQualityNote"):
        _expect_non_empty_str(payload[key], key)

    _validate_summary(payload["summary"])
    _validate_quick_facts(payload["quickFacts"])
    _validate_timeline(payload["timeline"], mode)
    _validate_ranking_sections(payload["rankingSections"])
    _validate_insights(payload["insightCards"])
    _validate_memory_questions(payload["memoryQuestions"])
    _validate_frontend_hints(payload["frontendHints"], mode)


def _validate_summary(summary: Any) -> None:
    _expect(isinstance(summary, dict), "summary must be an object")
    _require_exact_keys(summary, SUMMARY_KEYS, "summary")
    _expect_non_empty_str(summary["headline"], "summary.headline")
    _expect_non_empty_str(summary["paragraph"], "summary.paragraph")
    _expect_string_list(summary["tags"], "summary.tags", min_len=2, max_len=6)


def _validate_quick_facts(quick_facts: Any) -> None:
    _expect(isinstance(quick_facts, list), "quickFacts must be an array")
    _expect(2 <= len(quick_facts) <= 6, "quickFacts must contain 2 to 6 items")
    for index, item in enumerate(quick_facts):
        path = f"quickFacts[{index}]"
        _expect(isinstance(item, dict), f"{path} must be an object")
        _require_exact_keys(item, QUICK_FACT_KEYS, path)
        _expect_safe_id(item["id"], f"{path}.id")
        for key in ("label", "value", "description"):
            _expect_non_empty_str(item[key], f"{path}.{key}")


def _validate_timeline(timeline: Any, mode: str) -> None:
    _expect(isinstance(timeline, list), "timeline must be an array")
    if mode == "daily":
        _expect(1 <= len(timeline) <= 8, "daily timeline must contain 1 to 8 items")
    else:
        _expect(len(timeline) == 0, "month timeline must be an empty array")

    for index, item in enumerate(timeline):
        path = f"timeline[{index}]"
        _expect(isinstance(item, dict), f"{path} must be an object")
        _require_exact_keys(item, TIMELINE_KEYS, path)
        _expect_safe_id(item["id"], f"{path}.id")
        for key in ("timeRange", "title", "category", "description"):
            _expect_non_empty_str(item[key], f"{path}.{key}")
        _expect_string_list(item["evidence"], f"{path}.evidence", min_len=1, max_len=4)
        _expect_string_list(item["sourceTypes"], f"{path}.sourceTypes", min_len=1, max_len=8)
        for source_type in item["sourceTypes"]:
            _expect(source_type in ALLOWED_SOURCE_TYPES, f"{path}.sourceTypes contains invalid value {source_type}")
        _expect(isinstance(item["display"], dict), f"{path}.display must be an object")
        _require_exact_keys(item["display"], DISPLAY_KEYS, f"{path}.display")
        _expect(item["display"]["icon"] in ALLOWED_ICONS, f"{path}.display.icon is invalid")
        _expect(item["display"]["tone"] in ALLOWED_TONES, f"{path}.display.tone is invalid")


def _validate_ranking_sections(sections: Any) -> None:
    _expect(isinstance(sections, list), "rankingSections must be an array")
    _expect(len(sections) <= 6, "rankingSections must contain at most 6 sections")
    for section_index, section in enumerate(sections):
        section_path = f"rankingSections[{section_index}]"
        _expect(isinstance(section, dict), f"{section_path} must be an object")
        _require_exact_keys(section, RANKING_SECTION_KEYS, section_path)
        _expect_safe_id(section["id"], f"{section_path}.id")
        _expect_non_empty_str(section["title"], f"{section_path}.title")
        _expect(section["unit"] in ALLOWED_UNITS, f"{section_path}.unit is invalid")
        _expect(isinstance(section["items"], list), f"{section_path}.items must be an array")
        _expect(len(section["items"]) <= 8, f"{section_path}.items must contain at most 8 items")
        for item_index, item in enumerate(section["items"]):
            item_path = f"{section_path}.items[{item_index}]"
            _expect(isinstance(item, dict), f"{item_path} must be an object")
            _require_exact_keys(item, RANKING_ITEM_KEYS, item_path)
            _expect(isinstance(item["rank"], int) and item["rank"] >= 1, f"{item_path}.rank must be positive integer")
            for key in ("label", "value", "description"):
                _expect_non_empty_str(item[key], f"{item_path}.{key}")


def _validate_insights(insights: Any) -> None:
    _expect(isinstance(insights, list), "insightCards must be an array")
    _expect(1 <= len(insights) <= 8, "insightCards must contain 1 to 8 items")
    for index, insight in enumerate(insights):
        path = f"insightCards[{index}]"
        _expect(isinstance(insight, dict), f"{path} must be an object")
        _require_exact_keys(insight, INSIGHT_KEYS, path)
        _expect_safe_id(insight["id"], f"{path}.id")
        for key in ("title", "description"):
            _expect_non_empty_str(insight[key], f"{path}.{key}")
        _expect_string_list(insight["evidence"], f"{path}.evidence", min_len=1, max_len=5)
        _expect(insight["type"] in ALLOWED_INSIGHT_TYPES, f"{path}.type is invalid")


def _validate_memory_questions(questions: Any) -> None:
    _expect_string_list(questions, "memoryQuestions", min_len=2, max_len=4)


def _validate_frontend_hints(hints: Any, mode: str) -> None:
    _expect(isinstance(hints, dict), "frontendHints must be an object")
    _require_exact_keys(hints, FRONTEND_HINT_KEYS, "frontendHints")
    expected_view = "timeline" if mode == "daily" else "overview"
    _expect(hints["defaultView"] == expected_view, f"frontendHints.defaultView must be {expected_view}")
    _expect(hints["accent"] in ALLOWED_TONES, "frontendHints.accent is invalid")
    _expect(hints["density"] == "comfortable", "frontendHints.density must be comfortable")


def _require_exact_keys(obj: dict[str, Any], expected: set[str], path: str) -> None:
    actual = set(obj.keys())
    missing = expected - actual
    extra = actual - expected
    if missing or extra:
        parts = []
        if missing:
            parts.append(f"missing keys: {sorted(missing)}")
        if extra:
            parts.append(f"extra keys: {sorted(extra)}")
        raise ContractValidationError(f"{path} has invalid keys ({'; '.join(parts)})")


def _expect_string_list(value: Any, path: str, min_len: int, max_len: int) -> None:
    _expect(isinstance(value, list), f"{path} must be an array")
    _expect(min_len <= len(value) <= max_len, f"{path} must contain {min_len} to {max_len} items")
    for index, item in enumerate(value):
        _expect_non_empty_str(item, f"{path}[{index}]")


def _expect_safe_id(value: Any, path: str) -> None:
    _expect(isinstance(value, str), f"{path} must be a string")
    _expect(re.match(r"^[a-z][a-z0-9_]*$", value) is not None, f"{path} must be lowercase snake_case")


def _expect_non_empty_str(value: Any, path: str) -> None:
    _expect(isinstance(value, str) and value.strip() != "", f"{path} must be a non-empty string")


def _expect(condition: bool, message: str) -> None:
    if not condition:
        raise ContractValidationError(message)
