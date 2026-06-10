#!/usr/bin/env python3
"""Exa web_fetch provider helper for ArkSpace."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

RUNTIME_DIR = Path(__file__).resolve().parents[2] / "provider-manager" / "scripts"
sys.path.insert(0, str(RUNTIME_DIR))

from arkspace_runtime import exa_client, provider_config


def parse_csv(value: str | None) -> list[str] | None:
    if not value:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def check_config(config_path: str | None = None, state_path: str | None = None) -> dict[str, Any]:
    return exa_client.check_config("web_fetch", config_path, state_path)


def run_contents(
    urls: list[str],
    *,
    ids: list[str] | None = None,
    include_text: bool = True,
    include_highlights: bool = False,
    include_summary: bool = False,
    text_max_characters: int | None = None,
    highlight_query: str | None = None,
    highlight_num_sentences: int | None = None,
    highlights_per_url: int | None = None,
    highlight_max_characters: int | None = None,
    summary_query: str | None = None,
    max_age_hours: int | None = None,
    subpages: int | None = None,
    subpage_target: list[str] | None = None,
    include_links: bool = False,
    timeout: int = 30,
    config_path: str | None = None,
    state_path: str | None = None,
    post_json: Callable[[str, dict[str, str], dict[str, Any], int], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    resolved = exa_client.resolve_exa(capability="web_fetch", config_path=config_path, state_path=state_path)
    endpoint = resolved.get("endpoint") or {"id": "default", "base_url": exa_client.DEFAULT_BASE_URL}
    payload: dict[str, Any] = {}
    if urls:
        payload["urls"] = urls
    if ids:
        payload["ids"] = ids
    if "urls" not in payload and "ids" not in payload:
        raise provider_config.ProviderConfigError("at least one URL or Exa id is required")
    if include_text:
        payload["text"] = {"maxCharacters": text_max_characters} if text_max_characters else True
    if include_highlights:
        highlights: dict[str, Any] = {}
        if highlight_query:
            highlights["query"] = highlight_query
        if highlight_num_sentences:
            highlights["numSentences"] = highlight_num_sentences
        if highlights_per_url:
            highlights["highlightsPerUrl"] = highlights_per_url
        if highlight_max_characters:
            highlights["maxCharacters"] = highlight_max_characters
        payload["highlights"] = highlights or True
    if include_summary:
        payload["summary"] = {"query": summary_query} if summary_query else True
    if max_age_hours is not None:
        payload["maxAgeHours"] = max_age_hours
    if subpages is not None:
        payload["subpages"] = subpages
    if subpage_target:
        payload["subpageTarget"] = subpage_target
    if include_links:
        payload["extras"] = {"links": True}

    try:
        if post_json is None:
            response = exa_client.post_json(
                exa_client.endpoint_url(endpoint["base_url"], "/contents"),
                exa_client.auth_headers(resolved),
                payload,
                timeout,
                label="Contents",
            )
        else:
            response = exa_client.safe_json_call(
                lambda: post_json(
                    exa_client.endpoint_url(endpoint["base_url"], "/contents"),
                    exa_client.auth_headers(resolved),
                    payload,
                    timeout,
                ),
                label="Contents",
            )
        exa_client.record_success(resolved, config_path=config_path, state_path=state_path)
    except provider_config.ProviderConfigError as exc:
        exa_client.record_failure(resolved, exc, config_path=config_path, state_path=state_path)
        raise

    results = []
    for item in response.get("results") or []:
        if not isinstance(item, dict):
            continue
        results.append(
            {
                "url": item.get("url") or "",
                "title": item.get("title") or "",
                "raw_content": item.get("text") or "",
                "summary": item.get("summary") or "",
                "highlights": item.get("highlights") or [],
                "highlight_scores": item.get("highlightScores") or [],
                "published": item.get("publishedDate"),
                "author": item.get("author"),
                "id": item.get("id"),
                "image": item.get("image"),
                "favicon": item.get("favicon"),
                "subpages": item.get("subpages") or [],
                "extras": item.get("extras") or {},
            }
        )
    return {
        "provider": "exa",
        "capability": "web_fetch",
        "results": results,
        "statuses": response.get("statuses") or [],
        "context": response.get("context"),
        "cost_dollars": response.get("costDollars"),
        "request_id": response.get("requestId") or response.get("request_id"),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch URL contents through ArkSpace's Exa provider.")
    parser.add_argument("urls", nargs="*")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--ids", help="Comma-separated Exa result ids to fetch")
    parser.add_argument("--include-text", action="store_true", default=True)
    parser.add_argument("--include-highlights", action="store_true")
    parser.add_argument("--include-summary", action="store_true")
    parser.add_argument("--text-max-characters", type=int)
    parser.add_argument("--highlight-query")
    parser.add_argument("--highlight-num-sentences", type=int)
    parser.add_argument("--highlights-per-url", type=int)
    parser.add_argument("--highlight-max-characters", type=int)
    parser.add_argument("--summary-query")
    parser.add_argument("--max-age-hours", type=int)
    parser.add_argument("--subpages", type=int)
    parser.add_argument("--subpage-target")
    parser.add_argument("--include-links", action="store_true")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--config-path")
    parser.add_argument("--state-path")
    parser.add_argument("--output", choices=["json", "markdown"], default="markdown")
    return parser.parse_args()


def print_markdown(result: dict[str, Any]) -> None:
    if result.get("ok") is False:
        print(f"Exa Contents is not configured: {result['error']}")
        return
    if result.get("ok") is True:
        print("Exa web_fetch provider is configured.")
        return
    for item in result.get("results") or []:
        print(f"## {item.get('title') or item.get('url')}")
        print()
        if item.get("summary"):
            print(item["summary"])
            print()
        print(item.get("raw_content") or "")
        print()


def main() -> int:
    args = parse_args()
    try:
        if args.check:
            result = check_config(args.config_path, args.state_path)
        else:
            result = run_contents(
                args.urls,
                ids=parse_csv(args.ids),
                include_text=args.include_text,
                include_highlights=args.include_highlights,
                include_summary=args.include_summary,
                text_max_characters=args.text_max_characters,
                highlight_query=args.highlight_query,
                highlight_num_sentences=args.highlight_num_sentences,
                highlights_per_url=args.highlights_per_url,
                highlight_max_characters=args.highlight_max_characters,
                summary_query=args.summary_query,
                max_age_hours=args.max_age_hours,
                subpages=args.subpages,
                subpage_target=parse_csv(args.subpage_target),
                include_links=args.include_links,
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
