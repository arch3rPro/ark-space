#!/usr/bin/env python3
"""Firecrawl CLI browser provider helper for ArkSpace."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

RUNTIME_DIR = Path(__file__).resolve().parents[2] / "provider-manager" / "scripts"
sys.path.insert(0, str(RUNTIME_DIR))

from arkspace_runtime import firecrawl_cli, provider_config  # noqa: E402  # type: ignore[reportMissingImports]


def check_config(config_path: str | None = None, state_path: str | None = None) -> dict[str, Any]:
    return firecrawl_cli.check_config("web_interact", config_path, state_path)


def run_browser(
    instruction: str,
    *,
    profile: str | None = None,
    save_changes: bool = True,
    timeout: int = 180,
    config_path: str | None = None,
    state_path: str | None = None,
) -> dict[str, Any]:
    command = ["browser", instruction, "--json"]
    if profile:
        command.extend(["--profile", profile])
    if not save_changes:
        command.append("--no-save-changes")
    response = firecrawl_cli.run_capability_command(
        "web_interact", command, timeout=timeout, config_path=config_path, state_path=state_path
    )
    return {
        "provider": "firecrawl",
        "capability": "web_interact",
        "mode": "browser",
        "instruction": instruction,
        "response": response,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Firecrawl Browser through ArkSpace web_interact routing.")
    parser.add_argument("instruction", nargs="?")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--profile")
    parser.add_argument("--no-save-changes", action="store_true")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--config-path")
    parser.add_argument("--state-path")
    parser.add_argument("--output", choices=["json", "markdown"], default="markdown")
    return parser.parse_args()


def print_markdown(result: dict[str, Any]) -> None:
    if result.get("ok") is False:
        print(f"Firecrawl Browser is not configured: {result['error']}")
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
        else:
            if not args.instruction:
                raise provider_config.ProviderConfigError("instruction is required")
            result = run_browser(
                args.instruction,
                profile=args.profile,
                save_changes=not args.no_save_changes,
                timeout=args.timeout,
                config_path=args.config_path,
                state_path=args.state_path,
            )
    except provider_config.ProviderConfigError as exc:
        kind, status = firecrawl_cli.classify_exception(exc)
        provider_config.write_error_file(
            "firecrawl", "web_interact", kind=kind, status=status, message=str(exc)
        )
        print(provider_config.safe_message(str(exc)), file=sys.stderr)
        return 2
    if args.output == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_markdown(result)
    return 0 if result.get("ok", True) else 2


if __name__ == "__main__":
    raise SystemExit(main())
