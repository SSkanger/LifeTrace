"""LifeTrace fuzzy memory search service."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from llm_client import OpenAICompatibleClient
from memory_index import (
    ChromaMemoryIndex,
    LLMEmbeddingProvider,
    LocalHashEmbeddingProvider,
    boost_candidates,
    build_memory_items,
    enrich_query_text,
)
from search_contract import validate_query_plan, validate_search_payload, validate_selection
from search_prompts import build_candidate_selection_messages, build_query_understanding_messages
from service import DEFAULT_INPUTS, PROJECT_ROOT, read_json


DEFAULT_SEARCH_OUTPUT = PROJECT_ROOT / "outputs" / "lifetrace_search_payload.json"


def search_memory(
    query: str,
    mock: bool = False,
    top_k: int = 5,
    candidate_k: int = 16,
    rebuild_index: bool = False,
    timeout: int = 90,
) -> dict[str, Any]:
    """Search LifeTrace memories with LLM query understanding, Chroma retrieval, and LLM selection."""

    cleaned_query = query.strip()
    if not cleaned_query:
        raise ValueError("query must not be empty")
    if top_k < 1 or top_k > 5:
        raise ValueError("top_k must be between 1 and 5")
    if candidate_k < top_k:
        candidate_k = top_k

    daily_input = DEFAULT_INPUTS.get("week", DEFAULT_INPUTS["daily"])
    daily_data = read_json(daily_input["data"])
    month_data = read_json(DEFAULT_INPUTS["month"]["data"])
    memory_items = build_memory_items(daily_data, month_data)

    if mock:
        query_plan = build_mock_query_plan(cleaned_query)
        embedding_provider = LocalHashEmbeddingProvider()
        collection_name = "lifetrace_memory_mock"
        llm_client = None
    else:
        llm_client = OpenAICompatibleClient(timeout_seconds=timeout)
        query_plan = llm_client.create_json_payload(
            messages=build_query_understanding_messages(cleaned_query),
            temperature=0.1,
            max_tokens=900,
        )
        embedding_provider = LLMEmbeddingProvider(llm_client)
        model_key = re.sub(r"[^a-zA-Z0-9_]+", "_", llm_client.embedding_model or "llm").strip("_").lower()
        collection_name = f"lifetrace_memory_{model_key}"

    validate_query_plan(query_plan)

    index = ChromaMemoryIndex(collection_name=collection_name)
    if rebuild_index:
        index.reset()
    if rebuild_index or index.count() != len(memory_items):
        index.upsert_items(memory_items, embedding_provider)

    candidates = index.query(
        text=enrich_query_text(query_plan),
        embedding_provider=embedding_provider,
        n_results=max(candidate_k, top_k),
    )
    candidates = boost_candidates(candidates, query_plan)[:candidate_k]
    if not candidates:
        raise ValueError("no memory candidates were found")

    if mock:
        selection = build_mock_selection(cleaned_query, query_plan, candidates[:top_k])
    else:
        assert llm_client is not None
        selection = llm_client.create_json_payload(
            messages=build_candidate_selection_messages(cleaned_query, query_plan, candidates),
            temperature=0.15,
            max_tokens=1400,
        )

    validate_selection(selection, {candidate["id"] for candidate in candidates})
    payload = compose_search_payload(cleaned_query, query_plan, candidates, selection, top_k=top_k)
    validate_search_payload(payload)
    return payload


def compose_search_payload(
    query: str,
    query_plan: dict[str, Any],
    candidates: list[dict[str, Any]],
    selection: dict[str, Any],
    top_k: int,
) -> dict[str, Any]:
    candidate_map = {candidate["id"]: candidate for candidate in candidates}
    results = []
    seen_ids = set()
    for selected in selection["selectedResults"]:
        candidate_id = selected["candidateId"]
        if candidate_id in seen_ids:
            continue
        seen_ids.add(candidate_id)
        candidate = candidate_map[candidate_id]
        results.append(
            {
                "id": candidate["id"],
                "score": round(float(candidate["score"]), 4),
                "confidence": selected["confidence"],
                "sourceType": candidate["sourceType"],
                "sourceKey": candidate["sourceKey"],
                "timeRange": candidate["timeRange"],
                "title": candidate["title"],
                "snippet": candidate["snippet"],
                "evidence": candidate["evidence"][:5],
                "matchReason": selected["matchReason"],
                "openTarget": candidate["openTarget"],
            }
        )
        if len(results) >= top_k:
            break

    if not results:
        raise ValueError("selection did not include any usable candidates")

    return {
        "schemaVersion": "lifetrace.search.v1",
        "query": query,
        "interpretedQuery": query_plan,
        "answer": selection["answer"],
        "results": results,
        "relatedQuestions": selection["relatedQuestions"],
        "frontendHints": {
            "defaultView": "search_results",
            "accent": selection["frontendHints"]["accent"],
            "density": "comfortable",
        },
    }


def default_search_output_path() -> Path:
    return DEFAULT_SEARCH_OUTPUT


def build_mock_query_plan(query: str) -> dict[str, Any]:
    """Rule-based query understanding for offline demo mode."""

    time_hints = _pick_terms(query, ["早上", "上午", "中午", "下午", "傍晚", "晚上", "晚间", "全天"])
    time_hints.extend(re.findall(r"\d{4}-\d{2}(?:-\d{2})?", query))

    location_hints = _pick_terms(query, ["宿舍", "宿舍区", "教学楼", "图书馆", "食堂", "校园", "操场", "湖边"])
    app_hints = _pick_terms(query, ["微信", "学习通", "浏览器", "WPS", "哔哩哔哩", "腾讯文档", "VSCode"])
    activity_hints = _pick_terms(
        query,
        ["课程", "学习", "自习", "项目", "项目整理", "资料查询", "文档", "休息", "娱乐", "午餐", "吃饭"],
    )
    visual_hints = _pick_terms(query, ["照片", "截图", "PPT", "板书", "晚霞", "代码", "餐食", "项目资料"])

    keywords = _keywords(query)
    if "项目" in query or "lifetrace" in query.lower():
        keywords.extend(["LifeTrace", "项目整理", "资料", "文档", "WPS", "浏览器"])
    if "图书馆" in query:
        keywords.extend(["图书馆附近", "自习"])
    if "晚霞" in query:
        keywords.extend(["校园晚霞", "照片"])
    if "课" in query or "PPT" in query.upper():
        keywords.extend(["课程学习", "教学楼", "学习通", "课堂PPT"])
    if not keywords:
        keywords = [query]

    return {
        "searchText": " ".join([query] + keywords[:8]),
        "intent": _mock_intent(query),
        "timeHints": _dedupe(time_hints)[:8],
        "locationHints": _dedupe(location_hints)[:8],
        "appHints": _dedupe(app_hints)[:8],
        "activityHints": _dedupe(activity_hints)[:8],
        "visualHints": _dedupe(visual_hints)[:8],
        "keywords": _dedupe(keywords)[:10],
    }


def build_mock_selection(query: str, query_plan: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any]:
    selected = []
    for candidate in candidates[:5]:
        selected.append(
            {
                "candidateId": candidate["id"],
                "matchReason": _mock_match_reason(candidate, query_plan),
                "confidence": _confidence_from_score(float(candidate["score"])),
            }
        )

    best = candidates[0]
    headline = f"最可能是{best['sourceKey']}的记录"
    if best["sourceType"].startswith("month"):
        headline = f"最可能在{best['sourceKey']}总结中"

    return {
        "answer": {
            "headline": headline[:28],
            "paragraph": (
                f"根据检索到的候选记忆，最接近“{query}”的是“{best['title']}”。"
                f"它的时间、标题或证据与问题中的线索更接近，适合作为这次模糊搜索的入口。"
            ),
        },
        "selectedResults": selected,
        "relatedQuestions": [
            "这条记忆对应的当天还有哪些片段？",
            "这条线索在阶段总结里是否也出现过？",
            "能不能只看包含照片或截图的记录？",
        ],
        "frontendHints": {
            "accent": _accent_for_candidate(best),
        },
    }


def _mock_match_reason(candidate: dict[str, Any], query_plan: dict[str, Any]) -> str:
    hints = []
    for key in ("timeHints", "locationHints", "appHints", "activityHints", "visualHints", "keywords"):
        hints.extend(query_plan.get(key, []))
    haystack = " ".join(
        [
            candidate.get("title", ""),
            candidate.get("snippet", ""),
            candidate.get("timeRange", ""),
            candidate.get("metadataText", ""),
            " ".join(candidate.get("evidence", [])),
        ]
    )
    matched = [hint for hint in hints if hint and str(hint) in haystack]
    if matched:
        return f"命中了“{'、'.join(matched[:3])}”等线索。"
    return "标题、描述或证据与用户问题语义较接近。"


def _confidence_from_score(score: float) -> str:
    if score >= 0.55:
        return "high"
    if score >= 0.28:
        return "medium"
    return "low"


def _accent_for_candidate(candidate: dict[str, Any]) -> str:
    source_type = candidate.get("sourceType", "")
    title = candidate.get("title", "")
    if "项目" in title or "文档" in title or source_type == "month_pattern":
        return "violet"
    if "课程" in title or "学习" in title:
        return "blue"
    if "照片" in title or "晚霞" in title:
        return "rose"
    if "食堂" in title or "餐" in title:
        return "green"
    if "休息" in title or "娱乐" in title:
        return "slate"
    return "blue"


def _mock_intent(query: str) -> str:
    if "总结" in query or "这个月" in query or "本月" in query:
        return "open_summary"
    if "规律" in query or "经常" in query or "阶段" in query:
        return "find_pattern"
    if re.search(r"\d{4}-\d{2}(?:-\d{2})?", query):
        return "find_day"
    return "find_memory"


def _pick_terms(text: str, terms: list[str]) -> list[str]:
    lowered = text.lower()
    return [term for term in terms if term.lower() in lowered]


def _keywords(text: str) -> list[str]:
    ascii_terms = re.findall(r"[a-zA-Z0-9_]+", text)
    cjk_terms = re.findall(r"[\u4e00-\u9fff]{2,}", text)
    return _dedupe(cjk_terms + ascii_terms)


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        cleaned = str(value).strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result
