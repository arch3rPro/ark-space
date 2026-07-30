#!/usr/bin/env python3
"""Exa answer helper for ArkSpace."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

RUNTIME_DIR = Path(__file__).resolve().parents[2] / "provider-manager" / "scripts"
sys.path.insert(0, str(RUNTIME_DIR))

from arkspace_runtime import exa_client, provider_config


def check_config(config_path: str | None = None, state_path: str | None = None) -> dict[str, Any]:
    return exa_client.check_config("deep_research", config_path, state_path)


def run_answer(
    query: str,
    *,
    timeout: int = 60,
    config_path: str | None = None,
    state_path: str | None = None,
    post_json: Callable[[str, dict[str, str], dict[str, Any], int], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    resolved = exa_client.resolve_exa(capability="deep_research", config_path=config_path, state_path=state_path)
    endpoint = resolved.get("endpoint") or {"id": "default", "base_url": exa_client.DEFAULT_BASE_URL}
    payload: dict[str, Any] = {"query": query}

    try:
        if post_json is None:
            response = exa_client.post_json(
                exa_client.endpoint_url(endpoint["base_url"], "/answer"),
                exa_client.auth_headers(resolved),
                payload,
                timeout,
                label="Answer",
            )
        else:
            response = exa_client.safe_json_call(
                lambda: post_json(
                    exa_client.endpoint_url(endpoint["base_url"], "/answer"),
                    exa_client.auth_headers(resolved),
                    payload,
                    timeout,
                ),
                label="Answer",
            )
        exa_client.record_success(resolved, config_path=config_path, state_path=state_path)
    except provider_config.ProviderConfigError as exc:
        exa_client.record_failure(resolved, exc, config_path=config_path, state_path=state_path)
        raise

    return {
        "provider": "exa",
        "capability": "deep_research",
        "query": query,
        "answer": response.get("answer") or response.get("text") or response.get("content") or "",
        "sources": response.get("sources") or response.get("citations") or [],
        "request_id": response.get("requestId") or response.get("request_id"),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Answer through ArkSpace's Exa provider.")
    parser.add_argument("query", nargs="?")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--config-path")
    parser.add_argument("--state-path")
    parser.add_argument("--output", choices=["json", "markdown"], default="markdown")
    return parser.parse_args()


def print_markdown(result: dict[str, Any]) -> None:
    if result.get("ok") is False:
        print(f"Exa Answer is not configured: {result['error']}")
        return
    if result.get("ok") is True:
        print("Exa deep_research provider is configured.")
        return
    print(result.get("answer") or "")
    if result.get("sources"):
        print()
        print("Sources:")
        for source in result["sources"]:
            if isinstance(source, dict):
                title = source.get("title") or source.get("url") or "Source"
                url = source.get("url") or ""
                print(f"- [{title}]({url})" if url else f"- {title}")
            else:
                print(f"- {source}")


def main() -> int:
    args = parse_args()
    try:
        if args.check:
            result = check_config(args.config_path, args.state_path)
        else:
            if not args.query:
                raise provider_config.ProviderConfigError("query is required")
            result = run_answer(
                args.query,
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
