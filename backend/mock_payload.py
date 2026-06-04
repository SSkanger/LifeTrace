"""Deterministic mock page payloads for local demo and frontend development."""

from __future__ import annotations

from typing import Any


def build_mock_page_payload(mode: str, data: dict[str, Any]) -> dict[str, Any]:
    """Build a contract-compliant payload without calling an LLM."""

    if mode == "daily":
        return _build_daily_payload(data)
    if mode == "week":
        return _build_week_payload(data)
    if mode == "month":
        return _build_month_payload(data)
    raise ValueError("mode must be 'daily', 'week', or 'month'")


def _build_daily_payload(data: dict[str, Any]) -> dict[str, Any]:
    date_key = data["dateKey"]
    basic_info = data.get("basicInfo", {})
    memory_segments = data.get("memorySegments", [])
    app_usage = data.get("appUsage", [])
    location_stays = data.get("locationStays", [])
    photo_moments = data.get("photoMoments", [])
    daily_context = data.get("dailyContextText", "")

    top_location = max(location_stays, key=lambda item: item.get("stayMinutes", 0), default={})
    top_app = max(app_usage, key=lambda item: item.get("durationMinutes", 0), default={})
    data_completeness = basic_info.get("dataCompleteness", "unknown")

    timeline = [
        _daily_segment_to_timeline_item(index + 1, segment)
        for index, segment in enumerate(memory_segments[:8])
    ]

    ranking_sections = [
        {
            "id": "location_stays",
            "title": "地点停留",
            "unit": "minutes",
            "items": [
                {
                    "rank": index + 1,
                    "label": item.get("locationLabel", "未知地点"),
                    "value": f"{item.get('stayMinutes', 0)} 分钟",
                    "description": item.get("stayType") or item.get("description") or "当天停留记录",
                }
                for index, item in enumerate(sorted(location_stays, key=lambda item: item.get("stayMinutes", 0), reverse=True)[:5])
            ],
        },
        {
            "id": "app_usage",
            "title": "App 使用",
            "unit": "minutes",
            "items": [
                {
                    "rank": index + 1,
                    "label": item.get("appName", "未知 App"),
                    "value": f"{item.get('durationMinutes', 0)} 分钟",
                    "description": item.get("note") or item.get("appCategory") or "当天 App 使用记录",
                }
                for index, item in enumerate(sorted(app_usage, key=lambda item: item.get("durationMinutes", 0), reverse=True)[:5])
            ],
        },
    ]

    insight_cards = [
        {
            "id": "day_main_thread",
            "title": "这一天的主线比较清楚",
            "description": _clip_text(daily_context, 110),
            "evidence": [_fact_text("当天类型", basic_info.get("dayType", "暂无")), _fact_text("生活片段数", f"{len(memory_segments)} 个")],
            "type": "highlight",
        },
        {
            "id": "strongest_memory",
            "title": "最适合作为回看入口的片段",
            "description": _pick_memory_description(memory_segments),
            "evidence": _pick_evidence(memory_segments, fallback="当天有可追溯的生活片段记录"),
            "type": "suggestion",
        },
        {
            "id": "visual_memory",
            "title": "照片补充了生活感",
            "description": _photo_description(photo_moments),
            "evidence": _photo_evidence(photo_moments),
            "type": "highlight",
        },
    ]

    return {
        "schemaVersion": "lifetrace.page.v1",
        "pageType": "daily",
        "sourceKey": date_key,
        "title": f"{date_key} 生活回放",
        "subtitle": basic_info.get("dayType", "当天生活记录"),
        "dataQualityNote": _data_quality_note(data_completeness),
        "summary": {
            "headline": _daily_headline(basic_info),
            "paragraph": _clip_text(daily_context, 170),
            "tags": _daily_tags(data),
        },
        "quickFacts": [
            {
                "id": "day_type",
                "label": "当天类型",
                "value": basic_info.get("dayType", "暂无"),
                "description": "根据当天地点、App 和照片记录综合整理。",
            },
            {
                "id": "main_location",
                "label": "主要地点",
                "value": top_location.get("locationLabel", "暂无"),
                "description": top_location.get("stayType", "当天没有明显地点停留记录。"),
            },
            {
                "id": "top_app",
                "label": "主要 App",
                "value": top_app.get("appName", "暂无"),
                "description": top_app.get("note", "当天没有明显 App 使用记录。"),
            },
            {
                "id": "photo_moments",
                "label": "照片片段",
                "value": f"{sum(item.get('photoCount', 0) for item in photo_moments)} 张",
                "description": "照片和截图用于补充当天的视觉记忆。",
            },
        ],
        "timeline": timeline,
        "rankingSections": ranking_sections,
        "insightCards": insight_cards,
        "memoryQuestions": [
            "这一天最值得保留下来的一个片段是什么？",
            "下午的项目整理有没有留下可以继续推进的线索？",
            "晚间的休息方式是否让当天节奏收得比较舒服？",
        ],
        "frontendHints": {
            "defaultView": "timeline",
            "accent": "blue",
            "density": "comfortable",
        },
    }


def _build_week_payload(data: dict[str, Any]) -> dict[str, Any]:
    week_key = data["weekKey"]
    basic_info = data.get("basicInfo", {})
    days = data.get("days", [])
    missing_days = basic_info.get("missingDays", [])

    location_totals: dict[str, dict[str, Any]] = {}
    app_category_totals: dict[str, dict[str, Any]] = {}
    photo_scene_totals: dict[str, dict[str, Any]] = {}
    activity_counts: dict[str, int] = {}

    for day in days:
        for part in str(day.get("basicInfo", {}).get("dayType", "")).replace("＋", "+").split("+"):
            activity = part.strip()
            if activity:
                activity_counts[activity] = activity_counts.get(activity, 0) + 1
        for stay in day.get("locationStays", []):
            label = stay.get("locationLabel", "未知地点")
            entry = location_totals.setdefault(label, {"locationLabel": label, "totalStayMinutes": 0, "stayTypes": []})
            entry["totalStayMinutes"] += int(stay.get("stayMinutes", 0))
            if stay.get("stayType"):
                entry["stayTypes"].append(stay["stayType"])
        for app in day.get("appUsage", []):
            category = app.get("appCategory", "未知类型")
            entry = app_category_totals.setdefault(category, {"appCategory": category, "totalMinutes": 0})
            entry["totalMinutes"] += int(app.get("durationMinutes", 0))
        for photo in day.get("photoMoments", []):
            scene = photo.get("sceneLabel", "照片")
            entry = photo_scene_totals.setdefault(scene, {"sceneLabel": scene, "count": 0})
            entry["count"] += int(photo.get("photoCount", 0))

    top_location = max(location_totals.values(), key=lambda item: item.get("totalStayMinutes", 0), default={})
    top_activity_name = max(activity_counts, key=activity_counts.get, default="暂无")
    top_day = max(days, key=lambda day: len(day.get("memorySegments", [])), default={})
    total_segments = sum(len(day.get("memorySegments", [])) for day in days)
    total_photos = sum(int(photo.get("photoCount", 0)) for day in days for photo in day.get("photoMoments", []))

    daily_items = [
        {
            "rank": index + 1,
            "label": day.get("dateKey", f"day_{index + 1}"),
            "value": f"{len(day.get('memorySegments', []))} 个片段",
            "description": _clip_text(day.get("dailyContextText", day.get("basicInfo", {}).get("dayType", "当天记录")), 86),
        }
        for index, day in enumerate(days[:7])
    ]

    location_items = [
        {
            "rank": index + 1,
            "label": item["locationLabel"],
            "value": f"{item['totalStayMinutes']} 分钟",
            "description": "、".join(_limited_strings(item.get("stayTypes", []), 2, "本周地点停留记录")),
        }
        for index, item in enumerate(sorted(location_totals.values(), key=lambda item: item["totalStayMinutes"], reverse=True)[:6])
    ]

    app_items = [
        {
            "rank": index + 1,
            "label": item["appCategory"],
            "value": f"{item['totalMinutes']} 分钟",
            "description": f"本周 {item['appCategory']} 类 App 使用记录汇总。",
        }
        for index, item in enumerate(sorted(app_category_totals.values(), key=lambda item: item["totalMinutes"], reverse=True)[:6])
    ]

    photo_items = [
        {
            "rank": index + 1,
            "label": item["sceneLabel"],
            "value": f"{item['count']} 张",
            "description": f"本周出现的 {item['sceneLabel']} 照片或截图线索。",
        }
        for index, item in enumerate(sorted(photo_scene_totals.values(), key=lambda item: item["count"], reverse=True)[:6])
    ]

    focus_evidence = [
        f"本周覆盖 {len(days)} 天，共 {total_segments} 个生活片段",
        f"主要地点为 {top_location.get('locationLabel', '暂无')}",
        f"反复出现的主题包括 {top_activity_name}",
    ]
    project_days = [
        day.get("dateKey", "")
        for day in days
        if "项目" in str(day.get("basicInfo", {}).get("dayType", "")) or "LifeTrace" in day.get("dailyContextText", "")
    ]
    visual_days = [
        day.get("dateKey", "")
        for day in days
        if any(photo.get("photoCount", 0) for photo in day.get("photoMoments", []))
    ]

    insight_cards = [
        {
            "id": "week_main_thread",
            "title": "这一周以学习和项目推进为主",
            "description": _week_context_sentence(days, top_activity_name),
            "evidence": _limited_strings(focus_evidence, 5, "本周有连续的每日生活片段"),
            "type": "highlight",
        },
        {
            "id": "project_progress",
            "title": "LifeTrace 项目线索连续出现",
            "description": "多天记录中出现了 LifeTrace、前后端接口、数据契约、周总结脚本和静态 JSON 等项目相关内容。",
            "evidence": _limited_strings([f"{date} 出现项目相关记录" for date in project_days], 5, "本周有项目相关记录"),
            "type": "pattern",
        },
        {
            "id": "visual_memory",
            "title": "照片补充了课程、项目和校园生活",
            "description": f"本周共有 {total_photos} 张照片或截图线索，覆盖课堂、文档、代码界面和校园生活场景。",
            "evidence": _limited_strings([f"{date} 有照片或截图记录" for date in visual_days], 5, "本周有照片或截图记录"),
            "type": "highlight",
        },
        {
            "id": "review_suggestion",
            "title": "适合从项目推进最完整的一天回看",
            "description": f"可以优先回看 {top_day.get('dateKey', week_key)}，这一天的片段数量较多，适合作为本周入口。",
            "evidence": _limited_strings(
                [f"{top_day.get('dateKey', week_key)} 有 {len(top_day.get('memorySegments', []))} 个生活片段"],
                5,
                "本周有可回看的生活片段",
            ),
            "type": "suggestion",
        },
    ]

    return {
        "schemaVersion": "lifetrace.page.v1",
        "pageType": "week",
        "sourceKey": week_key,
        "title": f"{week_key} 周总结",
        "subtitle": "从连续 7 天的每日线索中回看这一周的学习、项目和生活节奏。",
        "dataQualityNote": _week_data_quality_note(basic_info.get("dataCompleteness", "unknown"), missing_days, len(days)),
        "summary": {
            "headline": "学习与项目交替推进",
            "paragraph": _week_context_sentence(days, top_activity_name),
            "tags": _week_tags(days, top_location.get("locationLabel", "")),
        },
        "quickFacts": [
            {
                "id": "week_range",
                "label": "时间范围",
                "value": basic_info.get("weekRange", week_key),
                "description": "本周总结覆盖的日期范围。",
            },
            {
                "id": "available_days",
                "label": "覆盖天数",
                "value": f"{len(days)} 天",
                "description": "用于判断周总结的数据覆盖范围。",
            },
            {
                "id": "main_location",
                "label": "主要地点",
                "value": top_location.get("locationLabel", "暂无"),
                "description": f"本周累计停留约 {top_location.get('totalStayMinutes', 0)} 分钟。",
            },
            {
                "id": "main_activity",
                "label": "主要主线",
                "value": top_activity_name,
                "description": "根据 7 天 dayType 和生活片段综合整理。",
            },
        ],
        "timeline": [],
        "rankingSections": [
            {
                "id": "daily_overview",
                "title": "每日主线",
                "unit": "mixed",
                "items": daily_items,
            },
            {
                "id": "main_locations",
                "title": "主要地点",
                "unit": "minutes",
                "items": location_items,
            },
            {
                "id": "app_categories",
                "title": "App 类型",
                "unit": "minutes",
                "items": app_items,
            },
            {
                "id": "photo_scenes",
                "title": "照片场景",
                "unit": "count",
                "items": photo_items,
            },
        ],
        "insightCards": insight_cards,
        "memoryQuestions": [
            "这一周最稳定推进的事情是什么？",
            "哪一天最适合作为本周项目进展的入口？",
            "学习、项目和休息之间的节奏是否比较平衡？",
        ],
        "frontendHints": {
            "defaultView": "overview",
            "accent": "violet",
            "density": "comfortable",
        },
    }


def _build_month_payload(data: dict[str, Any]) -> dict[str, Any]:
    month_key = data["monthKey"]
    basic_info = data.get("basicInfo", {})
    monthly_stats = data.get("monthlyStats", {})
    highlights = data.get("monthHighlights", [])
    patterns = data.get("possiblePatterns", [])
    monthly_context = data.get("monthlyContextText", "")
    missing_days = basic_info.get("missingDays", [])

    top_location = _first_item(monthly_stats.get("mainLocationRanking", []))
    top_activity = _first_item(monthly_stats.get("mainActivityRanking", []))

    ranking_sections = [
        _ranking_section(
            section_id="main_locations",
            title="主要地点",
            unit="minutes",
            items=monthly_stats.get("mainLocationRanking", []),
            label_key="locationLabel",
            value_key="totalStayMinutes",
            value_suffix=" 分钟",
        ),
        _ranking_section(
            section_id="main_activities",
            title="主要活动",
            unit="minutes",
            items=monthly_stats.get("mainActivityRanking", []),
            label_key="activityType",
            value_key="estimatedMinutes",
            value_suffix=" 分钟",
        ),
        _ranking_section(
            section_id="app_categories",
            title="App 类型",
            unit="minutes",
            items=monthly_stats.get("appCategoryRanking", []),
            label_key="appCategory",
            value_key="totalMinutes",
            value_suffix=" 分钟",
        ),
        _ranking_section(
            section_id="photo_scenes",
            title="照片场景",
            unit="count",
            items=monthly_stats.get("photoSceneRanking", []),
            label_key="sceneLabel",
            value_key="count",
            value_suffix=" 次",
        ),
    ]

    insight_cards = []
    for index, item in enumerate(highlights[:4]):
        insight_cards.append(
            {
                "id": f"highlight_{index + 1}",
                "title": item.get("title", "本月重点"),
                "description": item.get("description", "本月有可回顾的重点内容。"),
                "evidence": _limited_strings(item.get("evidence", []), 5, "月度重点来自统计结果"),
                "type": "highlight",
            }
        )
    for index, item in enumerate(patterns[:3]):
        insight_cards.append(
            {
                "id": f"pattern_{index + 1}",
                "title": item.get("patternName", "可能规律"),
                "description": item.get("description", "本月大致呈现出一个可观察的生活规律。"),
                "evidence": _limited_strings(item.get("evidence", []), 5, "规律来自月度聚合数据"),
                "type": "pattern",
            }
        )

    return {
        "schemaVersion": "lifetrace.page.v1",
        "pageType": "month",
        "sourceKey": month_key,
        "title": f"{month_key} 阶段总结",
        "subtitle": "从地点、活动、App 和照片中回看这个月的生活节奏。",
        "dataQualityNote": _month_data_quality_note(basic_info.get("dataCompleteness", "unknown"), missing_days),
        "summary": {
            "headline": "学习与项目并行推进",
            "paragraph": _clip_text(monthly_context, 170),
            "tags": ["课程学习", "项目整理", "图书馆", "宿舍休息", "校园生活"],
        },
        "quickFacts": [
            {
                "id": "available_days",
                "label": "覆盖天数",
                "value": f"{basic_info.get('availableDays', 0)} 天",
                "description": "用于判断这个月总结的数据覆盖范围。",
            },
            {
                "id": "missing_days",
                "label": "缺失日期",
                "value": f"{len(missing_days)} 天",
                "description": "有缺失时，趋势判断会保持更谨慎。",
            },
            {
                "id": "top_location",
                "label": "主要地点",
                "value": top_location.get("locationLabel", "暂无"),
                "description": top_location.get("description", "本月没有明显地点排行。"),
            },
            {
                "id": "top_activity",
                "label": "主要活动",
                "value": top_activity.get("activityType", "暂无"),
                "description": top_activity.get("description", "本月没有明显活动排行。"),
            },
        ],
        "timeline": [],
        "rankingSections": ranking_sections,
        "insightCards": insight_cards[:8],
        "memoryQuestions": [
            "这个月最稳定的生活节奏是什么？",
            "项目推进最集中的线索出现在哪些场景里？",
            "哪些学习或休息习惯值得下个月继续保留？",
        ],
        "frontendHints": {
            "defaultView": "overview",
            "accent": "green",
            "density": "comfortable",
        },
    }


def _daily_segment_to_timeline_item(index: int, segment: dict[str, Any]) -> dict[str, Any]:
    category = str(segment.get("segmentType") or "memory")
    return {
        "id": f"seg_{index}",
        "timeRange": segment.get("timeRange", "未知时间"),
        "title": segment.get("title", "生活片段"),
        "category": category,
        "description": segment.get("description", "这段时间有一条生活记录。"),
        "evidence": _limited_strings(segment.get("evidence", []), 4, "该片段来自当天融合后的生活记录"),
        "sourceTypes": _source_types_for_segment(segment),
        "display": _display_for_category(category),
    }


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
    if not source_types:
        source_types.append("summary")
    return source_types


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


def _ranking_section(
    section_id: str,
    title: str,
    unit: str,
    items: list[dict[str, Any]],
    label_key: str,
    value_key: str,
    value_suffix: str,
) -> dict[str, Any]:
    sorted_items = sorted(items, key=lambda item: item.get(value_key, 0), reverse=True)
    return {
        "id": section_id,
        "title": title,
        "unit": unit,
        "items": [
            {
                "rank": index + 1,
                "label": item.get(label_key, "暂无"),
                "value": f"{item.get(value_key, 0)}{value_suffix}",
                "description": item.get("description") or item.get("mainStayType") or "月度统计记录",
            }
            for index, item in enumerate(sorted_items[:6])
        ],
    }


def _daily_headline(basic_info: dict[str, Any]) -> str:
    day_type = basic_info.get("dayType")
    if not day_type:
        return "这一天已有生活记录"
    first_part = str(day_type).split("+")[0].strip()
    return f"{first_part}的一天"


def _daily_tags(data: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    day_type = data.get("basicInfo", {}).get("dayType", "")
    for part in str(day_type).replace("＋", "+").split("+"):
        cleaned = part.strip()
        if cleaned and cleaned not in tags:
            tags.append(cleaned)
    for segment in data.get("memorySegments", []):
        title = segment.get("title")
        if title and len(tags) < 6:
            tags.append(str(title)[:8])
    return (tags or ["生活记录", "日常回看"])[:6]


def _pick_memory_description(memory_segments: list[dict[str, Any]]) -> str:
    if not memory_segments:
        return "当天还没有足够明确的片段，适合先从整体总结回看。"
    best = max(memory_segments, key=lambda item: len(item.get("evidence", [])))
    return best.get("description", "这个片段有较多证据支持，适合作为当天回看的入口。")


def _pick_evidence(memory_segments: list[dict[str, Any]], fallback: str) -> list[str]:
    if not memory_segments:
        return [fallback]
    best = max(memory_segments, key=lambda item: len(item.get("evidence", [])))
    return _limited_strings(best.get("evidence", []), 5, fallback)


def _photo_description(photo_moments: list[dict[str, Any]]) -> str:
    if not photo_moments:
        return "当天没有明显照片记录，页面会更多依赖地点和 App 使用线索。"
    labels = "、".join(item.get("sceneLabel", "照片") for item in photo_moments[:4])
    return f"当天照片或截图中出现了{labels}，能为文字记录补上一些具体画面。"


def _photo_evidence(photo_moments: list[dict[str, Any]]) -> list[str]:
    if not photo_moments:
        return ["当天照片记录较少"]
    return _limited_strings(
        [f"{item.get('time', '未知时间')} {item.get('sceneLabel', '照片')} {item.get('photoCount', 0)} 张" for item in photo_moments],
        5,
        "当天有照片记录",
    )


def _data_quality_note(completeness: str) -> str:
    if completeness == "high":
        return "这一天的数据较完整，适合按时间线回看。"
    if completeness == "medium":
        return "这一天有部分数据缺口，页面中的判断会保留适度不确定性。"
    if completeness == "low":
        return "这一天数据较少，只适合做轻量回看。"
    return "数据完整度未明确，页面内容以已记录的信息为准。"


def _month_data_quality_note(completeness: str, missing_days: list[str]) -> str:
    if missing_days:
        days = "、".join(missing_days[:4])
        more = "等" if len(missing_days) > 4 else ""
        return f"这个月有 {len(missing_days)} 天缺少记录，包括 {days}{more}，趋势判断会更谨慎。"
    return _data_quality_note(completeness).replace("这一天", "这个月")


def _week_data_quality_note(completeness: str, missing_days: list[str], available_days: int) -> str:
    if missing_days:
        days = "、".join(missing_days[:4])
        more = "等" if len(missing_days) > 4 else ""
        return f"这一周有 {len(missing_days)} 天缺少记录，包括 {days}{more}，周总结会保留适度不确定性。"
    if available_days < 7:
        return f"这一周目前覆盖 {available_days} 天记录，适合做轻量周回顾。"
    return _data_quality_note(completeness).replace("这一天", "这一周")


def _week_context_sentence(days: list[dict[str, Any]], top_activity_name: str) -> str:
    date_range = ""
    if days:
        date_range = f"{days[0].get('dateKey', '')} 到 {days[-1].get('dateKey', '')}"
    project_days = [day.get("dateKey", "") for day in days if "项目" in day.get("dailyContextText", "") or "LifeTrace" in day.get("dailyContextText", "")]
    course_days = [day.get("dateKey", "") for day in days if "课程" in day.get("dailyContextText", "") or "教学楼" in day.get("dailyContextText", "")]
    life_days = [day.get("dateKey", "") for day in days if "散步" in day.get("dailyContextText", "") or "拍摄" in day.get("dailyContextText", "")]
    parts = [
        f"{date_range} 这一周的记录比较完整，主线大致围绕{top_activity_name}展开。",
        f"课程相关线索出现在 {len(course_days)} 天，项目相关线索出现在 {len(project_days)} 天。",
        f"同时有 {len(life_days)} 天保留了散步、拍照或晚间放松等生活片段。"
    ]
    return _clip_text("".join(parts), 170)


def _week_tags(days: list[dict[str, Any]], top_location: str) -> list[str]:
    tags: list[str] = []
    for day in days:
        for part in str(day.get("basicInfo", {}).get("dayType", "")).replace("＋", "+").split("+"):
            cleaned = part.strip()
            if cleaned and cleaned not in tags:
                tags.append(cleaned)
    if top_location and top_location not in tags:
        tags.append(top_location)
    return (tags or ["周度回顾", "生活记录"])[:6]


def _fact_text(label: str, value: str) -> str:
    return f"{label}：{value}"


def _first_item(items: list[dict[str, Any]]) -> dict[str, Any]:
    return items[0] if items else {}


def _limited_strings(items: list[Any], limit: int, fallback: str) -> list[str]:
    cleaned = [str(item).strip() for item in items if str(item).strip()]
    return cleaned[:limit] or [fallback]


def _clip_text(text: str, max_length: int) -> str:
    stripped = _humanize_text(str(text).strip())
    if len(stripped) <= max_length:
        return stripped or "暂无足够文本总结，页面以结构化记录为主。"
    clipped = stripped[: max_length - 1]
    for mark in ("。", "；", ";"):
        last_mark_index = clipped.rfind(mark)
        if last_mark_index >= max_length * 0.55:
            return clipped[: last_mark_index + 1]
    return clipped.rstrip("，。；; ") + "。"


def _humanize_text(text: str) -> str:
    replacements = {
        "数据完整度为 high": "数据完整度较高",
        "数据完整度为 medium": "数据完整度中等",
        "数据完整度为 low": "数据完整度较低",
        "整体数据完整度为 high": "整体数据完整度较高",
        "整体数据完整度为 medium": "整体数据完整度中等",
        "整体数据完整度为 low": "整体数据完整度较低",
    }
    result = text
    for source, target in replacements.items():
        result = result.replace(source, target)
    return result
