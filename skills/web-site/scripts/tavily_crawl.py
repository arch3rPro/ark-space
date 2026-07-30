#!/usr/bin/env python3
"""Tavily site crawl helper for ArkSpace."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

RUNTIME_DIR = Path(__file__).resolve().parents[2] / "provider-manager" / "scripts"
sys.path.insert(0, str(RUNTIME_DIR))

from arkspace_runtime import provider_config, tavily_client


def parse_csv(value: str | None) -> list[str] | None:
    if not value:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def bounded_int(value: int | None, *, minimum: int, maximum: int | None = None) -> int | None:
    if value is None:
        return None
    result = max(minimum, int(value))
    if maximum is not None:
        result = min(maximum, result)
    return result


def check_config(config_path: str | None = None, state_path: str | None = None) -> dict[str, Any]:
    return tavily_client.check_config("web_crawl", config_path, state_path)


def run_crawl(
    url: str,
    *,
    instructions: str | None = None,
    chunks_per_source: int | None = None,
    max_depth: int | None = None,
    max_breadth: int | None = None,
    limit: int | None = None,
    select_paths: list[str] | None = None,
    exclude_paths: list[str] | None = None,
    select_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
    allow_external: bool | None = None,
    include_images: bool = False,
    include_favicon: bool = False,
    extract_depth: str | None = None,
    content_format: str | None = None,
    timeout: int = 150,
    include_usage: bool = False,
    config_path: str | None = None,
    state_path: str | None = None,
    post_json: Callable[[str, dict[str, str], dict[str, Any], int], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    resolved = tavily_client.resolve_tavily(capability="web_crawl", config_path=config_path, state_path=state_path)
    endpoint = resolved.get("endpoint") or {"id": "default", "base_url": tavily_client.DEFAULT_BASE_URL}
    api_timeout = max(10, min(150, int(timeout)))
    payload: dict[str, Any] = {"url": url, "timeout": api_timeout}
    optional_values = {
        "instructions": instructions,
        "chunks_per_source": bounded_int(chunks_per_source, minimum=1, maximum=5),
        "max_depth": bounded_int(max_depth, minimum=1, maximum=5),
        "max_breadth": bounded_int(max_breadth, minimum=1, maximum=500),
        "limit": bounded_int(limit, minimum=1),
        "select_paths": select_paths,
        "exclude_paths": exclude_paths,
        "select_domains": select_domains,
        "exclude_domains": exclude_domains,
        "extract_depth": extract_depth,
        "format": content_format,
    }
    for key, value in optional_values.items():
        if value:
            payload[key] = value
    if allow_external is not None:
        payload["allow_external"] = allow_external
    if include_images:
        payload["include_images"] = True
    if include_favicon:
        payload["include_favicon"] = True
    if include_usage:
        payload["include_usage"] = True

    try:
        if post_json is None:
            response = tavily_client.post_json(
                tavily_client.endpoint_url(endpoint["base_url"], "/crawl"),
                tavily_client.auth_headers(resolved),
                payload,
                api_timeout + 5,
                label="Crawl",
            )
        else:
            response = tavily_client.safe_json_call(
                lambda: post_json(
                    tavily_client.endpoint_url(endpoint["base_url"], "/crawl"),
                    tavily_client.auth_headers(resolved),
                    payload,
                    api_timeout + 5,
                ),
                label="Crawl",
            )
        tavily_client.record_success(resolved, config_path=config_path, state_path=state_path)
    except provider_config.ProviderConfigError as exc:
        tavily_client.record_failure(resolved, exc, config_path=config_path, state_path=state_path)
        raise

    return {
        "provider": "tavily",
        "capability": "web_crawl",
        "base_url": response.get("base_url"),
        "results": response.get("results") or [],
        "usage": response.get("usage"),
        "request_id": response.get("request_id"),
        "response_time": response.get("response_time"),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crawl a site through ArkSpace's Tavily provider.")
    parser.add_argument("url", nargs="?")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--instructions")
    parser.add_argument("--chunks-per-source", type=int)
    parser.add_argument("--max-depth", type=int)
    parser.add_argument("--max-breadth", type=int)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--select-paths")
    parser.add_argument("--exclude-paths")
    parser.add_argument("--select-domains")
    parser.add_argument("--exclude-domains")
    parser.add_argument("--allow-external", dest="allow_external", action="store_true")
    parser.add_argument("--no-external", dest="allow_external", action="store_false")
    parser.set_defaults(allow_external=None)
    parser.add_argument("--include-images", action="store_true")
    parser.add_argument("--include-favicon", action="store_true")
    parser.add_argument("--extract-depth", choices=["basic", "advanced"])
    parser.add_argument("--format", dest="content_format", choices=["markdown", "text"])
    parser.add_argument("--include-usage", action="store_true")
    parser.add_argument("--timeout", type=int, default=150)
    parser.add_argument("--config-path")
    parser.add_argument("--state-path")
    parser.add_argument("--output", choices=["json", "markdown"], default="markdown")
    return parser.parse_args()


def print_markdown(result: dict[str, Any]) -> None:
    if result.get("ok") is False:
        print(f"Tavily Crawl is not configured: {result['error']}")
        return
    if result.get("ok") is True:
        print("Tavily web_crawl provider is configured.")
        return
    for item in result.get("results") or []:
        if not isinstance(item, dict):
            continue
        print(f"## {item.get('url') or ''}")
        print()
        print(item.get("raw_content") or "")
        print()


def main() -> int:
    args = parse_args()
    try:
        if args.check:
            result = check_config(args.config_path, args.state_path)
        else:
            if not args.url:
                raise provider_config.ProviderConfigError("url is required")
            result = run_crawl(
                args.url,
                instructions=args.instructions,
                chunks_per_source=args.chunks_per_source,
                max_depth=args.max_depth,
                max_breadth=args.max_breadth,
                limit=args.limit,
                select_paths=parse_csv(args.select_paths),
                exclude_paths=parse_csv(args.exclude_paths),
                select_domains=parse_csv(args.select_domains),
                exclude_domains=parse_csv(args.exclude_domains),
                allow_external=args.allow_external,
                include_images=args.include_images,
                include_favicon=args.include_favicon,
                extract_depth=args.extract_depth,
                content_format=args.content_format,
                include_usage=args.include_usage,
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
