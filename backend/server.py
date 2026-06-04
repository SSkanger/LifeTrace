"""Tiny HTTP API for LifeTrace frontend demos."""

from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from frontend_adapter import (
    get_calendar_month,
    get_daily_review,
    get_monthly_summary,
    get_search_guide,
    get_today_overview,
    get_weekly_summary,
    search_memories_for_frontend,
)
from llm_client import DEFAULT_MAX_TOKENS
from service import generate_page_payload
from search_service import search_memory


DEFAULT_MOCK = False


class LifeTraceRequestHandler(BaseHTTPRequestHandler):
    server_version = "LifeTraceLLMBackend/0.1"

    def do_OPTIONS(self) -> None:
        self._send_empty(HTTPStatus.NO_CONTENT)

    def do_GET(self) -> None:
        parsed_url = urlparse(self.path)
        if parsed_url.path == "/health":
            self._send_json(HTTPStatus.OK, {"ok": True})
            return

        if parsed_url.path == "/api/page-payload":
            query = parse_qs(parsed_url.query)
            mode = _first(query.get("mode"), "daily")
            mock = _parse_bool(_first(query.get("mock"), str(DEFAULT_MOCK)))
            self._handle_generate({"mode": mode, "mock": mock})
            return

        if parsed_url.path == "/api/today-overview":
            query = parse_qs(parsed_url.query)
            mock = _parse_bool(_first(query.get("mock"), str(DEFAULT_MOCK)))
            self._handle_frontend_today({"mock": mock})
            return

        if parsed_url.path == "/api/calendar-month":
            query = parse_qs(parsed_url.query)
            self._handle_frontend_calendar(
                {
                    "year": _first(query.get("year"), "2026"),
                    "month": _first(query.get("month"), "5"),
                }
            )
            return

        if parsed_url.path == "/api/daily-review":
            query = parse_qs(parsed_url.query)
            mock = _parse_bool(_first(query.get("mock"), str(DEFAULT_MOCK)))
            self._handle_frontend_daily_review(
                {
                    "date": _first(query.get("date"), ""),
                    "mock": mock,
                }
            )
            return

        if parsed_url.path == "/api/search-guide":
            self._handle_frontend_search_guide()
            return

        if parsed_url.path == "/api/search-memories":
            query = parse_qs(parsed_url.query)
            search_query = _first(query.get("query"), _first(query.get("q"), ""))
            mock = _parse_bool(_first(query.get("mock"), str(DEFAULT_MOCK)))
            top_k = _first(query.get("topK"), "5")
            self._handle_frontend_search({"query": search_query, "mock": mock, "topK": top_k})
            return

        if parsed_url.path == "/api/weekly-summary":
            query = parse_qs(parsed_url.query)
            mock = _parse_bool(_first(query.get("mock"), str(DEFAULT_MOCK)))
            self._handle_frontend_weekly(
                {
                    "offset": _first(query.get("offset"), "0"),
                    "mock": mock,
                }
            )
            return

        if parsed_url.path == "/api/monthly-summary":
            query = parse_qs(parsed_url.query)
            mock = _parse_bool(_first(query.get("mock"), str(DEFAULT_MOCK)))
            self._handle_frontend_monthly(
                {
                    "year": _first(query.get("year"), "2026"),
                    "month": _first(query.get("month"), "5"),
                    "mock": mock,
                }
            )
            return

        if parsed_url.path == "/api/search-memory":
            query = parse_qs(parsed_url.query)
            search_query = _first(query.get("query"), _first(query.get("q"), ""))
            mock = _parse_bool(_first(query.get("mock"), str(DEFAULT_MOCK)))
            top_k = _first(query.get("topK"), "5")
            self._handle_search({"query": search_query, "mock": mock, "topK": top_k})
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Not found"})

    def do_POST(self) -> None:
        parsed_url = urlparse(self.path)
        if parsed_url.path not in {
            "/api/page-payload",
            "/api/search-memory",
            "/api/today-overview",
            "/api/calendar-month",
            "/api/daily-review",
            "/api/search-guide",
            "/api/search-memories",
            "/api/weekly-summary",
            "/api/monthly-summary",
        }:
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Not found"})
            return

        try:
            request_body = self._read_json_body()
        except ValueError as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
            return

        if parsed_url.path == "/api/page-payload":
            self._handle_generate(request_body)
        elif parsed_url.path == "/api/search-memory":
            self._handle_search(request_body)
        elif parsed_url.path == "/api/today-overview":
            self._handle_frontend_today(request_body)
        elif parsed_url.path == "/api/calendar-month":
            self._handle_frontend_calendar(request_body)
        elif parsed_url.path == "/api/daily-review":
            self._handle_frontend_daily_review(request_body)
        elif parsed_url.path == "/api/search-guide":
            self._handle_frontend_search_guide()
        elif parsed_url.path == "/api/search-memories":
            self._handle_frontend_search(request_body)
        elif parsed_url.path == "/api/weekly-summary":
            self._handle_frontend_weekly(request_body)
        elif parsed_url.path == "/api/monthly-summary":
            self._handle_frontend_monthly(request_body)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"{self.address_string()} - {format % args}")

    def _handle_generate(self, request_body: dict[str, Any]) -> None:
        try:
            mode = request_body.get("mode", "daily")
            mock = _coerce_bool(request_body.get("mock", DEFAULT_MOCK))
            payload = generate_page_payload(
                mode=mode,
                data=request_body.get("data"),
                read_guide=request_body.get("readGuide"),
                mock=mock,
                temperature=float(request_body.get("temperature", 0.2)),
                max_tokens=int(request_body.get("maxTokens", DEFAULT_MAX_TOKENS)),
                timeout=int(request_body.get("timeout", 90)),
            )
        except Exception as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
            return

        self._send_json(HTTPStatus.OK, {"ok": True, "data": payload})

    def _handle_search(self, request_body: dict[str, Any]) -> None:
        try:
            payload = search_memory(
                query=str(request_body.get("query", "")),
                mock=_coerce_bool(request_body.get("mock", DEFAULT_MOCK)),
                top_k=int(request_body.get("topK", 5)),
                candidate_k=int(request_body.get("candidateK", 16)),
                rebuild_index=_coerce_bool(request_body.get("rebuildIndex", False)),
                timeout=int(request_body.get("timeout", 90)),
            )
        except Exception as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
            return

        self._send_json(HTTPStatus.OK, {"ok": True, "data": payload})

    def _handle_frontend_today(self, request_body: dict[str, Any]) -> None:
        try:
            payload = get_today_overview(
                mock=_coerce_bool(request_body.get("mock", DEFAULT_MOCK)),
                timeout=int(request_body.get("timeout", 90)),
            )
        except Exception as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
            return
        self._send_json(HTTPStatus.OK, {"ok": True, "data": payload})

    def _handle_frontend_calendar(self, request_body: dict[str, Any]) -> None:
        try:
            payload = get_calendar_month(
                year=int(request_body.get("year", 2026)),
                month=int(request_body.get("month", 5)),
            )
        except Exception as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
            return
        self._send_json(HTTPStatus.OK, {"ok": True, "data": payload})

    def _handle_frontend_daily_review(self, request_body: dict[str, Any]) -> None:
        try:
            date_value = str(request_body.get("date", "")).strip() or None
            payload = get_daily_review(
                date_key=date_value,
                mock=_coerce_bool(request_body.get("mock", DEFAULT_MOCK)),
                timeout=int(request_body.get("timeout", 90)),
            )
        except Exception as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
            return
        self._send_json(HTTPStatus.OK, {"ok": True, "data": payload})

    def _handle_frontend_search_guide(self) -> None:
        try:
            payload = get_search_guide()
        except Exception as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
            return
        self._send_json(HTTPStatus.OK, {"ok": True, "data": payload})

    def _handle_frontend_search(self, request_body: dict[str, Any]) -> None:
        try:
            payload = search_memories_for_frontend(
                query=str(request_body.get("query", "")),
                mock=_coerce_bool(request_body.get("mock", DEFAULT_MOCK)),
                top_k=int(request_body.get("topK", 5)),
                candidate_k=int(request_body.get("candidateK", 16)),
                rebuild_index=_coerce_bool(request_body.get("rebuildIndex", False)),
                timeout=int(request_body.get("timeout", 90)),
            )
        except Exception as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
            return
        self._send_json(HTTPStatus.OK, {"ok": True, "data": payload})

    def _handle_frontend_weekly(self, request_body: dict[str, Any]) -> None:
        try:
            payload = get_weekly_summary(
                offset=int(request_body.get("offset", 0)),
                mock=_coerce_bool(request_body.get("mock", DEFAULT_MOCK)),
                timeout=int(request_body.get("timeout", 90)),
            )
        except Exception as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
            return
        self._send_json(HTTPStatus.OK, {"ok": True, "data": payload})

    def _handle_frontend_monthly(self, request_body: dict[str, Any]) -> None:
        try:
            payload = get_monthly_summary(
                year=int(request_body.get("year", 2026)),
                month=int(request_body.get("month", 5)),
                mock=_coerce_bool(request_body.get("mock", DEFAULT_MOCK)),
                timeout=int(request_body.get("timeout", 90)),
            )
        except Exception as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
            return
        self._send_json(HTTPStatus.OK, {"ok": True, "data": payload})

    def _read_json_body(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length == 0:
            return {}

        raw_body = self.rfile.read(content_length).decode("utf-8")
        try:
            parsed = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise ValueError("Request body must be valid JSON") from exc
        if not isinstance(parsed, dict):
            raise ValueError("Request body must be a JSON object")
        return parsed

    def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self._send_common_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_empty(self, status: HTTPStatus) -> None:
        self.send_response(status)
        self._send_common_headers()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _send_common_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


def run(host: str, port: int, mock_default: bool) -> None:
    global DEFAULT_MOCK
    DEFAULT_MOCK = mock_default
    server = ThreadingHTTPServer((host, port), LifeTraceRequestHandler)
    print(f"LifeTrace LLM backend listening on http://{host}:{port}")
    print(f"Default mock mode: {DEFAULT_MOCK}")
    server.serve_forever()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the LifeTrace demo backend API.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--mock-default", action="store_true", help="Use mock generation unless a request overrides it.")
    return parser.parse_args()


def _first(values: list[str] | None, fallback: str) -> str:
    return values[0] if values else fallback


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return _parse_bool(value)
    return bool(value)


if __name__ == "__main__":
    args = parse_args()
    run(args.host, args.port, args.mock_default)
