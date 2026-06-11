#!/usr/bin/env python3
"""Firecrawl CLI web_search provider helper for ArkSpace."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

RUNTIME_DIR = Path(__file__).resolve().parents[2] / "provider-manager" / "scripts"
sys.path.insert(0, str(RUNTIME_DIR))

from arkspace_runtime import firecrawl_cli, provider_config


def check_config(config_path: str | None = None, state_path: str | None = None) -> dict[str, Any]:
    return firecrawl_cli.check_config("web_search", config_path, state_path)


def run_search(
    query: str,
    *,
    max_results: int = 5,
    include_text: bool = False,
    sources: str | None = None,
    categories: str | None = None,
    timeout: int = 60,
    config_path: str | None = None,
    state_path: str | None = None,
) -> dict[str, Any]:
    resolved = firecrawl_cli.resolve_firecrawl(capability="web_search", config_path=config_path, state_path=state_path)
    command = ["search", query, "--limit", str(max(1, min(20, int(max_results)))), "--json"]
    if include_text:
        command.append("--scrape")
        command.extend(["--scrape-formats", "markdown"])
    if sources:
        command.extend(["--sources", sources])
    if categories:
        command.extend(["--categories", categories])
    raw = firecrawl_cli.run_cli(resolved, command, timeout=timeout, config_path=config_path, state_path=state_path)
    return {"provider": "firecrawl", "capability": "web_search", "query": query, "response": firecrawl_cli.parse_json_or_text(raw)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search through ArkSpace's Firecrawl CLI provider.")
    parser.add_argument("query", nargs="?")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--include-text", action="store_true")
    parser.add_argument("--sources")
    parser.add_argument("--categories")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--config-path")
    parser.add_argument("--state-path")
    parser.add_argument("--output", choices=["json", "markdown"], default="markdown")
    return parser.parse_args()


def print_markdown(result: dict[str, Any]) -> None:
    if result.get("ok") is False:
        print(f"Firecrawl Search is not configured: {result['error']}")
        return
    if result.get("ok") is True:
        print("Firecrawl web_search provider is configured.")
        return
    print(json.dumps(result.get("response"), ensure_ascii=False, indent=2))


def main() -> int:
    args = parse_args()
    try:
        if args.check:
            result = check_config(args.config_path, args.state_path)
        else:
            if not args.query:
                raise provider_config.ProviderConfigError("query is required")
            result = run_search(
                args.query,
                max_results=args.max_results,
                include_text=args.include_text,
                sources=args.sources,
                categories=args.categories,
                timeout=args.timeout,
                config_path=args.config_path,
                state_path=args.state_path,
            )
    except provider_config.ProviderConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if args.output == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_markdown(result)
    return 0 if result.get("ok", True) else 2


if __name__ == "__main__":
    raise SystemExit(main())
