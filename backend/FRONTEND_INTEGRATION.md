# LifeTrace 后端与前端对接说明

本文档用于前端对接当前 LifeTrace 后端。后端主要负责把已清洗的数据转换成前端可直接渲染的页面 JSON，并提供模糊记忆搜索结果。

## 一、当前后端能力

当前后端有三类能力：

1. 日期回看页面生成
   - 输入：`data/lifetrace_daily_short_final.json`
   - 输出：`outputs/lifetrace_daily_page_payload.json`
   - 页面类型：`daily`

2. 阶段/月度总结页面生成
   - 周总结输入：`data/lifetrace_week_daily_data.json`
   - 周总结输出：`outputs/lifetrace_week_page_payload.json`
   - 周总结页面类型：`week`
   - 月总结输入：`data/lifetrace_month_summary_data.json`
   - 月总结输出：`outputs/lifetrace_month_page_payload.json`
   - 月总结页面类型：`month`

3. 模糊记忆搜索
   - 输入：用户自然语言问题
   - 输出：`outputs/lifetrace_search_payload.json`
   - 页面类型：搜索结果页

核心逻辑：

```text
清洗后的 LifeTrace 数据
  ↓
提示词组装
  ↓
大模型生成结构化 JSON
  ↓
后端做保守修正
  ↓
契约校验
  ↓
输出给前端
```

## 二、目录与关键文件

```text
backend/
  generate_page_payload.py   日期回看/阶段总结命令行入口
  search_memory.py           模糊记忆搜索命令行入口
  server.py                  HTTP API 服务
  service.py                 页面生成主逻辑
  llm_client.py              OpenAI-compatible 大模型客户端
  vivo_client.py             vivo BlueLM 客户端
  prompts.py                 页面生成提示词
  page_contract.py           页面 payload 校验契约
  search_service.py          模糊搜索主逻辑
  search_prompts.py          搜索提示词
  search_contract.py         搜索 payload 校验契约
  memory_index.py            Chroma 向量索引与记忆条目构建
  mock_payload.py            不调用大模型的 mock 页面生成

data/
  lifetrace_daily_short_final.json
  lifetrace_read_guide_final.json
  lifetrace_week_daily_data.json
  lifetrace_week_read_guide.json
  lifetrace_month_summary_data.json
  lifetrace_month_read_guide.json

outputs/
  lifetrace_daily_page_payload.json
  lifetrace_week_page_payload.json
  lifetrace_month_page_payload.json
  lifetrace_search_payload.json
  chroma_lifetrace/
```

## 三、环境变量配置

PowerShell 中建议在项目根目录运行：

```powershell
cd "E:\Desktop\设计思维课程\Lifetrace"
```

### 1. 使用 DeepSeek 生成日期回看/阶段总结

```powershell
$env:LIFETRACE_LLM_PROVIDER="openai"
$env:LIFETRACE_LLM_BASE_URL="https://api.deepseek.com"
$env:LIFETRACE_LLM_API_KEY="你的 DeepSeek API Key"
$env:LIFETRACE_LLM_MODEL="deepseek-v4-flash"
$env:LIFETRACE_LLM_JSON_MODE="true"
$env:LIFETRACE_LLM_MAX_TOKENS="8000"
```

说明：

- 当前通用客户端使用 OpenAI-compatible 协议。
- DeepSeek 可用于日期回看、阶段总结、搜索候选结果总结。
- DeepSeek 当前不能作为 embedding 模型直接用于向量搜索。

### 2. 使用其他 OpenAI-compatible 网关

如果某个服务同时支持 `/chat/completions` 和 `/embeddings`，可以这样配置：

```powershell
$env:LIFETRACE_LLM_PROVIDER="openai"
$env:LIFETRACE_LLM_BASE_URL="https://你的服务地址/v1"
$env:LIFETRACE_LLM_API_KEY="你的 API Key"
$env:LIFETRACE_LLM_MODEL="聊天模型名"
$env:LIFETRACE_EMBEDDING_MODEL="embedding 模型名"
$env:LIFETRACE_LLM_JSON_MODE="true"
$env:LIFETRACE_LLM_MAX_TOKENS="8000"
```

注意：当前代码里 chat 和 embedding 共用同一个 `LIFETRACE_LLM_BASE_URL` 与 `LIFETRACE_LLM_API_KEY`。如果要“DeepSeek 做总结，另一个服务做 embedding”，需要后续把 embedding client 单独拆出来。

## 四、运行后端脚本

### 1. 日期回看

真实调用大模型：

```powershell
python backend\generate_page_payload.py --mode daily
```

更稳定的低温参数：

```powershell
python backend\generate_page_payload.py --mode daily --max-tokens 8000 --temperature 0
```

不调用大模型，使用本地 mock：

```powershell
python backend\generate_page_payload.py --mode daily --mock
```

默认输出：

```text
outputs/lifetrace_daily_page_payload.json
```

### 2. 阶段/周度总结

真实调用大模型：

```powershell
python backend\generate_page_payload.py --mode week
```

更稳定的低温参数：

```powershell
python backend\generate_page_payload.py --mode week --max-tokens 8000 --temperature 0
```

不调用大模型，使用本地 mock：

```powershell
python backend\generate_page_payload.py --mode week --mock
```

默认输出：

```text
outputs/lifetrace_week_page_payload.json
```

如果仍要生成月度总结，可以继续运行：

```powershell
python backend\generate_page_payload.py --mode month
```

### 3. 查看最终提示词

用于调试模型输入：

```powershell
python backend\generate_page_payload.py --mode daily --print-prompt
python backend\generate_page_payload.py --mode week --print-prompt
python backend\generate_page_payload.py --mode month --print-prompt
```

### 4. 模糊记忆搜索

mock 搜索，不调用大模型和真实 embedding：

```powershell
python backend\search_memory.py --query "我记得下午在图书馆整理 LifeTrace 项目" --mock --rebuild-index
```

真实搜索：

```powershell
python backend\search_memory.py --query "我记得下午在图书馆整理 LifeTrace 项目" --rebuild-index
```

常用参数：

```powershell
python backend\search_memory.py `
  --query "我上次拍晚霞是哪天" `
  --top-k 5 `
  --candidate-k 16 `
  --rebuild-index
```

默认输出：

```text
outputs/lifetrace_search_payload.json
```

注意：

- `--rebuild-index` 会重建 Chroma 向量索引。
- 修改 embedding 模型后，应重新加 `--rebuild-index`。
- DeepSeek 不能直接提供 `/embeddings`，所以真实语义搜索需要额外 embedding 服务。

## 五、启动 HTTP 服务

启动服务：

```powershell
python backend\server.py --port 8787
```

启动 mock 默认模式：

```powershell
python backend\server.py --port 8787 --mock-default
```

健康检查：

```text
GET http://127.0.0.1:8787/health
```

返回：

```json
{
  "ok": true
}
```

## 六、HTTP API

### 1. 获取日期回看或阶段总结

```text
GET /api/page-payload?mode=daily
GET /api/page-payload?mode=week
GET /api/page-payload?mode=month
```

mock：

```text
GET /api/page-payload?mode=daily&mock=1
GET /api/page-payload?mode=week&mock=1
GET /api/page-payload?mode=month&mock=1
```

POST：

```http
POST /api/page-payload
Content-Type: application/json
```

请求体：

```json
{
  "mode": "daily",
  "mock": false,
  "temperature": 0,
  "maxTokens": 8000,
  "timeout": 90
}
```

也可以传入自定义数据：

```json
{
  "mode": "daily",
  "mock": false,
  "data": {},
  "readGuide": {}
}
```

成功返回：

```json
{
  "ok": true,
  "data": {}
}
```

失败返回：

```json
{
  "ok": false,
  "error": "错误信息"
}
```

### 2. 模糊记忆搜索

```text
GET /api/search-memory?query=我记得下午在图书馆整理项目
```

mock：

```text
GET /api/search-memory?query=我记得下午在图书馆整理项目&mock=1
```

POST：

```http
POST /api/search-memory
Content-Type: application/json
```

请求体：

```json
{
  "query": "我记得下午在图书馆整理项目",
  "mock": false,
  "topK": 5,
  "candidateK": 16,
  "rebuildIndex": false,
  "timeout": 90
}
```

成功返回：

```json
{
  "ok": true,
  "data": {}
}
```

## 七、页面 payload 结构

日期回看和阶段总结共用 `lifetrace.page.v1` 结构。

顶层字段：

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

### 1. `summary`

页面核心摘要：

```json
{
  "headline": "学习、项目与晚霞",
  "paragraph": "自然语言总结",
  "tags": ["课程学习", "项目整理"]
}
```

前端建议：可用于页面顶部概览区。

### 2. `quickFacts`

关键事实卡片：

```json
{
  "id": "main_location",
  "label": "主要地点",
  "value": "图书馆附近",
  "description": "一句解释"
}
```

前端建议：用 2 到 6 张小卡片展示。

### 3. `timeline`

日期回看的时间线。`daily` 必须有，`month` 必须为空数组。

```json
{
  "id": "seg_project_work",
  "timeRange": "13:37-17:05",
  "title": "下午在图书馆整理项目资料",
  "category": "project_work",
  "description": "片段说明",
  "evidence": ["证据 1", "证据 2"],
  "sourceTypes": ["location", "app_usage", "photo"],
  "display": {
    "icon": "laptop",
    "tone": "violet"
  }
}
```

前端建议：

- `id` 可作为锚点。
- `display.icon` 对应图标。
- `display.tone` 对应卡片色彩。
- `evidence` 建议折叠展示或作为详情。

### 4. `rankingSections`

排行区：

```json
{
  "id": "app_usage",
  "title": "App 使用时长排行",
  "unit": "minutes",
  "items": [
    {
      "rank": 1,
      "label": "哔哩哔哩",
      "value": "58 分钟",
      "description": "晚间娱乐放松"
    }
  ]
}
```

前端建议：适合表格、排行榜、横向条形图。

### 5. `insightCards`

洞察卡片：

```json
{
  "id": "main_thread",
  "title": "今天的主线",
  "description": "洞察说明",
  "evidence": ["依据 1", "依据 2"],
  "type": "highlight"
}
```

`type` 可能是：

```text
highlight
pattern
suggestion
```

### 6. `memoryQuestions`

适合用户回顾的问题：

```json
[
  "今天下午最专注的片段是什么？",
  "傍晚的校园晚霞让你想起了什么？"
]
```

### 7. `frontendHints`

前端展示建议：

```json
{
  "defaultView": "timeline",
  "accent": "blue",
  "density": "comfortable"
}
```

`daily` 的 `defaultView` 固定为 `timeline`。  
`month` 的 `defaultView` 固定为 `overview`。

## 八、搜索 payload 结构

模糊搜索输出结构为 `lifetrace.search.v1`：

```json
{
  "schemaVersion": "lifetrace.search.v1",
  "query": "我记得下午在图书馆整理项目",
  "interpretedQuery": {},
  "answer": {},
  "results": [],
  "relatedQuestions": [],
  "frontendHints": {}
}
```

### 1. `interpretedQuery`

后端或大模型理解后的检索计划：

```json
{
  "searchText": "图书馆 LifeTrace 项目整理",
  "intent": "find_memory",
  "timeHints": ["下午"],
  "locationHints": ["图书馆"],
  "appHints": ["WPS"],
  "activityHints": ["项目整理"],
  "visualHints": [],
  "keywords": ["LifeTrace", "项目"]
}
```

### 2. `answer`

搜索结果摘要：

```json
{
  "headline": "最可能是 2026-05-20 的项目整理片段",
  "paragraph": "自然语言解释为什么匹配"
}
```

### 3. `results`

最终搜索结果：

```json
{
  "id": "daily_2026_05_20_seg_4",
  "score": 0.82,
  "confidence": "high",
  "sourceType": "daily_segment",
  "sourceKey": "2026-05-20",
  "timeRange": "13:37-17:05",
  "title": "下午在图书馆整理项目资料",
  "snippet": "简短摘要",
  "evidence": ["证据 1"],
  "matchReason": "为什么匹配",
  "openTarget": {
    "pageType": "daily",
    "sourceKey": "2026-05-20",
    "anchorId": "seg_4"
  }
}
```

前端建议：

- 点击搜索结果时，根据 `openTarget.pageType` 和 `openTarget.sourceKey` 打开对应页面。
- 如果是 `daily`，可滚动到 `openTarget.anchorId` 对应的时间线片段。
- `score` 可用于排序展示，但不建议直接暴露成百分比。
- `confidence` 可展示为“高/中/低匹配度”。

## 九、当前模型与搜索限制

### 1. DeepSeek 的定位

DeepSeek 当前适合：

```text
日期回看总结
阶段总结
理解搜索问题
从候选记忆中选择结果并解释
```

DeepSeek 当前不适合：

```text
直接作为 embedding 模型
直接提供向量搜索
```

### 2. 真实模糊搜索还需要 embedding

真实语义搜索需要：

```text
embedding 模型：把文本转成向量
Chroma：存储和检索向量
DeepSeek 或其他 LLM：理解和总结
```

推荐 embedding 模型：

```text
BAAI/bge-m3
text-embedding-3-small
```

当前如果没有 embedding 服务，可以先用：

```powershell
python backend\search_memory.py --query "我记得下午在图书馆整理项目" --mock --rebuild-index
```

## 十、前端对接建议

1. 前端优先对接 HTTP API，而不是直接读 `outputs/*.json`。
2. 页面生成接口返回的是 `{ ok, data }`，前端渲染使用 `data`。
3. `pageType + sourceKey` 可以作为页面唯一标识。
4. `timeline[].id` 和搜索结果里的 `openTarget.anchorId` 可以做锚点跳转。
5. 展示时不要假设所有数组都有固定长度，只按契约允许范围自适应。
6. 搜索 mock 和真实搜索返回结构一致，前端可以先用 mock 开发。
7. 如果接口返回 `ok=false`，直接展示 `error`，方便调试。
8. 数值型事实建议未来由后端确定性计算，模型主要负责表达和总结。

## 十一、常见命令速查

```powershell
# 只生成大模型展示文案，不包含事实/跳转字段
python backend\generate_display_payload.py --scope daily
python backend\generate_display_payload.py --scope week

# 日期回看
python backend\generate_page_payload.py --mode daily

# 周度阶段总结
python backend\generate_page_payload.py --mode week

# 月度总结
python backend\generate_page_payload.py --mode month

# 日期回看 mock
python backend\generate_page_payload.py --mode daily --mock

# 周度阶段总结 mock
python backend\generate_page_payload.py --mode week --mock

# 月度总结 mock
python backend\generate_page_payload.py --mode month --mock

# 模糊搜索 mock
python backend\search_memory.py --query "我记得下午在图书馆整理项目" --mock --rebuild-index

# 启动 HTTP 服务
python backend\server.py --port 8787

# 启动 HTTP 服务，默认 mock
python backend\server.py --port 8787 --mock-default
```

## 十二、当前建议的前端开发顺序

1. 先用 `--mock-default` 启动后端，完成页面结构渲染。
2. 对接 `GET /api/page-payload?mode=daily`。
3. 对接 `GET /api/page-payload?mode=week` 或 `/api/weekly-summary?mock=1`。
4. 对接 `GET /api/search-memory?query=...&mock=1`。
5. 后端 embedding 服务确定后，再切换到真实搜索。
6. 最后处理 loading、error、empty state 和锚点跳转。

## 十三、当前前端页面专用接口

`frontend-data-requirements.md` 和当前 WebView 前端更接近下面这些轻量接口。它们由 `backend/frontend_adapter.py` 从严格的 `page.v1/search.v1` payload 转成前端卡片字段，适合直接替换 `LifeTraceRepository.java` 里的硬编码 JSON。

当前采用的生成边界是：

```text
大模型输出 lifetrace.llmDisplay.v1：只包含标题、摘要、描述、标签、回看建议等展示文案。
后端规则合并事实字段：date、timeRange、evidence、sourceTypes、hasData、clueCount、targetDate、targetPage。
前端读取最终接口：/api/today-overview、/api/daily-review、/api/weekly-summary 等。
```

因此前端不要直接用 `lifetrace_daily_display_payload.json` 渲染完整页面；它只是模型文案层。前端直接可用的是下面这些接口或由这些接口导出的静态 JSON。

```text
GET /api/today-overview?mock=1
GET /api/calendar-month?year=2026&month=5
GET /api/daily-review?date=2026-05-20&mock=1
GET /api/search-guide
GET /api/search-memories?query=图书馆 LifeTrace 项目&mock=1
GET /api/weekly-summary?offset=0&mock=1
GET /api/monthly-summary?year=2026&month=5&mock=1
```

这些接口也支持 POST，body 使用同名参数，例如：

```json
{
  "query": "图书馆 LifeTrace 项目",
  "mock": true,
  "topK": 5
}
```

返回格式统一为：

```json
{
  "ok": true,
  "data": {}
}
```

前端字段对应关系：

| 前端方法 | 后端接口 | 主要返回字段 |
|---|---|---|
| `getTodayOverview()` | `/api/today-overview` | `title`, `text`, `tags`, `homeTodaySummary` |
| `getCalendarMonth(year, month)` | `/api/calendar-month` | `memoryDays`, `daySummaries` |
| `getDailyReview(date)` | `/api/daily-review` | `selectedDaySummary`, `dailyOverview`, `events`, `timeline` |
| `searchMemories(query)` | `/api/search-memories` | `searchResults` |
| 搜索打开前推荐 | `/api/search-guide` | `searchGuide.suggestedQueries`, `searchGuide.discoveryEntries` |
| `getWeeklySummary(offset)` | `/api/weekly-summary` | `weeklySummary` |
| `getMonthlySummary(year, month)` | `/api/monthly-summary` | `monthlySummary`, `recommendedMemories` |

注意：前端专用接口不会把 `memoryQuestions`、`relatedQuestions`、独立 AI 回答卡片作为必需字段返回，因为当前页面没有对应展示位置。

## 十四、搜索索引配置

Chroma 向量库默认写入：

```text
outputs/chroma_lifetrace
```

如果本机这个目录出现只读、锁定或权限异常，可以换一个新目录：

```powershell
$env:LIFETRACE_CHROMA_PATH="outputs/chroma_lifetrace_dev"
python backend\search_memory.py --query "图书馆 LifeTrace 项目" --mock --rebuild-index
```

`/api/search-memories?mock=1` 在 Chroma 不可写时会返回一个基于结构化记忆片段的兜底结果，保证前端 demo 不会因为本地索引目录问题直接空白。
