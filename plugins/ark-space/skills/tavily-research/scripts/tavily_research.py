#!/usr/bin/env python3
"""Tavily research helper for ArkSpace."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Callable

RUNTIME_DIR = Path(__file__).resolve().parents[2] / "provider-manager" / "scripts"
sys.path.insert(0, str(RUNTIME_DIR))

from arkspace_runtime import provider_config, tavily_client


def parse_csv(value: str | None) -> list[str] | None:
    if not value:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def load_schema(path: str | None) -> dict[str, Any] | None:
    if not path:
        return None
    with Path(path).expanduser().open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise provider_config.ProviderConfigError("output schema must be a JSON object")
    return data


def check_config(config_path: str | None = None, state_path: str | None = None) -> dict[str, Any]:
    return tavily_client.check_config("deep_research", config_path, state_path)


def run_research(
    input_text: str,
    *,
    model: str | None = None,
    citation_format: str | None = None,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
    output_length: str | None = None,
    output_schema: dict[str, Any] | None = None,
    wait: bool = False,
    poll_interval: int = 10,
    timeout: int = 600,
    config_path: str | None = None,
    state_path: str | None = None,
    post_json: Callable[[str, dict[str, str], dict[str, Any], int], dict[str, Any]] | None = None,
    get_json: Callable[[str, dict[str, str], int], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    resolved = tavily_client.resolve_tavily(capability="deep_research", config_path=config_path, state_path=state_path)
    endpoint = resolved.get("endpoint") or {"id": "default", "base_url": tavily_client.DEFAULT_BASE_URL}
    payload: dict[str, Any] = {"input": input_text}
    optional_values = {
        "model": model,
        "citation_format": citation_format,
        "include_domains": include_domains,
        "exclude_domains": exclude_domains,
        "output_length": output_length,
        "output_schema": output_schema,
    }
    for key, value in optional_values.items():
        if value:
            payload[key] = value

    try:
        if post_json is None:
            response = tavily_client.post_json(
                tavily_client.endpoint_url(endpoint["base_url"], "/research"),
                tavily_client.auth_headers(resolved),
                payload,
                min(60, max(10, int(timeout))),
                label="Research",
            )
        else:
            response = tavily_client.safe_json_call(
                lambda: post_json(
                    tavily_client.endpoint_url(endpoint["base_url"], "/research"),
                    tavily_client.auth_headers(resolved),
                    payload,
                    min(60, max(10, int(timeout))),
                ),
                label="Research",
            )
        tavily_client.record_success(resolved, config_path=config_path, state_path=state_path)
        if wait and response.get("request_id"):
            return poll_research(
                str(response["request_id"]),
                poll_interval=poll_interval,
                timeout=timeout,
                config_path=config_path,
                state_path=state_path,
                get_json=get_json,
                resolved=resolved,
            )
        return normalize_research_response(response)
    except provider_config.ProviderConfigError as exc:
        tavily_client.record_failure(resolved, exc, config_path=config_path, state_path=state_path)
        raise


def poll_research(
    request_id: str,
    *,
    poll_interval: int = 10,
    timeout: int = 600,
    config_path: str | None = None,
    state_path: str | None = None,
    get_json: Callable[[str, dict[str, str], int], dict[str, Any]] | None = None,
    resolved: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_provider = resolved or tavily_client.resolve_tavily(
        capability="deep_research",
        config_path=config_path,
        state_path=state_path,
    )
    endpoint = resolved_provider.get("endpoint") or {"id": "default", "base_url": tavily_client.DEFAULT_BASE_URL}
    deadline = time.time() + max(1, int(timeout))
    interval = max(1, int(poll_interval))
    while True:
        try:
            if get_json is None:
                response = tavily_client.get_json(
                    tavily_client.endpoint_url(endpoint["base_url"], f"/research/{request_id}"),
                    tavily_client.auth_headers(resolved_provider),
                    min(60, max(10, int(timeout))),
                    label="Research Status",
                )
            else:
                response = tavily_client.safe_json_call(
                    lambda: get_json(
                        tavily_client.endpoint_url(endpoint["base_url"], f"/research/{request_id}"),
                        tavily_client.auth_headers(resolved_provider),
                        min(60, max(10, int(timeout))),
                    ),
                    label="Research Status",
                )
            tavily_client.record_success(resolved_provider, config_path=config_path, state_path=state_path)
        except provider_config.ProviderConfigError as exc:
            tavily_client.record_failure(resolved_provider, exc, config_path=config_path, state_path=state_path)
            raise

        normalized = normalize_research_response(response)
        if normalized.get("status") in {"completed", "failed"}:
            return normalized
        if time.time() + interval > deadline:
            normalized["timed_out"] = True
            return normalized
        time.sleep(interval)


def normalize_research_response(response: dict[str, Any]) -> dict[str, Any]:
    return {
        "provider": "tavily",
        "capability": "deep_research",
        "request_id": response.get("request_id"),
        "created_at": response.get("created_at"),
        "status": response.get("status"),
        "input": response.get("input"),
        "model": response.get("model"),
        "content": response.get("content"),
        "sources": response.get("sources") or [],
        "usage": response.get("usage"),
        "response_time": response.get("response_time"),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Tavily Research through ArkSpace's Tavily provider.")
    parser.add_argument("input", nargs="?")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--status")
    parser.add_argument("--model", choices=["mini", "pro", "auto"])
    parser.add_argument("--citation-format", choices=["numbered", "mla", "apa", "chicago"])
    parser.add_argument("--include-domains")
    parser.add_argument("--exclude-domains")
    parser.add_argument("--output-length", choices=["short", "standard", "long"])
    parser.add_argument("--output-schema")
    parser.add_argument("--wait", action="store_true")
    parser.add_argument("--poll-interval", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--config-path")
    parser.add_argument("--state-path")
    parser.add_argument("--output", choices=["json", "markdown"], default="markdown")
    return parser.parse_args()


def print_markdown(result: dict[str, Any]) -> None:
    if result.get("ok") is False:
        print(f"Tavily Research is not configured: {result['error']}")
        return
    if result.get("ok") is True:
        print("Tavily deep_research provider is configured.")
        return
    if result.get("content"):
        print(result["content"])
        print()
    print(f"request_id: {result.get('request_id')}")
    print(f"status: {result.get('status')}")
    if result.get("sources"):
        print()
        print("Sources:")
        for source in result["sources"]:
            if isinstance(source, dict):
                print(f"- [{source.get('title') or source.get('url')}]({source.get('url')})")
            else:
                print(f"- {source}")


def main() -> int:
    args = parse_args()
    try:
        if args.check:
            result = check_config(args.config_path, args.state_path)
        elif args.status:
            result = poll_research(
                args.status,
                poll_interval=args.poll_interval,
                timeout=args.timeout,
                config_path=args.config_path,
                state_path=args.state_path,
            )
        else:
            if not args.input:
                raise provider_config.ProviderConfigError("research input is required")
            result = run_research(
                args.input,
                model=args.model,
                citation_format=args.citation_format,
                include_domains=parse_csv(args.include_domains),
                exclude_domains=parse_csv(args.exclude_domains),
                output_length=args.output_length,
                output_schema=load_schema(args.output_schema),
                wait=args.wait,
                poll_interval=args.poll_interval,
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
