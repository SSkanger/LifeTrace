# LifeTrace LLM Backend

这个目录实现 demo 的第二步：把 `data` 里的清洗后数据输入大模型，并要求模型输出固定的前端页面 JSON。

## 文件说明

- `prompts.py`：大模型系统提示词、用户提示词和固定输出契约。
- `llm_client.py`：OpenAI-compatible `/chat/completions` HTTP 客户端，只使用 Python 标准库。
- `page_contract.py`：前端页面 JSON 的本地校验器，防止模型输出多字段、少字段或类型不稳定。
- `display_service.py`：只让大模型生成前端展示文案，事实、证据和跳转字段由后端规则合并。
- `mock_payload.py`：不调用大模型的确定性 mock 输出，方便前端先开发和联调。
- `memory_index.py`：把单日、周度和月度数据切成可搜索记忆条目，并写入 Chroma 向量库。
- `search_prompts.py`：模糊记忆搜索的“问题理解”和“候选选择”提示词。
- `search_contract.py`：搜索结果 JSON 的本地校验器。
- `search_service.py`：大模型理解问题、Chroma 检索、大模型选择候选的搜索服务。
- `generate_page_payload.py`：命令行入口。
- `generate_display_payload.py`：生成 `lifetrace.llmDisplay.v1` 文案输出的命令行入口。
- `search_memory.py`：模糊记忆搜索命令行入口。
- `server.py`：标准库 HTTP 服务，供前端 demo 直接请求。

## 输出契约

脚本输出的顶层结构固定为：

```json
{
  "schemaVersion": "lifetrace.page.v1",
  "pageType": "daily",
  "sourceKey": "2026-05-20",
  "title": "...",
  "subtitle": "...",
  "dataQualityNote": "...",
  "summary": {},
  "quickFacts": [],
  "timeline": [],
  "rankingSections": [],
  "insightCards": [],
  "memoryQuestions": [],
  "frontendHints": {}
}
```

单日页面会重点填充 `timeline`，周度/月度页面会重点填充 `rankingSections` 和 `insightCards`。前端可以先按这些稳定字段构造页面。

模糊记忆搜索输出的顶层结构固定为：

```json
{
  "schemaVersion": "lifetrace.search.v1",
  "query": "...",
  "interpretedQuery": {},
  "answer": {},
  "results": [],
  "relatedQuestions": [],
  "frontendHints": {}
}
```

搜索链路是：用户自然语言问题 -> 大模型生成检索计划 -> Chroma 向量检索候选记忆 -> 大模型选择候选 -> 后端组装固定 JSON。

## 展示文案输出

当前推荐的前端链路是：大模型只输出展示文案，后端规则补回日期、时间段、证据、来源和跳转字段。

```powershell
python backend\generate_display_payload.py --scope daily --mock
python backend\generate_display_payload.py --scope week --mock
```

默认输出到：

- `outputs/lifetrace_daily_display_payload.json`
- `outputs/lifetrace_week_display_payload.json`

真实调用大模型时去掉 `--mock`。前端最终仍建议读取 `/api/today-overview`、`/api/daily-review`、`/api/weekly-summary` 这些接口，因为它们已经把文案和事实字段合并好。

## 安装依赖

页面生成只使用 Python 标准库；模糊记忆搜索需要 Chroma：

```powershell
python -m pip install -r backend\requirements.txt
```

## 本地 mock 生成

```powershell
python backend\generate_page_payload.py --mode daily --mock
python backend\generate_page_payload.py --mode week --mock
python backend\generate_page_payload.py --mode month --mock
python backend\search_memory.py --query "我记得下午在图书馆整理 LifeTrace 项目" --mock --rebuild-index
```

默认输出到：

- `outputs/lifetrace_daily_page_payload.json`
- `outputs/lifetrace_week_page_payload.json`
- `outputs/lifetrace_month_page_payload.json`
- `outputs/lifetrace_search_payload.json`

## 查看最终提示词

```powershell
python backend\generate_page_payload.py --mode daily --print-prompt
python backend\generate_page_payload.py --mode week --print-prompt
python backend\generate_page_payload.py --mode month --print-prompt
```

## 调用真实大模型 API

默认支持 OpenAI-compatible 接口。先设置环境变量：

```powershell
$env:LIFETRACE_LLM_BASE_URL="https://api.openai.com/v1"
$env:LIFETRACE_LLM_API_KEY="你的 API Key"
$env:LIFETRACE_LLM_MODEL="你的模型名"
$env:LIFETRACE_EMBEDDING_BASE_URL="https://api.openai.com/v1"
$env:LIFETRACE_EMBEDDING_API_KEY="你的 embedding API Key"
$env:LIFETRACE_EMBEDDING_MODEL="你的 embedding 模型名"
```

`LIFETRACE_LLM_*` 用于每日回看、周度总结、搜索问题理解和候选排序；`LIFETRACE_EMBEDDING_*`
只用于模糊记忆搜索的向量召回。如果不设置 `LIFETRACE_EMBEDDING_BASE_URL` 和
`LIFETRACE_EMBEDDING_API_KEY`，后端会沿用 `LIFETRACE_LLM_BASE_URL` 和 `LIFETRACE_LLM_API_KEY`。

然后运行：

```powershell
python backend\generate_page_payload.py --mode daily
python backend\generate_page_payload.py --mode week
python backend\generate_page_payload.py --mode month
python backend\search_memory.py --query "我记得下午在图书馆整理 LifeTrace 项目"
```

如果只测试蓝心云端 API 的每日回看，可以使用 vivo 配置：

```powershell
$env:LIFETRACE_LLM_PROVIDER="vivo"
$env:LIFETRACE_VIVO_BASE_URL="https://api-ai.vivo.com.cn"
$env:LIFETRACE_VIVO_APP_ID="你的 vivo APP_ID"
$env:LIFETRACE_VIVO_APP_KEY="你的 vivo APP_KEY"
$env:LIFETRACE_VIVO_MODEL="vivo-BlueLM-TB-Pro"
```

然后运行：

```powershell
python backend\generate_page_payload.py --mode daily
```

蓝心云端 API 使用 vivo AI Gateway 签名鉴权，不使用 `Authorization: Bearer`。当前适配器会请求 `/vivogpt/completions`，并把模型返回内容解析为固定的 `lifetrace.page.v1` JSON。

如果模型服务不支持 `response_format: {"type": "json_object"}`，可以关闭 JSON mode：

```powershell
$env:LIFETRACE_LLM_JSON_MODE="false"
```

脚本会在写入文件前执行契约校验；如果大模型输出不符合前端结构，会直接报错，方便调整提示词或重试。

## 启动本地后端服务

前端开发阶段可以先用 mock 模式启动：

```powershell
python backend\server.py --port 8787 --mock-default
```

然后请求：

```text
GET http://127.0.0.1:8787/api/page-payload?mode=daily
GET http://127.0.0.1:8787/api/page-payload?mode=week
GET http://127.0.0.1:8787/api/page-payload?mode=month
GET http://127.0.0.1:8787/api/search-memory?query=我记得下午在图书馆整理LifeTrace项目
```

真实调用大模型时，先设置环境变量，再去掉 `--mock-default`。如果只想对某一次请求使用 mock，可以加查询参数：

```text
GET http://127.0.0.1:8787/api/page-payload?mode=daily&mock=1
GET http://127.0.0.1:8787/api/page-payload?mode=week&mock=1
GET http://127.0.0.1:8787/api/search-memory?query=我记得下午在图书馆整理LifeTrace项目&mock=1
```

也可以使用 `POST /api/page-payload` 或 `POST /api/search-memory`：

```json
{
  "mode": "daily",
  "mock": true,
  "data": {},
  "readGuide": {}
}
```

```json
{
  "query": "我记得下午在图书馆整理 LifeTrace 项目",
  "mock": true,
  "topK": 5,
  "rebuildIndex": false
}
```
