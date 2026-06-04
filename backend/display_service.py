"""Generate LLM display copy and keep factual fields out of the model contract."""

from __future__ import annotations

import json
from typing import Any

from llm_client import DEFAULT_MAX_TOKENS
from service import DEFAULT_INPUTS, build_chat_client, read_json


DISPLAY_SCHEMA_VERSION = "lifetrace.llmDisplay.v1"


SYSTEM_PROMPT = """你是 LifeTrace 的前端展示文案生成器。

你的任务不是生成完整页面数据，而是只根据输入事实生成前端需要展示的自然语言文案。

必须遵守：
1. 只输出展示文案字段，不输出日期是否有数据、线索数量、时间段、证据、sourceTypes、targetPage、targetDate、memoryDays、sourceItems 等事实/索引/跳转字段。
2. 只使用输入 JSON 中明确出现的事实，不编造地点、日期、App、照片、课程、人物或趋势。
3. 如果依据不充分，使用“可能”“看起来”“大致”等谨慎表达。
4. timelineTexts 只能按输入 memorySegments 的顺序生成标题、描述和标签；segmentId 必须是 seg_1、seg_2 这样的稳定序号。
5. weeklySummary.dailyOverviews[].date 和 relatedMemoryTexts[].targetDate 只能复制输入 days[].dateKey，不能生成不存在的日期。
6. 输出必须是严格 JSON 对象，不能包含 Markdown、代码块、解释文字或前后缀。
"""


DAILY_CONTRACT = """单日展示文案输出契约，顶层键必须且只能包含：

{
  "schemaVersion": "lifetrace.llmDisplay.v1",
  "scope": "daily",
  "sourceKey": "yyyy-MM-dd",
  "homeTodaySummary": {
    "headline": "首页今日摘要标题，15 到 30 字",
    "paragraph": "首页今日摘要正文，60 到 120 字",
    "chips": ["2 到 4 个短标签或事实入口"]
  },
  "selectedDaySummary": {
    "headline": "日期页选中日期摘要标题",
    "abstract": "日期页摘要正文，80 到 150 字",
    "keywords": ["2 到 6 个关键词"]
  },
  "dailyOverview": {
    "headline": "每日回顾页概览标题",
    "paragraph": "每日回顾页概览正文，120 到 220 字",
    "tags": ["2 到 6 个标签"]
  },
  "timelineTexts": [
    {
      "segmentId": "seg_1",
      "title": "片段标题",
      "description": "片段描述",
      "tags": ["1 到 4 个标签"]
    }
  ]
}

注意：不要输出 timeRange、evidence、sourceTypes、targetPage、targetDate、hasData、clueCount。"""


WEEK_CONTRACT = """周度展示文案输出契约，顶层键必须且只能包含：

{
  "schemaVersion": "lifetrace.llmDisplay.v1",
  "scope": "week",
  "sourceKey": "yyyy-Www",
  "weeklySummary": {
    "overview": "周度概览正文，120 到 220 字",
    "focus": "这一周的主要主线，一句话",
    "reviewSuggestion": "适合回看的建议，一句话",
    "tags": ["2 到 6 个标签"],
    "dailyOverviews": [
      {
        "date": "yyyy-MM-dd，只能复制输入 days[].dateKey",
        "summary": "当天一句短概述",
        "tags": ["1 到 4 个标签"]
      }
    ],
    "relatedMemoryTexts": [
      {
        "targetDate": "yyyy-MM-dd，只能复制输入 days[].dateKey",
        "title": "推荐回看标题",
        "subtitle": "推荐回看理由"
      }
    ]
  }
}

注意：不要输出 weekRange、weekday、hasData、clueCount、timeRange、evidence、sourceTypes、targetPage、sourceItems、ranking 数值。"""


def generate_display_payload(
    scope: str,
    data: dict[str, Any] | None = None,
    read_guide: dict[str, Any] | None = None,
    mock: bool = False,
    temperature: float = 0.2,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    timeout: int = 90,
) -> dict[str, Any]:
    """Generate and validate LLM display-only copy."""

    if scope not in {"daily", "week"}:
        raise ValueError("scope must be 'daily' or 'week'")

    if data is None or read_guide is None:
        defaults = DEFAULT_INPUTS[scope]
        data = data or read_json(defaults["data"])
        read_guide = read_guide or read_json(defaults["guide"])

    if mock:
        payload = build_mock_display_payload(scope, data)
    else:
        client = build_chat_client(timeout=timeout)
        payload = client.create_json_payload(
            messages=build_display_messages(scope, data, read_guide),
            temperature=temperature,
            max_tokens=max_tokens,
        )

    payload = normalize_display_payload(payload, scope, data)
    validate_display_payload(payload, scope, data)
    return payload


def build_display_messages(scope: str, data: dict[str, Any], read_guide: dict[str, Any]) -> list[dict[str, str]]:
    if scope not in {"daily", "week"}:
        raise ValueError("scope must be 'daily' or 'week'")

    contract = DAILY_CONTRACT if scope == "daily" else WEEK_CONTRACT
    task_name = "单日展示文案" if scope == "daily" else "周度展示文案"
    user_prompt = f"""请根据下面的 LifeTrace 数据生成「{task_name}」JSON。

输出要求：
{contract}

读取说明 JSON：
{json.dumps(read_guide, ensure_ascii=False, indent=2)}

源数据 JSON：
{json.dumps(data, ensure_ascii=False, indent=2)}
"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def build_mock_display_payload(scope: str, data: dict[str, Any]) -> dict[str, Any]:
    if scope == "daily":
        return _mock_daily_display(data)
    if scope == "week":
        return _mock_week_display(data)
    raise ValueError("scope must be 'daily' or 'week'")


def normalize_display_payload(payload: dict[str, Any], scope: str, data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return payload

    if scope == "daily":
        source_key = str(data.get("dateKey", ""))
        _keep_keys(payload, {"schemaVersion", "scope", "sourceKey", "homeTodaySummary", "selectedDaySummary", "dailyOverview", "timelineTexts"})
        payload["schemaVersion"] = DISPLAY_SCHEMA_VERSION
        payload["scope"] = "daily"
        payload["sourceKey"] = source_key
        _normalize_text_block(payload, "homeTodaySummary", {"headline", "paragraph", "chips"})
        _normalize_text_block(payload, "selectedDaySummary", {"headline", "abstract", "keywords"})
        _normalize_text_block(payload, "dailyOverview", {"headline", "paragraph", "tags"})
        timeline_texts = payload.get("timelineTexts")
        if not isinstance(timeline_texts, list):
            timeline_texts = []
        segments = data.get("memorySegments", [])
        normalized = []
        for index, segment in enumerate(segments[:8]):
            item = timeline_texts[index] if index < len(timeline_texts) and isinstance(timeline_texts[index], dict) else {}
            _keep_keys(item, {"segmentId", "title", "description", "tags"})
            item["segmentId"] = f"seg_{index + 1}"
            item["title"] = _str_or_default(item.get("title"), segment.get("title", "生活片段"))
            item["description"] = _str_or_default(item.get("description"), segment.get("description", "这段时间有一条生活记录。"))
            item["tags"] = _limited_strings(item.get("tags", []), 4, [segment.get("segmentType", "生活片段")])
            normalized.append(item)
        payload["timelineTexts"] = normalized
        return payload

    source_key = str(data.get("weekKey", ""))
    _keep_keys(payload, {"schemaVersion", "scope", "sourceKey", "weeklySummary"})
    payload["schemaVersion"] = DISPLAY_SCHEMA_VERSION
    payload["scope"] = "week"
    payload["sourceKey"] = source_key
    weekly = payload.get("weeklySummary")
    if not isinstance(weekly, dict):
        weekly = {}
    _keep_keys(weekly, {"overview", "focus", "reviewSuggestion", "tags", "dailyOverviews", "relatedMemoryTexts"})
    days = [day for day in data.get("days", []) if isinstance(day, dict)]
    weekly["overview"] = _str_or_default(weekly.get("overview"), _clip(_join_day_contexts(days), 170))
    weekly["focus"] = _str_or_default(weekly.get("focus"), "学习与项目交替推进")
    weekly["reviewSuggestion"] = _str_or_default(weekly.get("reviewSuggestion"), "可以优先回看线索最完整的日期。")
    weekly["tags"] = _limited_strings(weekly.get("tags", []), 6, _week_tags(days))

    daily_overviews = weekly.get("dailyOverviews")
    if not isinstance(daily_overviews, list):
        daily_overviews = []
    normalized_days = []
    for index, day in enumerate(days[:7]):
        item = daily_overviews[index] if index < len(daily_overviews) and isinstance(daily_overviews[index], dict) else {}
        _keep_keys(item, {"date", "summary", "tags"})
        item["date"] = str(day.get("dateKey", ""))
        item["summary"] = _str_or_default(item.get("summary"), _clip(day.get("dailyContextText", ""), 90))
        item["tags"] = _limited_strings(item.get("tags", []), 4, _day_tags(day))
        normalized_days.append(item)
    weekly["dailyOverviews"] = normalized_days

    valid_dates = {day.get("dateKey", "") for day in days}
    related = weekly.get("relatedMemoryTexts")
    if not isinstance(related, list):
        related = []
    normalized_related = []
    for item in related:
        if not isinstance(item, dict):
            continue
        _keep_keys(item, {"targetDate", "title", "subtitle"})
        if item.get("targetDate") not in valid_dates:
            continue
        item["title"] = _str_or_default(item.get("title"), "推荐回看")
        item["subtitle"] = _str_or_default(item.get("subtitle"), "这一天有较完整的生活线索。")
        normalized_related.append(item)
        if len(normalized_related) >= 3:
            break
    if not normalized_related:
        normalized_related = _fallback_related_memories(days)
    weekly["relatedMemoryTexts"] = normalized_related
    payload["weeklySummary"] = weekly
    return payload


def validate_display_payload(payload: Any, scope: str, data: dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise ValueError("display payload must be a JSON object")
    _expect(payload.get("schemaVersion") == DISPLAY_SCHEMA_VERSION, "schemaVersion must be lifetrace.llmDisplay.v1")
    _expect(payload.get("scope") == scope, f"scope must be {scope}")

    if scope == "daily":
        _expect(payload.get("sourceKey") == data.get("dateKey"), "daily sourceKey must match dateKey")
        for key in ("homeTodaySummary", "selectedDaySummary", "dailyOverview"):
            _expect(isinstance(payload.get(key), dict), f"{key} must be an object")
        _expect(isinstance(payload.get("timelineTexts"), list), "timelineTexts must be an array")
        _expect(len(payload["timelineTexts"]) == min(len(data.get("memorySegments", [])), 8), "timelineTexts must match memorySegments count")
        return

    _expect(payload.get("sourceKey") == data.get("weekKey"), "week sourceKey must match weekKey")
    weekly = payload.get("weeklySummary")
    _expect(isinstance(weekly, dict), "weeklySummary must be an object")
    _expect(len(weekly.get("dailyOverviews", [])) == len(data.get("days", [])), "dailyOverviews must match days count")


def _mock_daily_display(data: dict[str, Any]) -> dict[str, Any]:
    context = data.get("dailyContextText", "")
    tags = _day_tags(data)
    headline = _daily_headline(data)
    return {
        "schemaVersion": DISPLAY_SCHEMA_VERSION,
        "scope": "daily",
        "sourceKey": data.get("dateKey", ""),
        "homeTodaySummary": {
            "headline": headline,
            "paragraph": _clip(context, 118),
            "chips": _candidate_chips(data)[:4],
        },
        "selectedDaySummary": {
            "headline": headline,
            "abstract": _clip(context, 145),
            "keywords": tags[:6],
        },
        "dailyOverview": {
            "headline": headline,
            "paragraph": _clip(context, 210),
            "tags": tags[:6],
        },
        "timelineTexts": [
            {
                "segmentId": f"seg_{index + 1}",
                "title": segment.get("title", "生活片段"),
                "description": segment.get("description", "这段时间有一条生活记录。"),
                "tags": _limited_strings(
                    [segment.get("segmentType", "")] + segment.get("relatedLocations", []) + segment.get("relatedApps", []) + segment.get("relatedPhotos", []),
                    4,
                    ["生活片段"],
                ),
            }
            for index, segment in enumerate(data.get("memorySegments", [])[:8])
        ],
    }


def _mock_week_display(data: dict[str, Any]) -> dict[str, Any]:
    days = [day for day in data.get("days", []) if isinstance(day, dict)]
    tags = _week_tags(days)
    return {
        "schemaVersion": DISPLAY_SCHEMA_VERSION,
        "scope": "week",
        "sourceKey": data.get("weekKey", ""),
        "weeklySummary": {
            "overview": _clip(_join_day_contexts(days), 200),
            "focus": "学习与 LifeTrace 项目推进是这一周的主线",
            "reviewSuggestion": "可以优先回看项目线索最密集的 5 月 23 日和周回顾较完整的 5 月 24 日。",
            "tags": tags[:6],
            "dailyOverviews": [
                {
                    "date": day.get("dateKey", ""),
                    "summary": _clip(day.get("dailyContextText", ""), 90),
                    "tags": _day_tags(day)[:4],
                }
                for day in days
            ],
            "relatedMemoryTexts": _fallback_related_memories(days),
        },
    }


def _normalize_text_block(payload: dict[str, Any], key: str, allowed_keys: set[str]) -> None:
    value = payload.get(key)
    if not isinstance(value, dict):
        value = {}
    _keep_keys(value, allowed_keys)
    for item_key in allowed_keys:
        if item_key in {"chips", "keywords", "tags"}:
            value[item_key] = _limited_strings(value.get(item_key, []), 6, ["生活记录"])
        else:
            value[item_key] = _str_or_default(value.get(item_key), "暂无足够文本总结。")
    payload[key] = value


def _fallback_related_memories(days: list[dict[str, Any]]) -> list[dict[str, str]]:
    ranked = sorted(days, key=lambda day: len(day.get("memorySegments", [])), reverse=True)
    result = []
    for day in ranked[:3]:
        segments = day.get("memorySegments", [])
        best = max(segments, key=lambda item: len(item.get("evidence", [])), default={})
        result.append(
            {
                "targetDate": day.get("dateKey", ""),
                "title": best.get("title", "推荐回看"),
                "subtitle": _clip(best.get("description", day.get("dailyContextText", "")), 48),
            }
        )
    return result


def _daily_headline(data: dict[str, Any]) -> str:
    day_type = str(data.get("basicInfo", {}).get("dayType", "")).replace("＋", "+")
    first = day_type.split("+")[0].strip()
    return f"{first}的一天" if first else "这一天已有生活记录"


def _candidate_chips(data: dict[str, Any]) -> list[str]:
    chips = []
    top_location = max(data.get("locationStays", []), key=lambda item: item.get("stayMinutes", 0), default={})
    if top_location:
        chips.append(f"{top_location.get('locationLabel', '地点')} {top_location.get('stayMinutes', 0)} 分钟")
    for photo in data.get("photoMoments", [])[:2]:
        if photo.get("sceneLabel"):
            chips.append(str(photo["sceneLabel"]))
    for app in data.get("appUsage", [])[:2]:
        if app.get("appName"):
            chips.append(str(app["appName"]))
    return _dedupe(chips) or _day_tags(data)


def _day_tags(day: dict[str, Any]) -> list[str]:
    tags = []
    day_type = day.get("basicInfo", {}).get("dayType", "")
    for part in str(day_type).replace("＋", "+").split("+"):
        cleaned = part.strip()
        if cleaned:
            tags.append(cleaned)
    return _dedupe(tags) or ["生活记录"]


def _week_tags(days: list[dict[str, Any]]) -> list[str]:
    tags = []
    for day in days:
        tags.extend(_day_tags(day))
    return _dedupe(tags)[:6] or ["周度回顾"]


def _join_day_contexts(days: list[dict[str, Any]]) -> str:
    return "".join(str(day.get("dailyContextText", "")) for day in days)


def _keep_keys(obj: dict[str, Any], allowed_keys: set[str]) -> None:
    for key in list(obj.keys()):
        if key not in allowed_keys:
            del obj[key]


def _limited_strings(items: Any, limit: int, fallback: list[str]) -> list[str]:
    if not isinstance(items, list):
        items = []
    values = _dedupe([str(item).strip() for item in items if str(item).strip()])
    return values[:limit] or fallback[:limit]


def _str_or_default(value: Any, fallback: str) -> str:
    cleaned = str(value).strip() if value is not None else ""
    return cleaned or fallback


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _clip(text: Any, max_len: int) -> str:
    cleaned = " ".join(str(text).split())
    if len(cleaned) <= max_len:
        return cleaned or "暂无足够文本总结。"
    return cleaned[: max_len - 1].rstrip("，。；、 ") + "…"


def _expect(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)
