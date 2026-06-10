#!/usr/bin/env python3
"""Exa web_search provider helper for ArkSpace."""

from __future__ import annotations

import argparse
import datetime as dt
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


def parse_json_value(value: str | None) -> Any:
    if not value:
        return None
    stripped = value.strip()
    if stripped.startswith("{") or stripped.startswith("["):
        return json.loads(stripped)
    path = Path(value)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return json.loads(stripped)


def freshness_start(value: str | None) -> str | None:
    if not value:
        return None
    days_by_value = {
        "day": 1,
        "week": 7,
        "month": 30,
        "year": 365,
    }
    days = days_by_value.get(value)
    if not days:
        raise provider_config.ProviderConfigError("--freshness must be one of day, week, month, year")
    start = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    return start.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def validate_category_filters(
    category: str | None,
    *,
    include_domains: list[str] | None,
    exclude_domains: list[str] | None,
    start_crawl_date: str | None,
    end_crawl_date: str | None,
    start_published_date: str | None,
    end_published_date: str | None,
) -> None:
    if category == "company":
        if exclude_domains or start_crawl_date or end_crawl_date or start_published_date or end_published_date:
            raise provider_config.ProviderConfigError(
                "Exa company search does not support exclude domains or crawl/published date filters; "
                "put those constraints in the natural-language query"
            )
    if category == "people":
        if include_domains or exclude_domains or start_crawl_date or end_crawl_date or start_published_date or end_published_date:
            raise provider_config.ProviderConfigError(
                "Exa people search does not support domain or crawl/published date filters; "
                "put those constraints in the natural-language query"
            )


def check_config(config_path: str | None = None, state_path: str | None = None) -> dict[str, Any]:
    return exa_client.check_config("web_search", config_path, state_path)


def run_search(
    query: str,
    *,
    max_results: int = 5,
    search_type: str | None = None,
    category: str | None = None,
    freshness: str | None = None,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
    start_crawl_date: str | None = None,
    end_crawl_date: str | None = None,
    start_published_date: str | None = None,
    end_published_date: str | None = None,
    include_text: bool = False,
    include_highlights: bool = False,
    include_summary: bool = False,
    text_max_characters: int | None = None,
    highlight_query: str | None = None,
    highlight_num_sentences: int | None = None,
    highlights_per_url: int | None = None,
    highlight_max_characters: int | None = None,
    summary_query: str | None = None,
    additional_queries: list[str] | None = None,
    user_location: str | None = None,
    moderation: bool = False,
    output_schema: dict[str, Any] | None = None,
    system_prompt: str | None = None,
    stream: bool = False,
    timeout: int = 30,
    config_path: str | None = None,
    state_path: str | None = None,
    post_json: Callable[[str, dict[str, str], dict[str, Any], int], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    resolved = exa_client.resolve_exa(capability="web_search", config_path=config_path, state_path=state_path)
    endpoint = resolved.get("endpoint") or {"id": "default", "base_url": exa_client.DEFAULT_BASE_URL}
    payload: dict[str, Any] = {"query": query, "numResults": max(1, min(100, int(max_results)))}
    if search_type:
        payload["type"] = search_type
    if category:
        payload["category"] = category
    if include_domains:
        payload["includeDomains"] = include_domains
    if exclude_domains:
        payload["excludeDomains"] = exclude_domains
    if freshness:
        if start_published_date or end_published_date:
            raise provider_config.ProviderConfigError("--freshness cannot be combined with explicit published date filters")
        start_published_date = freshness_start(freshness)
    validate_category_filters(
        category,
        include_domains=include_domains,
        exclude_domains=exclude_domains,
        start_crawl_date=start_crawl_date,
        end_crawl_date=end_crawl_date,
        start_published_date=start_published_date,
        end_published_date=end_published_date,
    )
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
        contents["text"] = {"maxCharacters": text_max_characters} if text_max_characters else True
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
        contents["highlights"] = highlights or True
    if include_summary:
        contents["summary"] = {"query": summary_query} if summary_query else True
    if contents:
        payload["contents"] = contents
    if additional_queries:
        if search_type not in {"deep-lite", "deep", "deep-reasoning"}:
            raise provider_config.ProviderConfigError("--additional-queries requires --search-type deep-lite, deep, or deep-reasoning")
        payload["additionalQueries"] = additional_queries
    if user_location:
        payload["userLocation"] = user_location
    if moderation:
        payload["moderation"] = True
    if output_schema:
        payload["outputSchema"] = output_schema
    if system_prompt:
        payload["systemPrompt"] = system_prompt
    if stream:
        payload["stream"] = True

    try:
        if post_json is None:
            response = exa_client.post_json(
                exa_client.endpoint_url(endpoint["base_url"], "/search"),
                exa_client.auth_headers(resolved),
                payload,
                timeout,
                label="Search",
            )
        else:
            response = exa_client.safe_json_call(
                lambda: post_json(
                    exa_client.endpoint_url(endpoint["base_url"], "/search"),
                    exa_client.auth_headers(resolved),
                    payload,
                    timeout,
                ),
                label="Search",
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
        "capability": "web_search",
        "query": query,
        "results": results,
        "context": response.get("context"),
        "structured": response.get("content") or response.get("output"),
        "resolved_search_type": response.get("resolvedSearchType"),
        "cost_dollars": response.get("costDollars"),
        "request_id": response.get("requestId") or response.get("request_id"),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search through ArkSpace's Exa provider.")
    parser.add_argument("query", nargs="?")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--search-type")
    parser.add_argument("--category")
    parser.add_argument("--freshness", choices=["day", "week", "month", "year"])
    parser.add_argument("--include-domains")
    parser.add_argument("--exclude-domains")
    parser.add_argument("--start-crawl-date")
    parser.add_argument("--end-crawl-date")
    parser.add_argument("--start-published-date")
    parser.add_argument("--end-published-date")
    parser.add_argument("--include-text", action="store_true")
    parser.add_argument("--include-highlights", action="store_true")
    parser.add_argument("--include-summary", action="store_true")
    parser.add_argument("--text-max-characters", type=int)
    parser.add_argument("--highlight-query")
    parser.add_argument("--highlight-num-sentences", type=int)
    parser.add_argument("--highlights-per-url", type=int)
    parser.add_argument("--highlight-max-characters", type=int)
    parser.add_argument("--summary-query")
    parser.add_argument("--additional-queries")
    parser.add_argument("--user-location")
    parser.add_argument("--moderation", action="store_true")
    parser.add_argument("--output-schema", help="JSON string or path to a JSON schema file")
    parser.add_argument("--system-prompt")
    parser.add_argument("--stream", action="store_true")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--config-path")
    parser.add_argument("--state-path")
    parser.add_argument("--output", choices=["json", "markdown"], default="markdown")
    return parser.parse_args()


def print_markdown(result: dict[str, Any]) -> None:
    if result.get("ok") is False:
        print(f"Exa is not configured: {result['error']}")
        return
    if result.get("ok") is True:
        print("Exa web_search provider is configured.")
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
            if not args.query:
                raise provider_config.ProviderConfigError("query is required")
            result = run_search(
                args.query,
                max_results=args.max_results,
                search_type=args.search_type,
                category=args.category,
                freshness=args.freshness,
                include_domains=parse_csv(args.include_domains),
                exclude_domains=parse_csv(args.exclude_domains),
                start_crawl_date=args.start_crawl_date,
                end_crawl_date=args.end_crawl_date,
                start_published_date=args.start_published_date,
                end_published_date=args.end_published_date,
                include_text=args.include_text,
                include_highlights=args.include_highlights,
                include_summary=args.include_summary,
                text_max_characters=args.text_max_characters,
                highlight_query=args.highlight_query,
                highlight_num_sentences=args.highlight_num_sentences,
                highlights_per_url=args.highlights_per_url,
                highlight_max_characters=args.highlight_max_characters,
                summary_query=args.summary_query,
                additional_queries=parse_csv(args.additional_queries),
                user_location=args.user_location,
                moderation=args.moderation,
                output_schema=parse_json_value(args.output_schema),
                system_prompt=args.system_prompt,
                stream=args.stream,
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
