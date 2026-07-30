#!/usr/bin/env python3
"""Firecrawl CLI scrape-bound interact helper for ArkSpace."""

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
    return firecrawl_cli.check_config("web_interact", config_path, state_path)


def run_interact(
    *,
    scrape_id: str | None = None,
    prompt: str | None = None,
    code: str | None = None,
    language: str | None = None,
    interaction_timeout: int | None = None,
    timeout: int = 180,
    config_path: str | None = None,
    state_path: str | None = None,
) -> dict[str, Any]:
    if bool(prompt) == bool(code):
        raise provider_config.ProviderConfigError("provide exactly one of --prompt or --code")
    resolved = firecrawl_cli.resolve_firecrawl(capability="web_interact", config_path=config_path, state_path=state_path)
    command = ["interact", "--json"]
    if scrape_id:
        command.extend(["--scrape-id", scrape_id])
    if prompt:
        command.extend(["--prompt", prompt])
    if code:
        command.extend(["--code", code])
    if language:
        command.append(f"--{language}")
    if interaction_timeout is not None:
        command.extend(["--timeout", str(interaction_timeout)])
    raw = firecrawl_cli.run_cli(resolved, command, timeout=timeout, config_path=config_path, state_path=state_path)
    return {
        "provider": "firecrawl",
        "capability": "web_interact",
        "mode": "interact",
        "scrape_id": scrape_id,
        "response": firecrawl_cli.parse_json_or_text(raw),
    }


def stop_interact(
    *,
    scrape_id: str | None = None,
    timeout: int = 60,
    config_path: str | None = None,
    state_path: str | None = None,
) -> dict[str, Any]:
    resolved = firecrawl_cli.resolve_firecrawl(capability="web_interact", config_path=config_path, state_path=state_path)
    command = ["interact", "stop", "--json"]
    if scrape_id:
        command.append(scrape_id)
    raw = firecrawl_cli.run_cli(resolved, command, timeout=timeout, config_path=config_path, state_path=state_path)
    return {
        "provider": "firecrawl",
        "capability": "web_interact",
        "mode": "interact_stop",
        "scrape_id": scrape_id,
        "response": firecrawl_cli.parse_json_or_text(raw),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Firecrawl Interact through ArkSpace web_interact routing.")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--stop", action="store_true")
    parser.add_argument("--scrape-id")
    parser.add_argument("--prompt")
    parser.add_argument("--code")
    parser.add_argument("--language", choices=["node", "python", "bash"])
    parser.add_argument("--interaction-timeout", type=int)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--config-path")
    parser.add_argument("--state-path")
    parser.add_argument("--output", choices=["json", "markdown"], default="markdown")
    return parser.parse_args()


def print_markdown(result: dict[str, Any]) -> None:
    if result.get("ok") is False:
        print(f"Firecrawl Interact is not configured: {result['error']}")
        return
    if result.get("ok") is True:
        print("Firecrawl web_interact provider is configured.")
        return
    print(json.dumps(result.get("response"), ensure_ascii=False, indent=2))


def main() -> int:
    args = parse_args()
    try:
        if args.check:
            result = check_config(args.config_path, args.state_path)
        elif args.stop:
            result = stop_interact(
                scrape_id=args.scrape_id,
                timeout=args.timeout,
                config_path=args.config_path,
                state_path=args.state_path,
            )
        else:
            result = run_interact(
                scrape_id=args.scrape_id,
                prompt=args.prompt,
                code=args.code,
                language=args.language,
                interaction_timeout=args.interaction_timeout,
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
