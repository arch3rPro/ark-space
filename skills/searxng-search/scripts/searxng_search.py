#!/usr/bin/env python3
"""Query SearXNG with self-host preference and public-instance fallback."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

DEFAULT_INSTANCES_URL = "https://searx.space/data/instances.json"


def env_base_url() -> str | None:
    return os.environ.get("SEARXNG_URL") or os.environ.get("SEARXNG_BASE_URL")


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


def candidate_instances(instances_url: str, timeout: float, max_candidates: int) -> list[str]:
    data = fetch_json(instances_url, timeout)
    instances = data.get("instances", {}) if isinstance(data, dict) else {}
    if not isinstance(instances, dict):
        return []

    candidates: list[tuple[float, float, str]] = []
    for base_url, detail in instances.items():
        if not isinstance(detail, dict):
            continue
        if detail.get("error"):
            continue
        if detail.get("analytics") is True:
            continue
        if detail.get("network_type") not in (None, "normal"):
            continue
        timing = detail.get("timing") if isinstance(detail.get("timing"), dict) else {}
        search = timing.get("search") if isinstance(timing.get("search"), dict) else {}
        success = float(search.get("success_percentage") or 0)
        all_timing = search.get("all") if isinstance(search.get("all"), dict) else {}
        median = float(all_timing.get("median") or 999)
        if success <= 0:
            continue
        candidates.append((-success, median, base_url))

    candidates.sort()
    return [base for _, _, base in candidates[:max_candidates]]


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


def emit_html_fallback(args: argparse.Namespace, bases: list[str], failures: list[str]) -> None:
    urls = [search_url(base, args.query) for base in bases[: args.limit]]
    if args.output == "json":
        print(
            json.dumps(
                {
                    "query": args.query,
                    "json_api_available": False,
                    "fallback": "html_search_urls",
                    "urls": urls,
                    "failures": failures,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    print("JSON API search failed on all attempted SearXNG instances.")
    print("Fallback HTML search URLs:")
    print()
    for index, url in enumerate(urls, start=1):
        print(f"{index}. {url}")
    print()
    print("Failures:")
    for failure in failures:
        print(f"- {failure}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search SearXNG with fallback instances.")
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("--base-url", default=env_base_url(), help="Self-hosted SearXNG base URL")
    parser.add_argument("--categories", help="Comma-separated categories")
    parser.add_argument("--engines", help="Comma-separated engines")
    parser.add_argument("--language", help="Language code")
    parser.add_argument("--time-range", choices=["day", "month", "year"])
    parser.add_argument("--safesearch", choices=["0", "1", "2"])
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument("--max-candidates", type=int, default=20)
    parser.add_argument("--instances-url", default=DEFAULT_INSTANCES_URL)
    parser.add_argument("--no-public-fallback", action="store_true")
    parser.add_argument("--no-category-fallback", action="store_true")
    parser.add_argument("--strict-json", action="store_true", help="Fail instead of emitting HTML fallback URLs")
    parser.add_argument("--check", action="store_true", help="Probe availability using the configured or discovered instance")
    parser.add_argument("--output", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()
    if args.check and not args.query:
        args.query = "test"
        args.limit = min(args.limit, 1)
    if not args.query:
        parser.error("query is required unless --check is used")
    return args


def main() -> int:
    args = parse_args()
    bases: list[str] = []
    if args.base_url:
        bases.append(args.base_url)
    elif not args.no_public_fallback:
        try:
            bases.extend(candidate_instances(args.instances_url, args.timeout, args.max_candidates))
        except Exception as exc:  # noqa: BLE001 - CLI should report all discovery failures.
            print(f"failed to load public SearXNG instances: {exc}", file=sys.stderr)

    if not bases:
        print("no SearXNG instance available; set SEARXNG_URL or allow public fallback", file=sys.stderr)
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

    if args.strict_json:
        print("all SearXNG instances failed", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    emit_html_fallback(args, bases, failures)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
