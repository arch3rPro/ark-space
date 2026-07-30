#!/usr/bin/env python3
"""Tavily web_search provider helper for ArkSpace."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

RUNTIME_DIR = Path(__file__).resolve().parents[2] / "provider-manager" / "scripts"
sys.path.insert(0, str(RUNTIME_DIR))

from arkspace_runtime import provider_config

DEFAULT_BASE_URL = "https://api.tavily.com"


class ProviderRequestError(provider_config.ProviderConfigError):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


def failure_rotation_targets(endpoint_id: str | None, key_ref: str | None, status: int | None) -> tuple[str | None, str | None]:
    if status in {401, 403, 429}:
        return None, key_ref
    if status is None or status >= 500:
        return endpoint_id, None
    return endpoint_id, key_ref


def endpoint_url(base_url: str, path: str) -> str:
    return base_url.rstrip("/") + path


def auth_headers(resolved: dict[str, Any]) -> dict[str, str]:
    auth = resolved.get("auth") or {}
    if auth.get("type") != "api_key" or not auth.get("value"):
        raise provider_config.ProviderConfigError("provider tavily has no available API key")
    return {
        "Content-Type": "application/json",
        str(auth.get("header") or "Authorization"): f"{auth.get('prefix', '')}{auth['value']}",
    }


def post_json(url: str, headers: dict[str, str], payload: dict[str, Any], timeout: int) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise ProviderRequestError(f"Tavily Search HTTP {exc.code}: {body}", status=exc.code) from exc
    except urllib.error.URLError as exc:
        raise ProviderRequestError(f"Tavily Search request failed: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise ProviderRequestError(f"Tavily Search returned invalid JSON: {exc}") from exc
    except (TimeoutError, OSError) as exc:
        raise ProviderRequestError(f"Tavily Search request failed: {exc}") from exc


def safe_post_json(
    post_json_fn: Callable[[str, dict[str, str], dict[str, Any], int], dict[str, Any]],
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout: int,
) -> dict[str, Any]:
    try:
        return post_json_fn(url, headers, payload, timeout)
    except provider_config.ProviderConfigError:
        raise
    except json.JSONDecodeError as exc:
        raise ProviderRequestError(f"Tavily Search returned invalid JSON: {exc}") from exc
    except (TimeoutError, OSError) as exc:
        raise ProviderRequestError(f"Tavily Search request failed: {exc}") from exc


def resolve_tavily(
    *,
    capability: str,
    config_path: str | None = None,
    state_path: str | None = None,
) -> dict[str, Any]:
    return provider_config.resolve_provider(
        "tavily",
        capability=capability,
        config_path=config_path,
        state_path=state_path,
        require_secret=True,
    )


def check_config(config_path: str | None = None, state_path: str | None = None) -> dict[str, Any]:
    try:
        resolved = resolve_tavily(capability="web_search", config_path=config_path, state_path=state_path)
    except provider_config.ProviderConfigError as exc:
        return {"ok": False, "provider": "tavily", "capability": "web_search", "error": str(exc)}
    return {"ok": True, "provider": "tavily", "capability": "web_search", **provider_config.public_view(resolved)}


def run_search(
    query: str,
    *,
    max_results: int = 5,
    search_depth: str | None = None,
    topic: str | None = None,
    time_range: str | None = None,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
    include_answer: bool = False,
    timeout: int = 30,
    config_path: str | None = None,
    state_path: str | None = None,
    post_json: Callable[[str, dict[str, str], dict[str, Any], int], dict[str, Any]] = post_json,
) -> dict[str, Any]:
    resolved = resolve_tavily(capability="web_search", config_path=config_path, state_path=state_path)
    endpoint = resolved.get("endpoint") or {"id": "default", "base_url": DEFAULT_BASE_URL}
    payload: dict[str, Any] = {"query": query, "max_results": max(1, min(20, int(max_results)))}
    if search_depth:
        payload["search_depth"] = search_depth
    if topic:
        payload["topic"] = topic
    if time_range:
        payload["time_range"] = time_range
    if include_domains:
        payload["include_domains"] = include_domains
    if exclude_domains:
        payload["exclude_domains"] = exclude_domains
    if include_answer:
        payload["include_answer"] = True

    try:
        response = safe_post_json(
            post_json,
            endpoint_url(endpoint["base_url"], "/search"),
            auth_headers(resolved),
            payload,
            timeout,
        )
        provider_config.record_provider_result(
            "tavily",
            endpoint_id=endpoint.get("id"),
            key_ref=(resolved.get("auth") or {}).get("key_ref"),
            ok=True,
            status=200,
            config_path=config_path,
            state_path=state_path,
        )
    except provider_config.ProviderConfigError as exc:
        endpoint_id, key_ref = failure_rotation_targets(
            endpoint.get("id"),
            (resolved.get("auth") or {}).get("key_ref"),
            getattr(exc, "status", None),
        )
        provider_config.record_provider_result(
            "tavily",
            endpoint_id=endpoint_id,
            key_ref=key_ref,
            ok=False,
            status=getattr(exc, "status", None),
            config_path=config_path,
            state_path=state_path,
        )
        raise

    results = []
    for item in response.get("results") or []:
        if not isinstance(item, dict):
            continue
        results.append(
            {
                "title": item.get("title") or "",
                "url": item.get("url") or "",
                "snippet": item.get("content") or "",
                "score": item.get("score"),
                "published": item.get("published_date"),
            }
        )
    output = {
        "provider": "tavily",
        "capability": "web_search",
        "query": query,
        "results": results,
        "usage": response.get("usage"),
        "request_id": response.get("request_id"),
    }
    if response.get("answer"):
        output["answer"] = response["answer"]
    return output


def parse_csv(value: str | None) -> list[str] | None:
    if not value:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search through ArkSpace's Tavily provider.")
    parser.add_argument("query", nargs="?")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--search-depth")
    parser.add_argument("--topic")
    parser.add_argument("--time-range")
    parser.add_argument("--include-domains")
    parser.add_argument("--exclude-domains")
    parser.add_argument("--include-answer", action="store_true")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--config-path")
    parser.add_argument("--state-path")
    parser.add_argument("--output", choices=["json", "markdown"], default="markdown")
    return parser.parse_args()


def print_markdown(result: dict[str, Any]) -> None:
    if result.get("ok") is False:
        print(f"Tavily is not configured: {result['error']}")
        return
    if result.get("ok") is True:
        print("Tavily web_search provider is configured.")
        return
    if result.get("answer"):
        print(result["answer"])
        print()
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
                search_depth=args.search_depth,
                topic=args.topic,
                time_range=args.time_range,
                include_domains=parse_csv(args.include_domains),
                exclude_domains=parse_csv(args.exclude_domains),
                include_answer=args.include_answer,
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
