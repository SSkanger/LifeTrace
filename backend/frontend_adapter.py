"""Frontend-facing view adapters for the current LifeTrace UI."""

from __future__ import annotations

from datetime import date, datetime
import re
from typing import Any

from display_service import generate_display_payload
from memory_index import build_memory_items
from service import DEFAULT_INPUTS, generate_page_payload, read_json
from search_service import search_memory


def get_today_overview(mock: bool = False, timeout: int = 90) -> dict[str, Any]:
    """Return the home page today-summary shape used by the current frontend."""

    daily_data = read_json(DEFAULT_INPUTS["daily"]["data"])
    display = generate_display_payload("daily", data=daily_data, mock=mock, temperature=0, timeout=timeout)
    summary = display["homeTodaySummary"]
    chips = summary["chips"]
    return {
        "date": display["sourceKey"],
        "title": summary["headline"],
        "text": _clip(summary["paragraph"], 120),
        "tags": chips,
        "homeTodaySummary": {
            "date": display["sourceKey"],
            "headline": summary["headline"],
            "paragraph": _clip(summary["paragraph"], 120),
            "chips": chips,
        },
    }


def get_calendar_month(year: int, month: int) -> dict[str, Any]:
    """Return month metadata and known memory days for the calendar page."""

    memory_days: list[int] = []
    day_summaries: list[dict[str, Any]] = []
    for daily_data in _load_week_days():
        date_key = str(daily_data.get("dateKey", ""))
        try:
            daily_date = datetime.strptime(date_key, "%Y-%m-%d").date()
        except ValueError:
            continue

        if daily_date.year == year and daily_date.month == month:
            memory_days.append(daily_date.day)
            day_summaries.append(
                {
                    "date": date_key,
                    "day": daily_date.day,
                    "hasData": True,
                    "clueCount": _clue_count(daily_data),
                    "dataQuality": daily_data.get("basicInfo", {}).get("dataCompleteness", "unknown"),
                }
            )

    return {
        "year": year,
        "month": month,
        "memoryDays": sorted(memory_days),
        "daySummaries": day_summaries,
    }


def get_daily_review(
    date_key: str | None = None,
    mock: bool = False,
    timeout: int = 90,
) -> dict[str, Any]:
    """Return the selected-day and review-page shape used by the current frontend."""

    daily_data = _find_daily_data(date_key) or read_json(DEFAULT_INPUTS["daily"]["data"])
    source_date = str(daily_data.get("dateKey", ""))
    if date_key and date_key != source_date:
        return _empty_daily_review(date_key)

    display = generate_display_payload("daily", data=daily_data, mock=mock, temperature=0, timeout=timeout)
    timeline = _merge_timeline_texts_with_raw_segments(display["timelineTexts"], daily_data.get("memorySegments", []))
    events = [_timeline_event(item) for item in timeline]

    return {
        "date": display["sourceKey"],
        "hasData": True,
        "clueCount": len(daily_data.get("memorySegments", [])),
        "selectedDaySummary": display["selectedDaySummary"],
        "dailyOverview": display["dailyOverview"],
        "quickFacts": _quick_facts_from_daily_data(daily_data),
        "events": events,
        "timeline": events,
        "dataQualityNote": _data_quality_note(daily_data.get("basicInfo", {}).get("dataCompleteness", "unknown"), "这一天"),
    }


def get_search_guide() -> dict[str, Any]:
    """Return search suggestions for the search panel before the user submits a query."""

    daily_data = read_json(DEFAULT_INPUTS["daily"]["data"])
    month_data = read_json(DEFAULT_INPUTS["month"]["data"])
    suggested = []

    for photo in daily_data.get("photoMoments", []):
        scene = str(photo.get("sceneLabel", "")).strip()
        if scene:
            suggested.append({"text": scene, "hot": True})

    for stay in daily_data.get("locationStays", []):
        location = str(stay.get("locationLabel", "")).strip()
        if location:
            suggested.append({"text": f"{location}做了什么", "hot": True})

    for app in daily_data.get("appUsage", []):
        app_name = str(app.get("appName", "")).strip()
        if app_name:
            suggested.append({"text": f"{app_name}相关记录", "hot": False})

    discovery = []
    stats = month_data.get("monthlyStats", {})
    if stats.get("mainLocationRanking"):
        discovery.append("最近常去地点")
    if stats.get("photoSceneRanking"):
        discovery.append("有照片的日子")
    if stats.get("mainActivityRanking"):
        discovery.append("学习和项目状态")
    discovery.append("这个月的高光时刻")

    return {
        "searchGuide": {
            "suggestedQueries": _dedupe_query_items(suggested)[:4],
            "discoveryEntries": _dedupe_strings(discovery)[:4],
        }
    }


def search_memories_for_frontend(
    query: str,
    mock: bool = False,
    top_k: int = 5,
    candidate_k: int = 16,
    rebuild_index: bool = False,
    timeout: int = 90,
) -> dict[str, Any]:
    """Return search results in the card shape used by the current frontend."""

    if not query.strip():
        raise ValueError("query must not be empty")

    try:
        payload = search_memory(
            query=query,
            mock=mock,
            top_k=top_k,
            candidate_k=candidate_k,
            rebuild_index=rebuild_index,
            timeout=timeout,
        )
    except Exception:
        if not mock:
            raise
        return _fallback_mock_search(query=query, top_k=top_k)

    results = []
    for index, item in enumerate(payload["results"]):
        results.append(
            {
                "id": item["id"],
                "title": item["title"],
                "summary": item["snippet"],
                "badge": "最相关" if index == 0 else _confidence_label(item["confidence"]),
                "sourceItems": _source_items(item),
                "targetPage": "reviewPage" if item["openTarget"]["pageType"] == "daily" else "summaryPage",
                "targetDate": item["openTarget"]["sourceKey"],
                "openTarget": item["openTarget"],
            }
        )

    return {
        "query": payload["query"],
        "searchResults": results,
    }


def get_weekly_summary(offset: int = 0, mock: bool = False, timeout: int = 90) -> dict[str, Any]:
    """Return a frontend weekly summary from the seven-day week input."""

    if offset != 0:
        return {
            "offset": offset,
            "weeklySummary": {
                "weekKey": "",
                "dateRange": "",
                "overview": "当前 demo 只准备了 2026-W21 这一周的数据。",
                "focus": "暂无这一周数据",
                "reviewSuggestion": "可以先回看已准备好的 2026-W21。",
                "tags": ["线索较少"],
                "dailyOverviews": [],
                "relatedMemories": [],
            },
        }

    week_data = read_json(DEFAULT_INPUTS["week"]["data"])
    display = generate_display_payload("week", data=week_data, mock=mock, temperature=0, timeout=timeout)
    weekly_display = display["weeklySummary"]
    days = week_data.get("days", [])
    basic_info = week_data.get("basicInfo", {})

    return {
        "offset": offset,
        "weeklySummary": {
            "weekKey": display["sourceKey"],
            "dateRange": str(basic_info.get("weekRange", "")).replace(" 至 ", " - "),
            "overview": weekly_display["overview"],
            "focus": weekly_display["focus"],
            "reviewSuggestion": weekly_display["reviewSuggestion"],
            "tags": weekly_display["tags"][:4],
            "dailyOverviews": [
                {
                    "weekday": _weekday_cn_from_text(day.get("basicInfo", {}).get("weekday", "")),
                    "date": item["date"],
                    "summary": item["summary"],
                    "tags": item["tags"][:3],
                }
                for day, item in zip(days, weekly_display["dailyOverviews"])
            ],
            "relatedMemories": _merge_related_memory_texts(weekly_display["relatedMemoryTexts"], days),
            "rankings": _week_rankings_from_data(week_data),
            "insights": _week_insights_from_display(weekly_display, week_data),
        },
    }


def _load_week_days() -> list[dict[str, Any]]:
    try:
        week_data = read_json(DEFAULT_INPUTS["week"]["data"])
    except Exception:
        return [read_json(DEFAULT_INPUTS["daily"]["data"])]
    days = week_data.get("days", [])
    return [day for day in days if isinstance(day, dict)]


def _find_daily_data(date_key: str | None) -> dict[str, Any] | None:
    if not date_key:
        return None
    for day in _load_week_days():
        if day.get("dateKey") == date_key:
            return day
    return None


def _weekday_cn_from_text(value: str) -> str:
    mapping = {
        "Monday": "周一",
        "Tuesday": "周二",
        "Wednesday": "周三",
        "Thursday": "周四",
        "Friday": "周五",
        "Saturday": "周六",
        "Sunday": "周日",
    }
    return mapping.get(str(value), str(value) or "未知")


def _day_tags(day: dict[str, Any]) -> list[str]:
    tags = []
    day_type = day.get("basicInfo", {}).get("dayType", "")
    for part in str(day_type).replace("＋", "+").split("+"):
        cleaned = part.strip()
        if cleaned:
            tags.append(cleaned)
    return _dedupe_strings(tags)


def _related_memories_from_week_days(days: list[dict[str, Any]]) -> list[dict[str, str]]:
    memories = []
    for day in days:
        segments = day.get("memorySegments", [])
        if not segments:
            continue
        best = max(segments, key=lambda item: len(item.get("evidence", [])))
        memories.append(
            {
                "title": best.get("title", "生活片段"),
                "subtitle": _clip(best.get("description", ""), 42),
                "targetDate": day.get("dateKey", ""),
            }
        )
    return memories[:3]


def get_monthly_summary(year: int | None = None, month: int | None = None, mock: bool = False, timeout: int = 90) -> dict[str, Any]:
    """Return the monthly summary shape used by the current summary panel."""

    payload = generate_page_payload("month", mock=mock, temperature=0, timeout=timeout)
    source_year, source_month = _parse_month_key(payload["sourceKey"])
    if year and month and (year != source_year or month != source_month):
        return {
            "year": year,
            "month": month,
            "monthlySummary": {
                "headline": "这个月的线索还不够完整",
                "paragraph": "当前数据中还没有整理到这个月份的完整总结。",
                "tags": ["线索较少"],
                "rhythm": "暂时没有足够连续的线索判断生活节奏。",
                "places": "地点线索较少，建议进入具体日期查看。",
                "reviewSuggestion": "可以通过日期回顾补充更多片段。",
            },
            "recommendedMemories": [],
        }

    return {
        "year": source_year,
        "month": source_month,
        "monthlySummary": {
            "headline": payload["summary"]["headline"],
            "paragraph": payload["summary"]["paragraph"],
            "tags": payload["summary"]["tags"],
            "rhythm": _first_insight(payload, "pattern") or _first_insight(payload, "highlight"),
            "places": _ranking_sentence(payload, "地点"),
            "reviewSuggestion": _first_insight(payload, "suggestion") or _fallback_review_suggestion(payload),
        },
        "recommendedMemories": _recommended_memories(payload),
        "rankings": payload["rankingSections"],
        "insights": payload["insightCards"],
    }


def _timeline_event(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item["id"],
        "time": item["timeRange"],
        "timeRange": item["timeRange"],
        "title": item["title"],
        "text": item["description"],
        "description": item["description"],
        "tags": item.get("tags") or _dedupe_strings([item.get("category", "")] + item.get("sourceTypes", []) + item.get("evidence", [])[:1])[:4],
        "sourceTypes": item.get("sourceTypes", []),
        "evidence": item.get("evidence", []),
        "icon": item.get("display", {}).get("icon", "sparkles"),
        "tone": item.get("display", {}).get("tone", "blue"),
        "photo": item.get("photo"),
        "photos": item.get("photos", []),
    }


def _empty_daily_review(date_key: str) -> dict[str, Any]:
    return {
        "date": date_key,
        "hasData": False,
        "clueCount": 0,
        "events": [],
        "timeline": [],
        "selectedDaySummary": {
            "headline": "这一天线索较少",
            "abstract": "当前数据中还没有整理到这一天的完整回顾线索。",
            "keywords": ["线索较少"],
        },
        "dailyOverview": {
            "headline": "暂无完整回顾",
            "paragraph": "可以先查看已有日期，或等待更多生活线索同步后再生成。",
            "tags": ["待补充"],
        },
    }


def _merge_timeline_texts_with_raw_segments(
    timeline_texts: list[dict[str, Any]],
    segments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged = []
    for index, segment in enumerate(segments[:8]):
        text_item = timeline_texts[index] if index < len(timeline_texts) and isinstance(timeline_texts[index], dict) else {}
        category = str(segment.get("segmentType") or "memory")
        merged.append(
            {
                "id": f"seg_{index + 1}",
                "timeRange": segment.get("timeRange", "未知时间"),
                "title": text_item.get("title") or segment.get("title") or "生活片段",
                "description": text_item.get("description") or segment.get("description") or "这段时间有一条生活记录。",
                "tags": _limited_strings(text_item.get("tags", []), 4, category),
                "category": category,
                "evidence": _limited_strings(
                    segment.get("evidence", []),
                    4,
                    "该片段来自当天融合后的生活记录",
                ),
                "sourceTypes": _source_types_for_segment(segment),
                "display": _display_for_category(category),
                "photo": _primary_photo_for_segment(segment, category),
                "photos": _photos_for_segment(segment, category),
            }
        )
    return merged


def _merge_timeline_with_raw_segments(
    timeline: list[dict[str, Any]],
    segments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged = []
    count = min(max(len(timeline), len(segments)), 8)
    for index in range(count):
        item = timeline[index] if index < len(timeline) else {}
        segment = segments[index] if index < len(segments) else {}
        category = str(segment.get("segmentType") or item.get("category") or "memory")
        merged.append(
            {
                **item,
                "id": f"seg_{index + 1}",
                "timeRange": segment.get("timeRange", item.get("timeRange", "未知时间")),
                "title": item.get("title") or segment.get("title") or "生活片段",
                "description": item.get("description") or segment.get("description") or "这段时间有一条生活记录。",
                "category": category,
                "evidence": _limited_strings(
                    segment.get("evidence", item.get("evidence", [])),
                    4,
                    "该片段来自当天融合后的生活记录",
                ),
                "sourceTypes": _source_types_for_segment(segment) if segment else item.get("sourceTypes", []),
                "display": item.get("display") or _display_for_category(category),
                "photo": item.get("photo") or _primary_photo_for_segment(segment, category),
                "photos": item.get("photos") or _photos_for_segment(segment, category),
            }
        )
    return merged


def _source_types_for_segment(segment: dict[str, Any]) -> list[str]:
    source_types = []
    if segment.get("relatedApps"):
        source_types.append("app_usage")
    if segment.get("relatedLocations"):
        source_types.append("location")
    if segment.get("relatedPhotos"):
        source_types.append("photo")
    evidence_text = " ".join(str(item) for item in segment.get("evidence", []))
    if "OCR" in evidence_text or "ocr" in evidence_text:
        source_types.append("ocr")
    return source_types or ["summary"]


def _display_for_category(category: str) -> dict[str, str]:
    mapping = {
        "morning_prepare": {"icon": "home", "tone": "amber"},
        "wake_up": {"icon": "home", "tone": "amber"},
        "class": {"icon": "book-open", "tone": "blue"},
        "meal": {"icon": "utensils", "tone": "green"},
        "project_work": {"icon": "laptop", "tone": "violet"},
        "research": {"icon": "laptop", "tone": "violet"},
        "document_work": {"icon": "laptop", "tone": "violet"},
        "daily_life": {"icon": "camera", "tone": "rose"},
        "rest": {"icon": "moon", "tone": "slate"},
    }
    return mapping.get(category, {"icon": "sparkles", "tone": "blue"})


def _photos_for_segment(segment: dict[str, Any], category: str) -> list[dict[str, str]]:
    photo_labels = _dedupe_strings([str(item) for item in segment.get("relatedPhotos", []) if str(item).strip()])[:4]
    if not photo_labels:
        return []

    evidence_text = " ".join(str(item) for item in segment.get("evidence", []))
    photos = []
    for label in photo_labels:
        photos.append(
            {
                "title": label,
                "meta": _photo_meta(label, evidence_text),
                "style": _photo_style(label, category),
            }
        )
    return photos


def _primary_photo_for_segment(segment: dict[str, Any], category: str) -> dict[str, str] | None:
    photos = _photos_for_segment(segment, category)
    return photos[0] if photos else None


def _photo_meta(label: str, evidence_text: str) -> str:
    count_match = re.search(rf"{re.escape(label)}[^，。；;]*?(\d+)\s*张", evidence_text)
    if count_match:
        return f"照片线索 · {count_match.group(1)} 张"

    time_match = re.search(r"(\d{1,2}:\d{2})[^，。；;]*" + re.escape(label), evidence_text)
    if time_match:
        return f"照片线索 · {time_match.group(1)}"

    return "照片线索"


def _photo_style(label: str, category: str) -> str:
    text = f"{label} {category}".lower()
    if any(keyword in text for keyword in ("晚霞", "天空", "sunset", "操场")):
        return "sunset"
    if any(keyword in text for keyword in ("图书馆", "文档", "项目", "资料", "报告", "代码", "计划", "ppt", "板书", "提纲")):
        return "library"
    if any(keyword in text for keyword in ("散步", "校园", "生活")):
        return "walk"
    return "memory"


def _home_chips(payload: dict[str, Any]) -> list[str]:
    chips = []
    for fact in payload.get("quickFacts", [])[:3]:
        label = str(fact.get("label", "")).strip()
        value = str(fact.get("value", "")).strip()
        if value:
            chips.append(value if not label else f"{label}：{value}")
    return chips or payload["summary"]["tags"][:3]


def _clue_count(daily_data: dict[str, Any]) -> int:
    return sum(
        len(daily_data.get(key, []))
        for key in ("appUsage", "locationStays", "photoMoments", "memorySegments")
    )


def _quick_facts_from_daily_data(daily_data: dict[str, Any]) -> list[dict[str, str]]:
    basic_info = daily_data.get("basicInfo", {})
    top_location = max(daily_data.get("locationStays", []), key=lambda item: item.get("stayMinutes", 0), default={})
    top_app = max(daily_data.get("appUsage", []), key=lambda item: item.get("durationMinutes", 0), default={})
    photo_count = sum(int(item.get("photoCount", 0)) for item in daily_data.get("photoMoments", []))
    return [
        {
            "id": "day_type",
            "label": "当天类型",
            "value": str(basic_info.get("dayType", "暂无")),
            "description": "根据当天地点、App 和照片记录综合整理。",
        },
        {
            "id": "main_location",
            "label": "主要地点",
            "value": str(top_location.get("locationLabel", "暂无")),
            "description": str(top_location.get("stayType", "当天没有明显地点停留记录。")),
        },
        {
            "id": "top_app",
            "label": "主要 App",
            "value": str(top_app.get("appName", "暂无")),
            "description": str(top_app.get("note", "当天没有明显 App 使用记录。")),
        },
        {
            "id": "photo_moments",
            "label": "照片片段",
            "value": f"{photo_count} 张",
            "description": "照片和截图用于补充当天的视觉记忆。",
        },
    ]


def _data_quality_note(completeness: str, subject: str) -> str:
    if completeness == "high":
        return f"{subject}的数据较完整，适合回看。"
    if completeness == "medium":
        return f"{subject}有部分数据缺口，页面中的判断会保留适度不确定性。"
    if completeness == "low":
        return f"{subject}数据较少，只适合做轻量回看。"
    return "数据完整度未明确，页面内容以已记录的信息为准。"


def _merge_related_memory_texts(items: list[dict[str, Any]], days: list[dict[str, Any]]) -> list[dict[str, str]]:
    valid_dates = {day.get("dateKey", "") for day in days}
    result = []
    for item in items:
        target_date = str(item.get("targetDate", ""))
        if target_date not in valid_dates:
            continue
        result.append(
            {
                "title": str(item.get("title", "推荐回看")),
                "subtitle": str(item.get("subtitle", "这一天有较完整的生活线索。")),
                "targetDate": target_date,
            }
        )
    return result or _related_memories_from_week_days(days)


def _week_rankings_from_data(week_data: dict[str, Any]) -> list[dict[str, Any]]:
    days = [day for day in week_data.get("days", []) if isinstance(day, dict)]
    location_totals: dict[str, int] = {}
    app_totals: dict[str, int] = {}
    photo_totals: dict[str, int] = {}

    for day in days:
        for stay in day.get("locationStays", []):
            label = str(stay.get("locationLabel", "未知地点"))
            location_totals[label] = location_totals.get(label, 0) + int(stay.get("stayMinutes", 0))
        for app in day.get("appUsage", []):
            category = str(app.get("appCategory", "未知类型"))
            app_totals[category] = app_totals.get(category, 0) + int(app.get("durationMinutes", 0))
        for photo in day.get("photoMoments", []):
            scene = str(photo.get("sceneLabel", "照片"))
            photo_totals[scene] = photo_totals.get(scene, 0) + int(photo.get("photoCount", 0))

    return [
        {
            "id": "daily_overview",
            "title": "每日主线",
            "unit": "mixed",
            "items": [
                {
                    "rank": index + 1,
                    "label": day.get("dateKey", f"day_{index + 1}"),
                    "value": f"{len(day.get('memorySegments', []))} 个片段",
                    "description": _clip(day.get("dailyContextText", ""), 80),
                }
                for index, day in enumerate(days)
            ],
        },
        _ranking_from_totals("main_locations", "主要地点", "minutes", location_totals, "分钟"),
        _ranking_from_totals("app_categories", "App 类型", "minutes", app_totals, "分钟"),
        _ranking_from_totals("photo_scenes", "照片场景", "count", photo_totals, "张"),
    ]


def _ranking_from_totals(section_id: str, title: str, unit: str, totals: dict[str, int], suffix: str) -> dict[str, Any]:
    return {
        "id": section_id,
        "title": title,
        "unit": unit,
        "items": [
            {
                "rank": index + 1,
                "label": label,
                "value": f"{value} {suffix}",
                "description": f"本周{title}统计项。",
            }
            for index, (label, value) in enumerate(sorted(totals.items(), key=lambda item: item[1], reverse=True)[:6])
        ],
    }


def _week_insights_from_display(weekly_display: dict[str, Any], week_data: dict[str, Any]) -> list[dict[str, Any]]:
    days = week_data.get("days", [])
    evidence = [f"本周覆盖 {len(days)} 天每日数据"]
    related_dates = [item.get("targetDate", "") for item in weekly_display.get("relatedMemoryTexts", []) if item.get("targetDate")]
    evidence.extend([f"{date} 被推荐为回看入口" for date in related_dates[:3]])
    return [
        {
            "id": "week_focus",
            "title": weekly_display.get("focus", "本周主线"),
            "description": weekly_display.get("overview", ""),
            "evidence": evidence[:5] or ["本周有每日生活片段记录"],
            "type": "highlight",
        },
        {
            "id": "review_suggestion",
            "title": "继续回看建议",
            "description": weekly_display.get("reviewSuggestion", ""),
            "evidence": evidence[:5] or ["本周有可回看的日期"],
            "type": "suggestion",
        },
    ]


def _source_items(item: dict[str, Any]) -> list[dict[str, str]]:
    source_items = [
        {"label": "时间", "value": item.get("timeRange", "")},
        {"label": "日期", "value": item.get("sourceKey", "")},
    ]
    source_types = item.get("sourceType", "")
    if source_types:
        source_items.append({"label": "来源", "value": _source_type_label(source_types)})
    return [entry for entry in source_items if entry["value"]]


def _source_type_label(source_type: str) -> str:
    labels = {
        "daily_segment": "生活片段",
        "daily_context": "日总结",
        "app_usage": "App",
        "location_stay": "位置",
        "photo_moment": "照片",
        "month_summary": "月总结",
        "month_highlight": "月度重点",
        "month_pattern": "月度规律",
        "month_stat": "月度统计",
    }
    return labels.get(source_type, source_type)


def _fallback_mock_search(query: str, top_k: int) -> dict[str, Any]:
    daily_data = read_json(DEFAULT_INPUTS.get("week", DEFAULT_INPUTS["daily"])["data"])
    month_data = read_json(DEFAULT_INPUTS["month"]["data"])
    items = build_memory_items(daily_data, month_data)
    terms = _search_terms(query)

    ranked = []
    for item in items:
        haystack = " ".join([item.title, item.text, " ".join(item.evidence)]).lower()
        score = sum(1 for term in terms if term.lower() in haystack)
        if score > 0:
            ranked.append((score, item))

    if not ranked:
        ranked = [(0, item) for item in items[:top_k]]

    ranked.sort(key=lambda pair: pair[0], reverse=True)
    results = []
    for index, (_, item) in enumerate(ranked[:top_k]):
        results.append(
            {
                "id": item.id,
                "title": item.title,
                "summary": _clip(item.text, 110),
                "badge": "最相关" if index == 0 else "可能相关",
                "sourceItems": [
                    entry
                    for entry in (
                        {"label": "时间", "value": item.time_range},
                        {"label": "日期", "value": item.source_key},
                        {"label": "来源", "value": _source_type_label(item.source_type)},
                    )
                    if entry["value"]
                ],
                "targetPage": "reviewPage" if item.page_type == "daily" else "summaryPage",
                "targetDate": item.source_key,
                "openTarget": {
                    "pageType": item.page_type,
                    "sourceKey": item.source_key,
                    "anchorId": item.anchor_id,
                },
            }
        )

    return {
        "query": query,
        "searchResults": results,
        "fallback": True,
    }


def _search_terms(query: str) -> list[str]:
    raw = str(query).strip()
    terms = re.findall(r"[a-zA-Z0-9_]+|[\u4e00-\u9fff]{2,}", raw)
    cjk_bigrams = [
        raw[index : index + 2]
        for index in range(len(raw) - 1)
        if all("\u4e00" <= char <= "\u9fff" for char in raw[index : index + 2])
    ]
    return _dedupe_strings(terms + cjk_bigrams)


def _confidence_label(confidence: str) -> str:
    return {"high": "高相关", "medium": "较相关", "low": "可能相关"}.get(confidence, "相关")


def _weekday_cn(value: date) -> str:
    return ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][value.weekday()]


def _weekly_review_suggestion(payload: dict[str, Any]) -> str:
    if payload.get("timeline"):
        title = payload["timeline"][0]["title"]
        return f"可以重点回看 {payload['sourceKey']} 的“{title}”等片段。"
    return "可以从这一天的摘要和关键事实开始回看。"


def _related_memories_from_timeline(timeline: list[dict[str, Any]], source_key: str) -> list[dict[str, str]]:
    memories = []
    for item in timeline[:2]:
        memories.append(
            {
                "title": item["title"],
                "subtitle": _clip(item["description"], 42),
                "targetDate": source_key,
            }
        )
    return memories


def _parse_month_key(month_key: str) -> tuple[int, int]:
    try:
        parsed = datetime.strptime(month_key, "%Y-%m")
        return parsed.year, parsed.month
    except ValueError:
        return 0, 0


def _first_insight(payload: dict[str, Any], insight_type: str) -> str:
    for item in payload.get("insightCards", []):
        if item.get("type") == insight_type:
            return item.get("description", "")
    return ""


def _ranking_sentence(payload: dict[str, Any], keyword: str) -> str:
    for section in payload.get("rankingSections", []):
        if keyword in section.get("title", "") and section.get("items"):
            labels = [item.get("label", "") for item in section["items"][:3] if item.get("label")]
            if labels:
                return "、".join(labels) + "是最常出现的相关地点。"
    return ""


def _fallback_review_suggestion(payload: dict[str, Any]) -> str:
    if payload.get("memoryQuestions"):
        return payload["memoryQuestions"][0]
    return "可以优先回看线索最完整的日期。"


def _recommended_memories(payload: dict[str, Any]) -> list[dict[str, str]]:
    recommendations = []
    for item in payload.get("insightCards", [])[:2]:
        recommendations.append(
            {
                "title": item["title"],
                "subtitle": _clip(item["description"], 52),
                "targetDate": payload["sourceKey"],
            }
        )
    return recommendations


def _dedupe_query_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    result = []
    for item in items:
        text = str(item.get("text", "")).strip()
        if text and text not in seen:
            seen.add(text)
            result.append({"text": text, "hot": bool(item.get("hot"))})
    return result


def _dedupe_strings(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        value = str(item).strip()
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _limited_strings(items: list[Any], max_len: int, fallback: str) -> list[str]:
    values = _dedupe_strings([str(item) for item in items if str(item).strip()])
    return values[:max_len] or [fallback]


def _clip(text: str, max_len: int) -> str:
    cleaned = " ".join(str(text).split())
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 1].rstrip("，。；、 ") + "…"
