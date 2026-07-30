#!/usr/bin/env python3
"""Exa related_pages provider helper for ArkSpace."""

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
    return exa_client.check_config("related_pages", config_path, state_path)


def run_similar(
    url: str,
    *,
    max_results: int = 5,
    search_type: str | None = None,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
    start_crawl_date: str | None = None,
    end_crawl_date: str | None = None,
    start_published_date: str | None = None,
    end_published_date: str | None = None,
    include_text: bool = False,
    include_highlights: bool = False,
    include_summary: bool = False,
    timeout: int = 30,
    config_path: str | None = None,
    state_path: str | None = None,
    post_json: Callable[[str, dict[str, str], dict[str, Any], int], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    resolved = exa_client.resolve_exa(capability="related_pages", config_path=config_path, state_path=state_path)
    endpoint = resolved.get("endpoint") or {"id": "default", "base_url": exa_client.DEFAULT_BASE_URL}
    payload: dict[str, Any] = {"url": url, "numResults": max(1, min(100, int(max_results)))}
    if search_type:
        payload["type"] = search_type
    if include_domains:
        payload["includeDomains"] = include_domains
    if exclude_domains:
        payload["excludeDomains"] = exclude_domains
    if start_crawl_date:
        payload["startCrawlDate"] = start_crawl_date
    if end_crawl_date:
        payload["endCrawlDate"] = end_crawl_date
    if start_published_date:
        payload["startPublishedDate"] = start_published_date
    if end_published_date:
        payload["endPublishedDate"] = end_published_date
    contents: dict[str, Any] = {}
    if include_text:
        contents["text"] = True
    if include_highlights:
        contents["highlights"] = True
    if include_summary:
        contents["summary"] = True
    if contents:
        payload["contents"] = contents

    try:
        if post_json is None:
            response = exa_client.post_json(
                exa_client.endpoint_url(endpoint["base_url"], "/findSimilar"),
                exa_client.auth_headers(resolved),
                payload,
                timeout,
                label="FindSimilar",
            )
        else:
            response = exa_client.safe_json_call(
                lambda: post_json(
                    exa_client.endpoint_url(endpoint["base_url"], "/findSimilar"),
                    exa_client.auth_headers(resolved),
                    payload,
                    timeout,
                ),
                label="FindSimilar",
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
                "title": item.get("title") or "",
                "url": item.get("url") or "",
                "snippet": item.get("text") or item.get("summary") or "",
                "score": item.get("score"),
                "published": item.get("publishedDate"),
                "id": item.get("id"),
                "image": item.get("image"),
                "favicon": item.get("favicon"),
                "author": item.get("author"),
                "highlights": item.get("highlights") or [],
                "highlight_scores": item.get("highlightScores") or [],
                "summary": item.get("summary") or "",
                "entities": item.get("entities") or [],
                "extras": item.get("extras") or {},
            }
        )
    return {
        "provider": "exa",
        "capability": "related_pages",
        "url": url,
        "results": results,
        "cost_dollars": response.get("costDollars"),
        "request_id": response.get("requestId") or response.get("request_id"),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Find similar pages through ArkSpace's Exa provider.")
    parser.add_argument("url", nargs="?")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--search-type")
    parser.add_argument("--include-domains")
    parser.add_argument("--exclude-domains")
    parser.add_argument("--start-crawl-date")
    parser.add_argument("--end-crawl-date")
    parser.add_argument("--start-published-date")
    parser.add_argument("--end-published-date")
    parser.add_argument("--include-text", action="store_true")
    parser.add_argument("--include-highlights", action="store_true")
    parser.add_argument("--include-summary", action="store_true")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--config-path")
    parser.add_argument("--state-path")
    parser.add_argument("--output", choices=["json", "markdown"], default="markdown")
    return parser.parse_args()


def print_markdown(result: dict[str, Any]) -> None:
    if result.get("ok") is False:
        print(f"Exa Similar is not configured: {result['error']}")
        return
    if result.get("ok") is True:
        print("Exa related_pages provider is configured.")
        return
    for index, item in enumerate(result.get("results") or [], start=1):
        print(f"{index}. [{item['title']}]({item['url']})")
        if item.get("snippet"):
            print(f"   {item['snippet']}")


def main() -> int:
    args = parse_args()
    try:
        if args.check:
            result = check_config(args.config_path, args.state_path)
        else:
            if not args.url:
                raise provider_config.ProviderConfigError("URL is required")
            result = run_similar(
                args.url,
                max_results=args.max_results,
                search_type=args.search_type,
                include_domains=parse_csv(args.include_domains),
                exclude_domains=parse_csv(args.exclude_domains),
                start_crawl_date=args.start_crawl_date,
                end_crawl_date=args.end_crawl_date,
                start_published_date=args.start_published_date,
                end_published_date=args.end_published_date,
                include_text=args.include_text,
                include_highlights=args.include_highlights,
                include_summary=args.include_summary,
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
