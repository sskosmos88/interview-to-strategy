"""CLI entrypoint for interview-to-strategy generator.

Usage:
    # With local Ollama model
    python main.py --input data/sample-transcript.txt --name "Иван Петров" --output output/strategy.md

    # Force rule-based fallback without any LLM
    python main.py --input data/sample-transcript.txt --name "Иван Петров" --output output/strategy.md --fallback

Environment:
    ANTHROPIC_API_KEY  - for Claude-powered analysis
    PERPLEXITY_API_KEY - for Perplexity analysis
    OLLAMA_URL         - Ollama host (default: http://localhost:11434)
    OLLAMA_MODEL       - Ollama model name, e.g. llama3:latest
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
        "--fallback",
        action="store_true",
        help="Use local rule-based analysis instead of any LLM",
    )
    parser.add_argument("--producer-name", default="", help="Producer / author name")
    parser.add_argument("--producer-phone", default="", help="Producer phone")
    parser.add_argument("--producer-telegram", default="", help="Producer Telegram")
    parser.add_argument("--producer-site", default="", help="Producer website")
    parser.add_argument("--producer-vk", default="", help="Producer VK")
    parser.add_argument("--producer-email", default="", help="Producer email")
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
    provider = "fallback" if args.fallback else _detect_provider_label()
    print(f"[INFO] Provider: {provider}")

    data = analyze(transcript, name=args.name, use_llm=not args.fallback)

    print(f"[INFO] Rendering strategy document for '{data.name or args.name}'...")
    producer_info = {
        k.replace("producer_", ""): v
        for k, v in vars(args).items()
        if k.startswith("producer_") and v
    }
    document = render(data, producer=producer_info)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    write_output(args.output, document)
    print(f"[DONE] Strategy written to: {args.output}")
    return 0


def _detect_provider_label() -> str:
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.environ.get("PERPLEXITY_API_KEY"):
        return "perplexity"
    if os.environ.get("OLLAMA_MODEL"):
        return "ollama"
    return "fallback (no API key / OLLAMA_MODEL configured)"


if __name__ == "__main__":
    sys.exit(main())
