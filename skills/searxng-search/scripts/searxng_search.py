#!/usr/bin/env python3
"""Query a configured SearXNG instance."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "skills" / "provider-manager" / "scripts"))

from arkspace_runtime.provider_config import (  # noqa: E402
    ProviderConfigError,
    default_config_path,
    public_view,
    resolve_provider,
    set_provider_endpoint,
)

PROVIDER_ID = "searxng"
CAPABILITY = "web_search"


def env_base_url() -> str | None:
    return os.environ.get("SEARXNG_URL") or os.environ.get("SEARXNG_BASE_URL")


def resolve_base_url(args: argparse.Namespace) -> tuple[str | None, str | None]:
    if args.base_url:
        return args.base_url, "--base-url"
    env_value = env_base_url()
    if env_value:
        source = "SEARXNG_URL" if os.environ.get("SEARXNG_URL") else "SEARXNG_BASE_URL"
        return env_value, source
    resolved = resolve_provider(
        PROVIDER_ID,
        capability=CAPABILITY,
        config_path=args.config_path,
        require_endpoint=True,
    )
    endpoint = resolved.get("endpoint") or {}
    value = endpoint.get("base_url")
    if value:
        return value, str(default_config_path(args.config_path))
    return None, None


def normalize_base_url(url: str) -> str:
    url = url.strip()
    if not url:
        raise ValueError("empty base URL")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url.rstrip("/")


def fetch_json(url: str, timeout: float) -> Any:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "ArkSpace-searxng-search/0.1",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        content_type = response.headers.get("content-type", "")
        body = response.read()
    if "json" not in content_type.lower():
        body_start = body[:80].decode("utf-8", "replace")
        raise ValueError(f"expected JSON, got {content_type or 'unknown'}: {body_start!r}")
    return json.loads(body.decode("utf-8"))


def search_instance(base_url: str, args: argparse.Namespace) -> dict[str, Any]:
    params = build_params(args)
    data = fetch_search_json(base_url, args, params)
    results = data.get("results") or []
    if (
        args.categories
        and args.categories != "general"
        and not args.no_category_fallback
        and not results
    ):
        fallback_params = dict(params)
        fallback_params["categories"] = "general"
        data = fetch_search_json(base_url, args, fallback_params)
        data["_arkspace_category_fallback"] = "general"
    return data


def build_params(args: argparse.Namespace) -> dict[str, str]:
    params = {
        "q": args.query,
        "format": "json",
        "pageno": str(args.page),
    }
    optional = {
        "categories": args.categories,
        "engines": args.engines,
        "language": args.language,
        "time_range": args.time_range,
        "safesearch": args.safesearch,
    }
    params.update({key: value for key, value in optional.items() if value is not None})
    return params


def fetch_search_json(base_url: str, args: argparse.Namespace, params: dict[str, str]) -> dict[str, Any]:
    url = f"{normalize_base_url(base_url)}/search?{urllib.parse.urlencode(params)}"
    started = time.monotonic()
    data = fetch_json(url, args.timeout)
    elapsed = time.monotonic() - started
    if not isinstance(data, dict):
        raise ValueError("SearXNG response was not a JSON object")
    data["_arkspace_instance"] = normalize_base_url(base_url)
    data["_arkspace_elapsed_seconds"] = round(elapsed, 3)
    return data


def simplify_result(result: dict[str, Any]) -> dict[str, Any]:
    keep = [
        "title",
        "url",
        "content",
        "engine",
        "category",
        "parsed_url",
        "img_src",
        "thumbnail",
        "author",
        "publishedDate",
        "published_date",
        "score",
    ]
    return {key: result[key] for key in keep if key in result and result[key]}


def search_url(base_url: str, query: str) -> str:
    params = urllib.parse.urlencode({"q": query})
    return f"{normalize_base_url(base_url)}/search?{params}"


def emit_markdown(data: dict[str, Any], limit: int) -> None:
    instance = data.get("_arkspace_instance", "unknown instance")
    results = data.get("results") or []
    print(f"Instance: {instance}")
    print()
    for index, item in enumerate(results[:limit], start=1):
        if not isinstance(item, dict):
            continue
        title = item.get("title") or item.get("url") or "Untitled"
        url = item.get("url") or ""
        content = (item.get("content") or "").strip()
        engine = item.get("engine") or item.get("category") or ""
        print(f"{index}. [{title}]({url})")
        if engine:
            print(f"   Source: {engine}")
        if content:
            print(f"   {content[:500]}")
        print()


def emit_json(data: dict[str, Any], limit: int) -> None:
    output = {
        "instance": data.get("_arkspace_instance"),
        "elapsed_seconds": data.get("_arkspace_elapsed_seconds"),
        "query": data.get("query"),
        "number_of_results": data.get("number_of_results"),
        "category_fallback": data.get("_arkspace_category_fallback"),
        "answers": data.get("answers") or [],
        "corrections": data.get("corrections") or [],
        "suggestions": data.get("suggestions") or [],
        "results": [
            simplify_result(item)
            for item in (data.get("results") or [])[:limit]
            if isinstance(item, dict)
        ],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


def emit_config(args: argparse.Namespace) -> None:
    try:
        base_url, source = resolve_base_url(args)
    except ProviderConfigError:
        base_url, source = None, None
    resolved: dict[str, Any] | None = None
    try:
        resolved = public_view(
            resolve_provider(
                PROVIDER_ID,
                capability=CAPABILITY,
                config_path=args.config_path,
                require_endpoint=False,
            )
        )
    except ProviderConfigError:
        resolved = None
    output = {
        "config_path": str(default_config_path(args.config_path)),
        "base_url": normalize_base_url(base_url) if base_url else None,
        "source": source,
        "env": {
            "SEARXNG_URL": bool(os.environ.get("SEARXNG_URL")),
            "SEARXNG_BASE_URL": bool(os.environ.get("SEARXNG_BASE_URL")),
            "ARKSPACE_PROVIDER_CONFIG": bool(os.environ.get("ARKSPACE_PROVIDER_CONFIG")),
        },
        "provider": resolved,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search a configured SearXNG instance.")
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("--base-url", help="Self-hosted SearXNG base URL")
    parser.add_argument("--save-base-url", help="Persist a self-hosted SearXNG base URL to ArkSpace provider config and exit")
    parser.add_argument("--config-path", help="Provider config file path; defaults to $ARKSPACE_PROVIDER_CONFIG or ~/.config/ark-space/providers.json")
    parser.add_argument("--print-config", action="store_true", help="Print resolved SearXNG configuration and exit")
    parser.add_argument("--categories", help="Comma-separated categories")
    parser.add_argument("--engines", help="Comma-separated engines")
    parser.add_argument("--language", help="Language code")
    parser.add_argument("--time-range", choices=["day", "month", "year"])
    parser.add_argument("--safesearch", choices=["0", "1", "2"])
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument("--no-category-fallback", action="store_true")
    parser.add_argument("--check", action="store_true", help="Probe availability using the configured instance")
    parser.add_argument("--output", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()
    if args.save_base_url or args.print_config:
        return args
    if args.check and not args.query:
        args.query = "test"
        args.limit = min(args.limit, 1)
    if not args.query:
        parser.error("query is required unless --check is used")
    return args


def main() -> int:
    args = parse_args()
    if args.save_base_url:
        path = set_provider_endpoint(
            PROVIDER_ID,
            capability=CAPABILITY,
            base_url=args.save_base_url,
            config_path=args.config_path,
        )
        print(f"saved SearXNG base URL to ArkSpace provider config: {path}")
        return 0
    if args.print_config:
        emit_config(args)
        return 0

    bases: list[str] = []
    try:
        base_url, _source = resolve_base_url(args)
        if base_url:
            bases.append(base_url)
    except ProviderConfigError as exc:
        print(
            f"no configured SearXNG provider: {exc}; pass --base-url for a one-off search",
            file=sys.stderr,
        )
        return 2

    if not bases:
        config_path = default_config_path(args.config_path)
        print(
            "no SearXNG instance available; set SEARXNG_URL, run "
            "`python3 scripts/arkspace_provider.py configure searxng --base-url <url>`, "
            f"or pass --base-url; config path: {config_path}",
            file=sys.stderr,
        )
        return 2

    failures: list[str] = []
    for base in bases:
        try:
            data = search_instance(base, args)
            if args.output == "json":
                emit_json(data, args.limit)
            else:
                emit_markdown(data, args.limit)
            return 0
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            failures.append(f"{base}: {exc}")

    print("configured SearXNG instance failed", file=sys.stderr)
    for failure in failures:
        print(f"- {failure}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
