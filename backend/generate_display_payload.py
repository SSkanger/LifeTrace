"""Generate LifeTrace display-only JSON from cleaned demo data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from display_service import build_display_messages, generate_display_payload
from llm_client import DEFAULT_MAX_TOKENS
from service import DEFAULT_INPUTS, PROJECT_ROOT, read_json, write_json


DEFAULT_OUTPUTS = {
    "daily": PROJECT_ROOT / "outputs" / "lifetrace_daily_display_payload.json",
    "week": PROJECT_ROOT / "outputs" / "lifetrace_week_display_payload.json",
}


def main() -> None:
    args = parse_args()
    data = read_json(Path(args.data)) if args.data else None
    read_guide = read_json(Path(args.guide)) if args.guide else None
    if data is None or read_guide is None:
        defaults = DEFAULT_INPUTS[args.scope]
        data = data or read_json(defaults["data"])
        read_guide = read_guide or read_json(defaults["guide"])

    if args.print_prompt:
        messages = build_display_messages(args.scope, data, read_guide)
        print(json.dumps(messages, ensure_ascii=False, indent=2))
        return

    payload = generate_display_payload(
        scope=args.scope,
        data=data,
        read_guide=read_guide,
        mock=args.mock,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        timeout=args.timeout,
    )
    out_path = Path(args.out) if args.out else DEFAULT_OUTPUTS[args.scope]
    write_json(out_path, payload)
    print(f"Wrote {out_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate LifeTrace display-only payload.")
    parser.add_argument("--scope", choices=["daily", "week"], required=True, help="Display data scope.")
    parser.add_argument("--data", help="Path to cleaned LifeTrace data JSON.")
    parser.add_argument("--guide", help="Path to the read guide JSON.")
    parser.add_argument("--out", help="Output path for the display payload JSON.")
    parser.add_argument("--mock", action="store_true", help="Generate deterministic mock output without calling an LLM.")
    parser.add_argument("--print-prompt", action="store_true", help="Print the final chat messages and exit.")
    parser.add_argument("--temperature", type=float, default=0.2, help="LLM temperature for non-mock generation.")
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS, help="Max output tokens for non-mock generation.")
    parser.add_argument("--timeout", type=int, default=90, help="LLM request timeout in seconds.")
    return parser.parse_args()


if __name__ == "__main__":
    main()
