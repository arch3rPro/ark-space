#!/usr/bin/env python3
"""Tavily web_fetch provider helper for ArkSpace."""

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
        raise ProviderRequestError(f"Tavily Extract HTTP {exc.code}: {body}", status=exc.code) from exc
    except urllib.error.URLError as exc:
        raise ProviderRequestError(f"Tavily Extract request failed: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise ProviderRequestError(f"Tavily Extract returned invalid JSON: {exc}") from exc
    except (TimeoutError, OSError) as exc:
        raise ProviderRequestError(f"Tavily Extract request failed: {exc}") from exc


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
        raise ProviderRequestError(f"Tavily Extract returned invalid JSON: {exc}") from exc
    except (TimeoutError, OSError) as exc:
        raise ProviderRequestError(f"Tavily Extract request failed: {exc}") from exc


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
        resolved = resolve_tavily(capability="web_fetch", config_path=config_path, state_path=state_path)
    except provider_config.ProviderConfigError as exc:
        return {"ok": False, "provider": "tavily", "capability": "web_fetch", "error": str(exc)}
    return {"ok": True, "provider": "tavily", "capability": "web_fetch", **provider_config.public_view(resolved)}


def run_extract(
    urls: list[str],
    *,
    query: str | None = None,
    extract_depth: str | None = None,
    chunks_per_source: int | None = None,
    include_images: bool = False,
    timeout: int = 30,
    config_path: str | None = None,
    state_path: str | None = None,
    post_json: Callable[[str, dict[str, str], dict[str, Any], int], dict[str, Any]] = post_json,
) -> dict[str, Any]:
    resolved = resolve_tavily(capability="web_fetch", config_path=config_path, state_path=state_path)
    endpoint = resolved.get("endpoint") or {"id": "default", "base_url": DEFAULT_BASE_URL}
    api_timeout = max(1, min(60, int(timeout)))
    payload: dict[str, Any] = {"urls": urls, "timeout": api_timeout}
    if query:
        payload["query"] = query
    if extract_depth:
        payload["extract_depth"] = extract_depth
    if chunks_per_source:
        payload["chunks_per_source"] = chunks_per_source
    if include_images:
        payload["include_images"] = True

    try:
        response = safe_post_json(
            post_json,
            endpoint_url(endpoint["base_url"], "/extract"),
            auth_headers(resolved),
            payload,
            api_timeout + 5,
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
                "url": item.get("url") or "",
                "raw_content": item.get("raw_content") or item.get("content") or "",
                "images": item.get("images") or [],
            }
        )
    return {
        "provider": "tavily",
        "capability": "web_fetch",
        "results": results,
        "failed_results": response.get("failed_results") or [],
        "request_id": response.get("request_id"),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract URLs through ArkSpace's Tavily provider.")
    parser.add_argument("urls", nargs="*")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--query")
    parser.add_argument("--extract-depth")
    parser.add_argument("--chunks-per-source", type=int)
    parser.add_argument("--include-images", action="store_true")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--config-path")
    parser.add_argument("--state-path")
    parser.add_argument("--output", choices=["json", "markdown"], default="markdown")
    return parser.parse_args()


def print_markdown(result: dict[str, Any]) -> None:
    if result.get("ok") is False:
        print(f"Tavily Extract is not configured: {result['error']}")
        return
    if result.get("ok") is True:
        print("Tavily web_fetch provider is configured.")
        return
    for item in result.get("results") or []:
        print(f"## {item['url']}")
        print()
        print(item.get("raw_content") or "")
        print()


def main() -> int:
    args = parse_args()
    try:
        if args.check:
            result = check_config(args.config_path, args.state_path)
        else:
            if not args.urls:
                raise provider_config.ProviderConfigError("at least one URL is required")
            result = run_extract(
                args.urls,
                query=args.query,
                extract_depth=args.extract_depth,
                chunks_per_source=args.chunks_per_source,
                include_images=args.include_images,
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
