"""Validation helpers for LifeTrace fuzzy memory search JSON."""

from __future__ import annotations

import re
from typing import Any


class SearchValidationError(ValueError):
    """Raised when a search plan or result payload is not contract-compliant."""


QUERY_PLAN_KEYS = {
    "searchText",
    "intent",
    "timeHints",
    "locationHints",
    "appHints",
    "activityHints",
    "visualHints",
    "keywords",
}
ANSWER_KEYS = {"headline", "paragraph"}
SELECTION_KEYS = {"answer", "selectedResults", "relatedQuestions", "frontendHints"}
SELECTED_RESULT_KEYS = {"candidateId", "matchReason", "confidence"}
SELECTION_HINT_KEYS = {"accent"}

SEARCH_PAYLOAD_KEYS = {
    "schemaVersion",
    "query",
    "interpretedQuery",
    "answer",
    "results",
    "relatedQuestions",
    "frontendHints",
}
INTERPRETED_QUERY_KEYS = QUERY_PLAN_KEYS
SEARCH_RESULT_KEYS = {
    "id",
    "score",
    "confidence",
    "sourceType",
    "sourceKey",
    "timeRange",
    "title",
    "snippet",
    "evidence",
    "matchReason",
    "openTarget",
}
OPEN_TARGET_KEYS = {"pageType", "sourceKey", "anchorId"}
SEARCH_HINT_KEYS = {"defaultView", "accent", "density"}

ALLOWED_INTENTS = {"find_memory", "find_day", "find_pattern", "open_summary"}
ALLOWED_CONFIDENCE = {"high", "medium", "low"}
ALLOWED_TONES = {"blue", "green", "amber", "rose", "violet", "slate"}
ALLOWED_SOURCE_TYPES = {
    "daily_segment",
    "daily_context",
    "app_usage",
    "location_stay",
    "photo_moment",
    "month_summary",
    "month_highlight",
    "month_pattern",
    "month_stat",
}
ALLOWED_PAGE_TYPES = {"daily", "month"}


def validate_query_plan(plan: Any) -> None:
    if not isinstance(plan, dict):
        raise SearchValidationError("query plan must be an object")
    _require_exact_keys(plan, QUERY_PLAN_KEYS, "queryPlan")
    _expect_non_empty_str(plan["searchText"], "queryPlan.searchText")
    _expect(plan["intent"] in ALLOWED_INTENTS, "queryPlan.intent is invalid")
    for key in ("timeHints", "locationHints", "appHints", "activityHints", "visualHints"):
        _expect_string_list(plan[key], f"queryPlan.{key}", min_len=0, max_len=8)
    _expect_string_list(plan["keywords"], "queryPlan.keywords", min_len=0, max_len=10)


def validate_selection(selection: Any, candidate_ids: set[str]) -> None:
    if not isinstance(selection, dict):
        raise SearchValidationError("selection must be an object")
    _require_exact_keys(selection, SELECTION_KEYS, "selection")
    _validate_answer(selection["answer"], "selection.answer")
    _expect(isinstance(selection["selectedResults"], list), "selection.selectedResults must be an array")
    _expect(1 <= len(selection["selectedResults"]) <= 5, "selection.selectedResults must contain 1 to 5 items")
    for index, item in enumerate(selection["selectedResults"]):
        path = f"selection.selectedResults[{index}]"
        _expect(isinstance(item, dict), f"{path} must be an object")
        _require_exact_keys(item, SELECTED_RESULT_KEYS, path)
        _expect(item["candidateId"] in candidate_ids, f"{path}.candidateId is not in candidates")
        _expect_non_empty_str(item["matchReason"], f"{path}.matchReason")
        _expect(item["confidence"] in ALLOWED_CONFIDENCE, f"{path}.confidence is invalid")
    _expect_string_list(selection["relatedQuestions"], "selection.relatedQuestions", min_len=2, max_len=4)
    _expect(isinstance(selection["frontendHints"], dict), "selection.frontendHints must be an object")
    _require_exact_keys(selection["frontendHints"], SELECTION_HINT_KEYS, "selection.frontendHints")
    _expect(selection["frontendHints"]["accent"] in ALLOWED_TONES, "selection.frontendHints.accent is invalid")


def validate_search_payload(payload: Any) -> None:
    if not isinstance(payload, dict):
        raise SearchValidationError("payload must be an object")
    _require_exact_keys(payload, SEARCH_PAYLOAD_KEYS, "payload")
    _expect(payload["schemaVersion"] == "lifetrace.search.v1", "schemaVersion must be lifetrace.search.v1")
    _expect_non_empty_str(payload["query"], "payload.query")
    _validate_query_plan_as_interpreted(payload["interpretedQuery"])
    _validate_answer(payload["answer"], "payload.answer")
    _expect(isinstance(payload["results"], list), "payload.results must be an array")
    _expect(1 <= len(payload["results"]) <= 5, "payload.results must contain 1 to 5 items")
    for index, result in enumerate(payload["results"]):
        _validate_search_result(result, f"payload.results[{index}]")
    _expect_string_list(payload["relatedQuestions"], "payload.relatedQuestions", min_len=2, max_len=4)
    _validate_frontend_hints(payload["frontendHints"])


def _validate_query_plan_as_interpreted(plan: Any) -> None:
    _expect(isinstance(plan, dict), "interpretedQuery must be an object")
    _require_exact_keys(plan, INTERPRETED_QUERY_KEYS, "interpretedQuery")
    validate_query_plan(plan)


def _validate_answer(answer: Any, path: str) -> None:
    _expect(isinstance(answer, dict), f"{path} must be an object")
    _require_exact_keys(answer, ANSWER_KEYS, path)
    _expect_non_empty_str(answer["headline"], f"{path}.headline")
    _expect_non_empty_str(answer["paragraph"], f"{path}.paragraph")


def _validate_search_result(result: Any, path: str) -> None:
    _expect(isinstance(result, dict), f"{path} must be an object")
    _require_exact_keys(result, SEARCH_RESULT_KEYS, path)
    _expect_safe_id(result["id"], f"{path}.id")
    _expect(isinstance(result["score"], (int, float)), f"{path}.score must be a number")
    _expect(0 <= float(result["score"]) <= 1.5, f"{path}.score is out of range")
    _expect(result["confidence"] in ALLOWED_CONFIDENCE, f"{path}.confidence is invalid")
    _expect(result["sourceType"] in ALLOWED_SOURCE_TYPES, f"{path}.sourceType is invalid")
    _expect_source_key(result["sourceKey"], f"{path}.sourceKey")
    for key in ("timeRange", "title", "snippet", "matchReason"):
        _expect_non_empty_str(result[key], f"{path}.{key}")
    _expect_string_list(result["evidence"], f"{path}.evidence", min_len=1, max_len=5)
    _expect(isinstance(result["openTarget"], dict), f"{path}.openTarget must be an object")
    _require_exact_keys(result["openTarget"], OPEN_TARGET_KEYS, f"{path}.openTarget")
    _expect(result["openTarget"]["pageType"] in ALLOWED_PAGE_TYPES, f"{path}.openTarget.pageType is invalid")
    _expect_source_key(result["openTarget"]["sourceKey"], f"{path}.openTarget.sourceKey")
    _expect(isinstance(result["openTarget"]["anchorId"], str), f"{path}.openTarget.anchorId must be a string")


def _validate_frontend_hints(hints: Any) -> None:
    _expect(isinstance(hints, dict), "frontendHints must be an object")
    _require_exact_keys(hints, SEARCH_HINT_KEYS, "frontendHints")
    _expect(hints["defaultView"] == "search_results", "frontendHints.defaultView must be search_results")
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
        raise SearchValidationError(f"{path} has invalid keys ({'; '.join(parts)})")


def _expect_string_list(value: Any, path: str, min_len: int, max_len: int) -> None:
    _expect(isinstance(value, list), f"{path} must be an array")
    _expect(min_len <= len(value) <= max_len, f"{path} must contain {min_len} to {max_len} items")
    for index, item in enumerate(value):
        _expect_non_empty_str(item, f"{path}[{index}]")


def _expect_safe_id(value: Any, path: str) -> None:
    _expect(isinstance(value, str), f"{path} must be a string")
    _expect(re.match(r"^[a-z][a-z0-9_]*$", value) is not None, f"{path} must be lowercase snake_case")


def _expect_source_key(value: Any, path: str) -> None:
    _expect(isinstance(value, str), f"{path} must be a string")
    _expect(
        re.match(r"^\d{4}-\d{2}(-\d{2})?$", value) is not None,
        f"{path} must be yyyy-MM or yyyy-MM-dd",
    )


def _expect_non_empty_str(value: Any, path: str) -> None:
    _expect(isinstance(value, str) and value.strip() != "", f"{path} must be a non-empty string")


def _expect(condition: bool, message: str) -> None:
    if not condition:
        raise SearchValidationError(message)
