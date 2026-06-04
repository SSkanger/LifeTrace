"""Prompt templates for LifeTrace fuzzy memory search."""

from __future__ import annotations

import json
from typing import Any


SEARCH_SYSTEM_PROMPT = """你是 LifeTrace 的记忆搜索助手。

你的任务不是编造回忆，而是帮助后端把用户的模糊表达转成可检索条件，并在候选记忆中选择最匹配的结果。

必须遵守：
1. 只使用用户问题和后端提供的候选记忆。
2. 不要编造候选里没有出现的日期、地点、App、照片场景或事件。
3. 不确定时使用“可能”“大概率”“看起来像是”“更接近”等措辞。
4. 输出必须是严格 JSON 对象，不能包含 Markdown、代码块、解释文字或前后缀。
5. JSON 键名和结构必须与契约一致，不要新增键，不要省略键。
"""


QUERY_PLAN_CONTRACT = """请把用户的模糊记忆问题转成下面的 JSON 检索计划，顶层键必须且只能包含这些字段：

{
  "searchText": "用于向量检索的一句话，保留用户核心含义并补全隐含意图",
  "intent": "find_memory/find_day/find_pattern/open_summary 之一",
  "timeHints": ["时间线索，例如 下午、晚上、2026-05、上周三；没有则返回空数组"],
  "locationHints": ["地点线索；没有则返回空数组"],
  "appHints": ["App 或工具线索；没有则返回空数组"],
  "activityHints": ["活动线索，例如 项目整理、课程学习、休息娱乐；没有则返回空数组"],
  "visualHints": ["照片、截图或视觉场景线索；没有则返回空数组"],
  "keywords": ["2 到 10 个检索关键词"]
}

规则：
- searchText 要适合语义向量检索，不要只重复原句。
- 如果用户问题很短，也要尽量抽取可用线索。
- 不要输出候选结果，不要回答问题，只生成检索计划。
"""


SELECTION_CONTRACT = """请从候选记忆中选择最匹配用户问题的结果，输出下面 JSON，顶层键必须且只能包含这些字段：

{
  "answer": {
    "headline": "一句搜索结论，28 个汉字以内",
    "paragraph": "60 到 160 个汉字，解释最可能对应哪些记忆以及为什么"
  },
  "selectedResults": [
    {
      "candidateId": "必须来自候选列表中的 id",
      "matchReason": "一句解释为什么匹配",
      "confidence": "high/medium/low 之一"
    }
  ],
  "relatedQuestions": ["2 到 4 个后续可追问问题"],
  "frontendHints": {
    "accent": "blue/green/amber/rose/violet/slate 之一"
  }
}

规则：
- selectedResults 最多 5 个，按匹配程度排序。
- 如果候选都很弱，也要选择最接近的 1 到 3 个，并在 paragraph 里说明“只找到较接近的记录”。
- candidateId 必须逐字复制候选 id。
- matchReason 只能引用候选中的时间、地点、App、照片场景、标题、描述或证据。
"""


def build_query_understanding_messages(query: str) -> list[dict[str, str]]:
    """Build messages for turning a user query into a retrieval plan."""

    user_prompt = f"""用户问题：
{query}

输出要求：
{QUERY_PLAN_CONTRACT}
"""

    return [
        {"role": "system", "content": SEARCH_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def build_candidate_selection_messages(
    query: str,
    query_plan: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Build messages for selecting the best candidates from retrieval results."""

    safe_candidates = [
        {
            "id": candidate["id"],
            "score": candidate["score"],
            "sourceType": candidate["sourceType"],
            "sourceKey": candidate["sourceKey"],
            "timeRange": candidate["timeRange"],
            "title": candidate["title"],
            "snippet": candidate["snippet"],
            "evidence": candidate["evidence"],
            "metadataText": candidate.get("metadataText", ""),
        }
        for candidate in candidates
    ]

    user_prompt = f"""用户问题：
{query}

检索计划：
{json.dumps(query_plan, ensure_ascii=False, indent=2)}

候选记忆：
{json.dumps(safe_candidates, ensure_ascii=False, indent=2)}

输出要求：
{SELECTION_CONTRACT}
"""

    return [
        {"role": "system", "content": SEARCH_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
