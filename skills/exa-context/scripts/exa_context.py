#!/usr/bin/env python3
"""Exa code_context provider helper for ArkSpace."""

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
    return exa_client.check_config("code_context", config_path, state_path)


def run_context(
    query: str,
    *,
    tokens: str | int = "dynamic",
    timeout: int = 60,
    config_path: str | None = None,
    state_path: str | None = None,
    post_json: Callable[[str, dict[str, str], dict[str, Any], int], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    resolved = exa_client.resolve_exa(capability="code_context", config_path=config_path, state_path=state_path)
    endpoint = resolved.get("endpoint") or {"id": "default", "base_url": exa_client.DEFAULT_BASE_URL}
    payload: dict[str, Any] = {"query": query, "tokensNum": tokens}

    try:
        if post_json is None:
            response = exa_client.post_json(
                exa_client.endpoint_url(endpoint["base_url"], "/context"),
                exa_client.auth_headers(resolved),
                payload,
                timeout,
                label="Context",
            )
        else:
            response = exa_client.safe_json_call(
                lambda: post_json(
                    exa_client.endpoint_url(endpoint["base_url"], "/context"),
                    exa_client.auth_headers(resolved),
                    payload,
                    timeout,
                ),
                label="Context",
            )
        exa_client.record_success(resolved, config_path=config_path, state_path=state_path)
    except provider_config.ProviderConfigError as exc:
        exa_client.record_failure(resolved, exc, config_path=config_path, state_path=state_path)
        raise

    return {
        "provider": "exa",
        "capability": "code_context",
        "query": response.get("query") or query,
        "response": response.get("response") or "",
        "results_count": response.get("resultsCount"),
        "cost_dollars": response.get("costDollars"),
        "search_time": response.get("searchTime"),
        "output_tokens": response.get("outputTokens"),
        "request_id": response.get("requestId") or response.get("request_id"),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Get coding context through ArkSpace's Exa provider.")
    parser.add_argument("query", nargs="?")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--tokens", default="dynamic")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--config-path")
    parser.add_argument("--state-path")
    parser.add_argument("--output", choices=["json", "markdown"], default="markdown")
    return parser.parse_args()


def print_markdown(result: dict[str, Any]) -> None:
    if result.get("ok") is False:
        print(f"Exa Context is not configured: {result['error']}")
        return
    if result.get("ok") is True:
        print("Exa code_context provider is configured.")
        return
    print(result.get("response") or "")


def main() -> int:
    args = parse_args()
    try:
        if args.check:
            result = check_config(args.config_path, args.state_path)
        else:
            if not args.query:
                raise provider_config.ProviderConfigError("query is required")
            result = run_context(
                args.query,
                tokens=args.tokens,
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
