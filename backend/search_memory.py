"""Search LifeTrace memories with Chroma and LLM-enhanced ranking."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from search_service import default_search_output_path, search_memory
from service import write_json


def main() -> None:
    args = parse_args()
    payload = search_memory(
        query=args.query,
        mock=args.mock,
        top_k=args.top_k,
        candidate_k=args.candidate_k,
        rebuild_index=args.rebuild_index,
        timeout=args.timeout,
    )
    if args.print_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    out_path = Path(args.out) if args.out else default_search_output_path()
    write_json(out_path, payload)
    print(f"Wrote {out_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search LifeTrace memories.")
    parser.add_argument("--query", required=True, help="Natural language memory query.")
    parser.add_argument("--mock", action="store_true", help="Use local mock query understanding and local embeddings.")
    parser.add_argument("--top-k", type=int, default=5, help="Number of final results, 1 to 5.")
    parser.add_argument("--candidate-k", type=int, default=16, help="Number of Chroma candidates sent to selection.")
    parser.add_argument("--rebuild-index", action="store_true", help="Clear and rebuild the Chroma collection first.")
    parser.add_argument("--timeout", type=int, default=90, help="LLM request timeout in seconds.")
    parser.add_argument("--out", help="Output path for the search payload JSON.")
    parser.add_argument("--print-json", action="store_true", help="Print the search payload and do not write a file.")
    return parser.parse_args()


if __name__ == "__main__":
    main()
