#!/usr/bin/env python3
"""Firecrawl CLI structured_extract provider helper for ArkSpace."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

RUNTIME_DIR = Path(__file__).resolve().parents[2] / "provider-manager" / "scripts"
sys.path.insert(0, str(RUNTIME_DIR))

from arkspace_runtime import firecrawl_cli, provider_config


def check_config(config_path: str | None = None, state_path: str | None = None) -> dict[str, Any]:
    return firecrawl_cli.check_config("structured_extract", config_path, state_path)


def run_agent(
    prompt: str,
    *,
    urls: str | None = None,
    schema: str | None = None,
    schema_file: str | None = None,
    model: str | None = None,
    max_credits: int | None = None,
    webhook: str | None = None,
    status: bool = False,
    cancel: bool = False,
    wait: bool = False,
    poll_interval: float | None = None,
    timeout: float | None = None,
    run_timeout: int = 300,
    config_path: str | None = None,
    state_path: str | None = None,
) -> dict[str, Any]:
    resolved = firecrawl_cli.resolve_firecrawl(
        capability="structured_extract",
        config_path=config_path,
        state_path=state_path,
    )
    command = ["agent", prompt, "--json"]
    for name, value in [
        ("urls", urls),
        ("schema", schema),
        ("schema-file", schema_file),
        ("model", model),
        ("max-credits", max_credits),
        ("webhook", webhook),
        ("poll-interval", poll_interval),
        ("timeout", timeout),
    ]:
        if value is not None:
            command.extend([f"--{name}", str(value)])
    for flag, enabled in [("status", status), ("cancel", cancel), ("wait", wait)]:
        if enabled:
            command.append(f"--{flag}")
    raw = firecrawl_cli.run_cli(
        resolved,
        command,
        timeout=run_timeout,
        config_path=config_path,
        state_path=state_path,
    )
    return {
        "provider": "firecrawl",
        "capability": "structured_extract",
        "prompt": prompt,
        "response": firecrawl_cli.parse_json_or_text(raw),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Firecrawl Agent through ArkSpace structured_extract routing.")
    parser.add_argument("prompt", nargs="?")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--urls")
    parser.add_argument("--schema")
    parser.add_argument("--schema-file")
    parser.add_argument("--model", choices=["spark-1-mini", "spark-1-pro"])
    parser.add_argument("--max-credits", type=int)
    parser.add_argument("--webhook")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--cancel", action="store_true")
    parser.add_argument("--wait", action="store_true")
    parser.add_argument("--poll-interval", type=float)
    parser.add_argument("--timeout", type=float)
    parser.add_argument("--run-timeout", type=int, default=300)
    parser.add_argument("--config-path")
    parser.add_argument("--state-path")
    parser.add_argument("--output", choices=["json", "markdown"], default="markdown")
    return parser.parse_args()


def print_markdown(result: dict[str, Any]) -> None:
    if result.get("ok") is False:
        print(f"Firecrawl Agent is not configured: {result['error']}")
        return
    if result.get("ok") is True:
        print("Firecrawl structured_extract provider is configured.")
        return
    print(json.dumps(result.get("response"), ensure_ascii=False, indent=2))


def main() -> int:
    args = parse_args()
    try:
        if args.check:
            result = check_config(args.config_path, args.state_path)
        else:
            if not args.prompt:
                raise provider_config.ProviderConfigError("prompt is required")
            result = run_agent(
                args.prompt,
                urls=args.urls,
                schema=args.schema,
                schema_file=args.schema_file,
                model=args.model,
                max_credits=args.max_credits,
                webhook=args.webhook,
                status=args.status,
                cancel=args.cancel,
                wait=args.wait,
                poll_interval=args.poll_interval,
                timeout=args.timeout,
                run_timeout=args.run_timeout,
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
