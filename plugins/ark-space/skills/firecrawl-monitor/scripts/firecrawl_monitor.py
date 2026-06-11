#!/usr/bin/env python3
"""Firecrawl CLI web_monitor provider helper for ArkSpace."""

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
    return firecrawl_cli.check_config("web_monitor", config_path, state_path)


def run_monitor(args: argparse.Namespace) -> dict[str, Any]:
    resolved = firecrawl_cli.resolve_firecrawl(
        capability="web_monitor",
        config_path=args.config_path,
        state_path=args.state_path,
    )
    command = ["monitor", args.monitor_action]
    for value in [args.monitor_id, args.check_id, args.file]:
        if value:
            command.append(value)
    for name in [
        "name",
        "cron",
        "schedule",
        "timezone",
        "page",
        "scrape_urls",
        "crawl_url",
        "webhook_url",
        "webhook_events",
        "email",
        "retention_days",
        "goal",
        "state",
        "limit",
        "offset",
        "skip",
        "page_status",
    ]:
        value = getattr(args, name)
        if value is not None:
            command.extend([f"--{name.replace('_', '-')}", str(value)])
    if args.pretty:
        command.append("--pretty")
    raw = firecrawl_cli.run_cli(
        resolved,
        command,
        timeout=args.timeout,
        config_path=args.config_path,
        state_path=args.state_path,
    )
    return {
        "provider": "firecrawl",
        "capability": "web_monitor",
        "action": args.monitor_action,
        "response": firecrawl_cli.parse_json_or_text(raw),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage Firecrawl Monitor through ArkSpace web_monitor routing.")
    parser.add_argument("monitor_action", nargs="?", choices=["create", "list", "get", "update", "delete", "run", "checks", "check"])
    parser.add_argument("monitor_id", nargs="?")
    parser.add_argument("check_id", nargs="?")
    parser.add_argument("file", nargs="?")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--name")
    parser.add_argument("--cron")
    parser.add_argument("--schedule")
    parser.add_argument("--timezone")
    parser.add_argument("--page")
    parser.add_argument("--scrape-urls")
    parser.add_argument("--crawl-url")
    parser.add_argument("--webhook-url")
    parser.add_argument("--webhook-events")
    parser.add_argument("--email")
    parser.add_argument("--retention-days", type=int)
    parser.add_argument("--goal")
    parser.add_argument("--state")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--offset", type=int)
    parser.add_argument("--skip", type=int)
    parser.add_argument("--page-status")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--config-path")
    parser.add_argument("--state-path")
    parser.add_argument("--output", choices=["json", "markdown"], default="markdown")
    return parser.parse_args()


def print_markdown(result: dict[str, Any]) -> None:
    if result.get("ok") is False:
        print(f"Firecrawl Monitor is not configured: {result['error']}")
        return
    if result.get("ok") is True:
        print("Firecrawl web_monitor provider is configured.")
        return
    print(json.dumps(result.get("response"), ensure_ascii=False, indent=2))


def main() -> int:
    args = parse_args()
    try:
        if args.check:
            result = check_config(args.config_path, args.state_path)
        else:
            if not args.monitor_action:
                raise provider_config.ProviderConfigError("monitor action is required")
            result = run_monitor(args)
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
