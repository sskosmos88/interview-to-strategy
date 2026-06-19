"""CLI entrypoint for interview-to-strategy generator.

Usage:
    python main.py --input data/sample-transcript.txt --name "Анна Ковалёва" --output output/strategy.md
    python main.py --input data/sample-transcript.txt --name "Анна Ковалёва" --output output/strategy.md --no-api

Environment:
    ANTHROPIC_API_KEY - required for Claude-powered analysis.
"""

from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv

from src.analyzer import analyze
from src.formatter import render, write_output

load_dotenv()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a marketing strategy document from a raw interview transcript.",
    )
    parser.add_argument("--input", "-i", required=True, help="Path to raw transcript text file")
    parser.add_argument("--name", "-n", default="", help="Expert name (fallback if not detected)")
    parser.add_argument("--output", "-o", default="output/strategy.md", help="Output Markdown path")
    parser.add_argument(
        "--no-api",
        action="store_true",
        help="Use local rule-based analysis instead of Claude API",
    )
    parser.add_argument(
        "--producer",
        default="Саша Космос",
        help="Producer name for the document signature",
    )
    args = parser.parse_args(argv)

    if not os.path.exists(args.input):
        print(f"[ERROR] Input file not found: {args.input}")
        return 1

    with open(args.input, "r", encoding="utf-8") as f:
        transcript = f.read()

    if not transcript.strip():
        print("[ERROR] Input file is empty")
        return 1

    print(f"[INFO] Analyzing transcript ({len(transcript)} chars)...")
    use_api = not args.no_api
    if use_api and not os.environ.get("ANTHROPIC_API_KEY"):
        print("[WARN] ANTHROPIC_API_KEY not found, switching to local analysis.")
        use_api = False

    data = analyze(transcript, name=args.name, use_api=use_api)

    print(f"[INFO] Rendering strategy document for '{data.name or args.name}'...")
    producer_info = {
        "name": args.producer,
        "phone": "+7 (909) 581-91-99",
        "telegram": "https://t.me/sskosmos",
        "site": "https://sskosmos.ru",
        "vk": "https://vk.com/sskosmos88",
    }
    document = render(data, producer=producer_info)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    write_output(args.output, document)
    print(f"[DONE] Strategy written to: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
