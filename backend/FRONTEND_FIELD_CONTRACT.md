# LifeTrace 前后端字段契约对齐表

本文档根据当前后端输出、现有前端 `LifeTrace_recovered_from_browser.html` 的静态渲染逻辑，以及后续真实 API 对接需求整理。目的不是马上改 schema，而是先把“前端需要什么字段、后端现在给什么字段、哪里需要适配”说清楚。

## 一、当前结论

当前后端已有两个正式契约：

```text
lifetrace.page.v1
lifetrace.search.v1
```

暂时不建议直接改成 `lifetrace.page.v2` / `lifetrace.search.v2`。原因是当前 `v1` 已经能覆盖日期回看、阶段总结和搜索结果页的大部分需求；真正缺的是前端从静态 mock 切到 API 渲染时的字段映射。

如果后续确认前端必须使用更扁平的字段，例如 `dailySummary`、`dailyAbstract`、`recommendedQuestions`，再做 `v2` 或后端 adapter 会更稳。

## 二、现有前端状态

当前前端主要还是静态数据：

| 页面 | 当前前端数据来源 | 关键位置 | 当前问题 |
|---|---|---|---|
| 日期回看 | JS 内置 `events` 数组 | `renderTimeline()` | 未调用 `/api/page-payload?mode=daily` |
| 搜索结果 | `renderResults()` 写死 HTML | `submitSearch()` -> `renderResults()` | 未调用 `/api/search-memory` |
| 月度总结 | JS 内置 `monthlyCopy` | `renderMonthlySummary()` | 未调用 `/api/page-payload?mode=month` |
| 周度总结 | JS 内置 `weeklyCopy` | `renderWeeklySummary()` | 后端当前还没有 week 模式 |
| 空状态/错误状态 | 静态页面 | state pages | 需要接 API loading/error/empty |

## 三、后端页面契约：`lifetrace.page.v1`

后端页面 payload 顶层结构：

```json
{
  "schemaVersion": "lifetrace.page.v1",
  "pageType": "daily",
  "sourceKey": "2026-05-20",
  "title": "",
  "subtitle": "",
  "dataQualityNote": "",
  "summary": {},
  "quickFacts": [],
  "timeline": [],
  "rankingSections": [],
  "insightCards": [],
  "memoryQuestions": [],
  "frontendHints": {}
}
```

### 1. 页面头部

| 前端展示位置 | 当前前端静态文案 | 后端字段 | 类型 | 必填 | 说明 |
|---|---|---|---|---|---|
| 页面标题 | `日期回看` / 日期文本 | `title` | string | 是 | 大模型生成的页面标题 |
| 页面副标题 | 静态说明 | `subtitle` | string | 是 | 可放在标题下方 |
| 日期/月标识 | 日历选中日期 | `sourceKey` | string | 是 | daily 为 `yyyy-MM-dd`，month 为 `yyyy-MM` |
| 数据质量提示 | 线索较少提示 | `dataQualityNote` | string | 是 | 可用于弱提示、角标、空状态说明 |
| 默认视图 | 无 | `frontendHints.defaultView` | string | 是 | daily 固定 `timeline`，month 固定 `overview` |
| 主色调 | 静态 CSS | `frontendHints.accent` | string | 是 | 可映射到主题色 |

### 2. 摘要区

| 前端需要 | 后端字段 | 类型 | 必填 | 示例 | 渲染建议 |
|---|---|---|---|---|---|
| 摘要标题 | `summary.headline` | string | 是 | `学习、项目与晚霞` | 作为摘要卡片标题 |
| 摘要正文 | `summary.paragraph` | string | 是 | `这一天以课程学习...` | 作为主要说明文 |
| 标签 | `summary.tags` | string[] | 是 | `["课程学习", "项目整理"]` | 渲染为 chip |

如果前端想使用截图中的字段：

| 扁平字段 | 当前后端映射 |
|---|---|
| `dailySummary` | `summary.headline` |
| `dailyAbstract` | `summary.paragraph` |
| `keywords` | `summary.tags` |

### 3. 日期回看时间线

`pageType=daily` 时使用 `timeline`。`pageType=month` 时 `timeline` 固定为空数组。

| 前端需要 | 后端字段 | 类型 | 必填 | 当前前端静态字段 | 说明 |
|---|---|---|---|---|---|
| 片段 id | `timeline[].id` | string | 是 | 无 | 可作为锚点 |
| 时间 | `timeline[].timeRange` | string | 是 | `events[].time` | 当前后端给时间段，不只是单点时间 |
| 标题 | `timeline[].title` | string | 是 | `events[].title` | 直接渲染 |
| 描述 | `timeline[].description` | string | 是 | `events[].text` | 直接渲染 |
| 分类 | `timeline[].category` | string | 是 | `events[].type` | 可做图标/样式映射 |
| 标签/来源 | `timeline[].sourceTypes` | string[] | 是 | `events[].tags` | 当前语义不同，前端可优先用 evidence 或 category 补展示 |
| 证据 | `timeline[].evidence` | string[] | 是 | 无 | 建议折叠到详情或作为小字 |
| 图标 | `timeline[].display.icon` | string | 是 | 静态 icon | 可映射 lucide/iconfont |
| 颜色 | `timeline[].display.tone` | string | 是 | 静态 class | 可映射 CSS class |

当前前端 `events[].photo` 在后端 `timeline` 中没有独立字段。可选方案：

1. 前端根据 `sourceTypes` 包含 `photo` 时展示照片占位卡。
2. 后端未来增加 `media` 字段，需要升级到 `page.v2`。
3. 前端进入详情时再根据原始数据或图片资源加载照片。

### 4. 关键事实卡片

| 前端需要 | 后端字段 | 类型 | 必填 | 说明 |
|---|---|---|---|---|
| 卡片 id | `quickFacts[].id` | string | 是 | 稳定 key |
| 标签 | `quickFacts[].label` | string | 是 | 如 `主要地点` |
| 值 | `quickFacts[].value` | string | 是 | 如 `图书馆附近` |
| 说明 | `quickFacts[].description` | string | 是 | 一句话解释 |

前端可用于日期摘要卡、顶部概览、月度数据概览。

注意：涉及“最长、最多、合计”等数值判断，建议未来由后端确定性计算后再给模型润色，避免模型算错。

### 5. 排行区

| 前端需要 | 后端字段 | 类型 | 必填 | 说明 |
|---|---|---|---|---|
| 排行组 id | `rankingSections[].id` | string | 是 | 如 `app_usage` |
| 排行标题 | `rankingSections[].title` | string | 是 | 如 `App 使用时长排行` |
| 单位 | `rankingSections[].unit` | string | 是 | `minutes/count/mixed` |
| 排名 | `items[].rank` | number | 是 | 从 1 开始 |
| 名称 | `items[].label` | string | 是 | 地点、App、活动名 |
| 数值 | `items[].value` | string | 是 | 含单位的展示值 |
| 描述 | `items[].description` | string | 是 | 一句话解释 |

可映射到截图里的：

| 扁平字段 | 当前后端映射 |
|---|---|
| `rankings` | `rankingSections` |
| `rankings.locations` | `rankingSections` 中地点相关 section |
| `rankings.apps` | `rankingSections` 中 App 相关 section |

### 6. 洞察卡片

| 前端需要 | 后端字段 | 类型 | 必填 | 说明 |
|---|---|---|---|---|
| 洞察 id | `insightCards[].id` | string | 是 | 稳定 key |
| 标题 | `insightCards[].title` | string | 是 | 洞察标题 |
| 描述 | `insightCards[].description` | string | 是 | 洞察正文 |
| 证据 | `insightCards[].evidence` | string[] | 是 | 1 到 5 条 |
| 类型 | `insightCards[].type` | string | 是 | `highlight/pattern/suggestion` |

可映射到截图中的 `insights`。

### 7. 推荐问题

| 前端需要 | 后端字段 | 类型 | 必填 | 说明 |
|---|---|---|---|---|
| 推荐问题 | `memoryQuestions` | string[] | 是 | 2 到 4 个 |

如果前端想使用截图中的字段：

| 扁平字段 | 当前后端映射 |
|---|---|
| `recommendedQuestions` | `memoryQuestions` |

## 四、搜索契约：`lifetrace.search.v1`

搜索 payload 顶层结构：

```json
{
  "schemaVersion": "lifetrace.search.v1",
  "query": "",
  "interpretedQuery": {},
  "answer": {},
  "results": [],
  "relatedQuestions": [],
  "frontendHints": {}
}
```

### 1. 搜索问题理解

| 前端需要 | 后端字段 | 类型 | 必填 | 说明 |
|---|---|---|---|---|
| 原始问题 | `query` | string | 是 | 用户输入 |
| AI 理解文本 | `interpretedQuery.searchText` | string | 是 | 可不展示，也可作为调试信息 |
| 意图 | `interpretedQuery.intent` | string | 是 | `find_memory/find_day/find_pattern/open_summary` |
| 时间线索 | `interpretedQuery.timeHints` | string[] | 是 | 可显示为 chip |
| 地点线索 | `interpretedQuery.locationHints` | string[] | 是 | 可显示为 chip |
| App 线索 | `interpretedQuery.appHints` | string[] | 是 | 可显示为 chip |
| 活动线索 | `interpretedQuery.activityHints` | string[] | 是 | 可显示为 chip |
| 视觉线索 | `interpretedQuery.visualHints` | string[] | 是 | 可显示为 chip |
| 关键词 | `interpretedQuery.keywords` | string[] | 是 | 可显示为 chip |

如果前端想使用截图中的字段：

| 扁平字段 | 当前后端映射 |
|---|---|
| `aiAnswer` | `answer` |
| `relatedQuestions` | `relatedQuestions` |

### 2. 搜索回答

| 前端需要 | 后端字段 | 类型 | 必填 | 说明 |
|---|---|---|---|---|
| 回答标题 | `answer.headline` | string | 是 | 搜索结论 |
| 回答正文 | `answer.paragraph` | string | 是 | 解释为什么匹配 |

### 3. 搜索结果列表

| 前端需要 | 后端字段 | 类型 | 必填 | 说明 |
|---|---|---|---|---|
| 结果 id | `results[].id` | string | 是 | 稳定 key |
| 匹配分 | `results[].score` | number | 是 | 仅建议内部排序，不建议直接显示为百分比 |
| 置信度 | `results[].confidence` | string | 是 | `high/medium/low` |
| 来源类型 | `results[].sourceType` | string | 是 | daily/month/app/location/photo 等 |
| 来源日期/月 | `results[].sourceKey` | string | 是 | `yyyy-MM-dd` 或 `yyyy-MM` |
| 时间段 | `results[].timeRange` | string | 是 | 结果对应时间 |
| 标题 | `results[].title` | string | 是 | 卡片标题 |
| 摘要 | `results[].snippet` | string | 是 | 卡片正文 |
| 证据 | `results[].evidence` | string[] | 是 | 可折叠展示 |
| 匹配原因 | `results[].matchReason` | string | 是 | 解释为什么命中 |
| 跳转目标 | `results[].openTarget` | object | 是 | 点击结果后跳转 |

`openTarget`：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `pageType` | string | 是 | `daily` 或 `month` |
| `sourceKey` | string | 是 | 目标日期/月 |
| `anchorId` | string | 是 | 页面内部锚点 |

## 五、月度总结字段对齐

当前前端 `monthlyCopy` 使用的是：

```text
meta
title
overview
rhythm
places
review
tags
```

当前后端 `page.v1` 可这样映射：

| 当前前端字段 | 后端字段 | 说明 |
|---|---|---|
| `meta` | `sourceKey` 或格式化后的 `sourceKey` | 如 `2026 年 05 月` |
| `title` | `title` | 月度标题 |
| `overview` | `summary.paragraph` | 月度总述 |
| `tags` | `summary.tags` | 标签 |
| `rhythm` | `insightCards` 中 `type=pattern` 的描述 | 生活节奏 |
| `places` | `rankingSections` 中地点排行 | 常出现地点 |
| `review` | `memoryQuestions` 或 `insightCards` 中建议类卡片 | 继续回看建议 |
| 推荐日期 | 当前后端暂无专门字段 | 可从 `rankingSections`/`insightCards` 推导，或后续加 `recommendedDays` |

如前端强依赖 `recommendedDays`，建议后续升级为 `page.v2`，新增：

```json
{
  "recommendedDays": [
    {
      "date": "2026-05-20",
      "title": "图书馆项目整理",
      "reason": "时间线和证据较完整"
    }
  ]
}
```

## 六、建议前端先实现的 Adapter

前端可以先不要求后端改字段，而是写一层 adapter，把后端 `v1` 转成页面更顺手的 view model。

### 1. 日期回看 adapter

```js
function adaptDailyPage(payload) {
  return {
    date: payload.sourceKey,
    dailySummary: payload.summary.headline,
    dailyAbstract: payload.summary.paragraph,
    keywords: payload.summary.tags,
    quickFacts: payload.quickFacts,
    timeline: payload.timeline.map(item => ({
      id: item.id,
      time: item.timeRange,
      title: item.title,
      text: item.description,
      tags: [...item.sourceTypes, item.category],
      evidence: item.evidence,
      icon: item.display.icon,
      tone: item.display.tone
    })),
    recommendedQuestions: payload.memoryQuestions,
    dataQualityNote: payload.dataQualityNote
  };
}
```

### 2. 月度总结 adapter

```js
function adaptMonthPage(payload) {
  const locationRanking = payload.rankingSections.find(section =>
    section.id.includes('location') || section.title.includes('地点')
  );
  const patternInsight = payload.insightCards.find(card => card.type === 'pattern');

  return {
    month: payload.sourceKey,
    monthSummary: payload.summary.paragraph,
    keywords: payload.summary.tags,
    rankings: payload.rankingSections,
    insights: payload.insightCards,
    rhythm: patternInsight?.description || '',
    places: locationRanking?.items?.map(item => item.label).join('、') || '',
    recommendedQuestions: payload.memoryQuestions
  };
}
```

### 3. 搜索 adapter

```js
function adaptSearchPayload(payload) {
  return {
    query: payload.query,
    aiAnswer: payload.answer,
    results: payload.results.map(item => ({
      id: item.id,
      title: item.title,
      text: item.snippet,
      score: item.score,
      confidence: item.confidence,
      timeRange: item.timeRange,
      sourceKey: item.sourceKey,
      evidence: item.evidence,
      matchReason: item.matchReason,
      openTarget: item.openTarget
    })),
    relatedQuestions: payload.relatedQuestions
  };
}
```

## 七、是否需要升级到 v2

只有出现以下情况时，建议升级 schema：

1. 前端明确不想写 adapter，要求后端直接输出 `dailySummary/monthSummary/aiAnswer` 等扁平字段。
2. 前端需要独立媒体字段，如照片缩略图、图片路径、OCR 高亮。
3. 月度总结需要固定 `recommendedDays`。
4. 周度总结也要接入后端，当前后端只有 `daily/month`。
5. 搜索结果需要更复杂的来源展示，例如按时间、地点、照片、日程分组。

如果升级，建议命名：

```text
lifetrace.page.v2
lifetrace.search.v2
```

升级时需要同步改：

| 模块 | 文件 |
|---|---|
| 页面提示词 | `backend/prompts.py` |
| 页面校验 | `backend/page_contract.py` |
| 页面 mock | `backend/mock_payload.py` |
| 搜索提示词 | `backend/search_prompts.py` |
| 搜索校验 | `backend/search_contract.py` |
| 搜索组装 | `backend/search_service.py` |
| 前端渲染 | `LifeTrace_recovered_from_browser.html` 或正式前端工程 |
| 对接文档 | `backend/FRONTEND_INTEGRATION.md` |

## 八、下一步建议

最稳顺序：

1. 前端先按本文档写 adapter，消费当前 `lifetrace.page.v1/search.v1`。
2. 后端保留当前契约，继续保证 mock 和真实 API 返回结构一致。
3. 搜索先用 `mock=1` 对接 UI。
4. 确认 embedding 服务后，再切真实搜索。
5. 如果前端接入后发现字段确实不顺手，再统一升级到 `v2`。

