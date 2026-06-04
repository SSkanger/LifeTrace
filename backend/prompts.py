"""Prompt templates for LifeTrace page payload generation."""

from __future__ import annotations

import json
from typing import Any


SYSTEM_PROMPT = """你是 LifeTrace 的记忆页面生成器。

你的任务是把已经清洗好的 LifeTrace JSON 数据转换为前端可直接渲染的页面 JSON，而不是重新发明事实。

必须遵守：
1. 只使用用户提供的源数据和读取说明，不编造日期、地点、App、照片场景、活动或趋势。
2. 所有判断都要能从源数据、证据列表、统计字段或总结文本中追溯到依据。
3. 不确定的表达必须使用“可能”“大概率”“看起来像是”“大致呈现”等措辞。
4. 不要在中文文案中暴露 dateKey、memorySegments、confidence、sourceTypes、high、medium、low 等技术字段名或枚举值；JSON 键名按契约保留。
5. 输出必须是严格 JSON 对象，不能包含 Markdown、代码块、解释文字或前后缀。
6. 顶层键、嵌套键、数组元素结构必须与输出契约一致。不要新增额外键，不要省略必需键。
7. 文案要适合 LifeTrace 记忆管理产品：克制、清晰、可回看，避免夸张营销语。
"""


PAGE_OUTPUT_CONTRACT = """输出 JSON 契约如下，顶层键必须且只能包含这些字段：

{
  "schemaVersion": "lifetrace.page.v1",
  "pageType": "daily、week 或 month",
  "sourceKey": "单日为 yyyy-MM-dd，周度为 yyyy-Www，月度为 yyyy-MM",
  "title": "页面标题，16 个汉字以内",
  "subtitle": "页面副标题，说明这份记忆页的主线",
  "dataQualityNote": "数据完整度提示。不要输出技术字段名；如果有缺失日期或数据不完整，需要温和说明",
  "summary": {
    "headline": "一句核心概括，24 个汉字以内",
    "paragraph": "80 到 180 个汉字的自然语言总结",
    "tags": ["2 到 6 个短标签"]
  },
  "quickFacts": [
    {
      "id": "稳定英文小写 id，例如 main_location",
      "label": "短标签",
      "value": "展示值",
      "description": "一句解释"
    }
  ],
  "timeline": [
    {
      "id": "稳定英文小写 id，例如 seg_1",
      "timeRange": "时间段；月度页面没有明确时间线时返回空数组",
      "title": "片段标题",
      "category": "片段类型英文小写，例如 class/project_work/rest",
      "description": "片段说明",
      "evidence": ["1 到 4 条可追溯证据"],
      "sourceTypes": ["app_usage/location/photo/ocr/summary/stats/highlight/pattern 中的若干项"],
      "display": {
        "icon": "home/book-open/utensils/laptop/map-pin/camera/moon/chart-bar/sparkles/alert-circle 之一",
        "tone": "blue/green/amber/rose/violet/slate 之一"
      }
    }
  ],
  "rankingSections": [
    {
      "id": "稳定英文小写 id",
      "title": "排行标题",
      "unit": "minutes/count/mixed 之一",
      "items": [
        {
          "rank": 1,
          "label": "展示名称",
          "value": "展示值，带单位",
          "description": "一句解释"
        }
      ]
    }
  ],
  "insightCards": [
    {
      "id": "稳定英文小写 id",
      "title": "洞察标题",
      "description": "洞察说明",
      "evidence": ["1 到 5 条依据"],
      "type": "highlight/pattern/suggestion 之一"
    }
  ],
  "memoryQuestions": ["2 到 4 个适合用户回顾自己的问题"],
  "frontendHints": {
    "defaultView": "timeline 或 overview",
    "accent": "blue/green/amber/rose/violet/slate 之一",
    "density": "comfortable"
  }
}

单日页面生成规则：
- pageType 必须是 "daily"，sourceKey 使用源数据 dateKey。
- timeline 必须来自 memorySegments，按时间顺序输出 4 到 8 个片段。
- rankingSections 至少包含地点停留和 App 使用两个 section；如果数据不足可以返回空 items，但 section 仍保留。
- insightCards 生成 3 到 5 张，优先概括当天主线、重要记忆点和可回顾的问题。
- defaultView 使用 "timeline"。

月度阶段总结页面生成规则：
- pageType 必须是 "month"，sourceKey 使用源数据 monthKey。
- timeline 返回空数组。
- rankingSections 优先覆盖主要地点、主要活动、App 类型、照片场景四类统计。
- insightCards 来自 monthHighlights 和 possiblePatterns，type 分别使用 highlight 或 pattern。
- 如果 missingDays 不为空，dataQualityNote 必须提示有部分日期缺失，避免把整个月说成完整覆盖。
- defaultView 使用 "overview"。

周度阶段总结页面生成规则：
- pageType 必须是 "week"，sourceKey 使用源数据 weekKey。
- 输入数据是 days 中连续 7 天的单日数据，不是已经总结好的周总结。
- timeline 返回空数组。
- rankingSections 优先覆盖每日主线、主要地点、App 类型、照片场景四类信息。
- insightCards 需要从 7 天 dailyContextText、memorySegments 和证据中选择本周重点、可能规律和适合回看的建议。
- 可以总结本周生活节奏，但必须能追溯到具体日期、地点、App、照片或 memorySegments 证据。
- 如果 missingDays 不为空，dataQualityNote 必须提示有部分日期缺失，避免把整周说成完整覆盖。
- defaultView 使用 "overview"。
"""


def build_messages(mode: str, data: dict[str, Any], read_guide: dict[str, Any]) -> list[dict[str, str]]:
    """Build chat messages for a LifeTrace page payload request."""

    if mode not in {"daily", "week", "month"}:
        raise ValueError("mode must be 'daily', 'week', or 'month'")

    task_names = {
        "daily": "单日生活回放页",
        "week": "周度阶段总结页",
        "month": "月度阶段总结页",
    }
    task_name = task_names[mode]
    user_prompt = f"""请根据下面的 LifeTrace 数据生成「{task_name}」前端页面 JSON。

输出要求：
{PAGE_OUTPUT_CONTRACT}

读取说明 JSON：
{json.dumps(read_guide, ensure_ascii=False, indent=2)}

源数据 JSON：
{json.dumps(data, ensure_ascii=False, indent=2)}
"""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
