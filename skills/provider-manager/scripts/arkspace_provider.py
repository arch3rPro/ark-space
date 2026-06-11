#!/usr/bin/env python3
"""Configure and inspect ArkSpace providers without editing config files by hand."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
import termios

from arkspace_runtime.provider_config import (
    ProviderConfigError,
    add_key_ref,
    arkspace_command,
    default_config_path,
    default_secrets_path,
    default_state_path,
    load_config,
    public_view,
    resolve_provider,
    set_secret_value,
    set_provider_endpoint,
)


DEFAULT_CAPABILITIES = {
    "searxng": "web_search",
    "tavily": ["web_search", "web_fetch", "web_map", "web_crawl", "deep_research"],
    "exa": ["web_search", "web_fetch", "deep_research", "code_context", "related_pages"],
    "firecrawl": [
        "web_search",
        "web_fetch",
        "web_map",
        "web_crawl",
        "structured_extract",
        "web_interact",
        "web_monitor",
    ],
}

SETUP_DEFAULTS = {
    "tavily": {
        "base_url": "https://api.tavily.com",
        "capabilities": ["web_search", "web_fetch", "web_map", "web_crawl", "deep_research"],
        "auth_header": "Authorization",
        "auth_prefix": "Bearer ",
    },
    "exa": {
        "base_url": "https://api.exa.ai",
        "capabilities": ["web_search", "web_fetch", "deep_research", "code_context", "related_pages"],
        "auth_header": "x-api-key",
        "auth_prefix": "",
    },
    "firecrawl": {
        "base_url": "https://api.firecrawl.dev",
        "capabilities": [
            "web_search",
            "web_fetch",
            "web_map",
            "web_crawl",
            "structured_extract",
            "web_interact",
            "web_monitor",
        ],
        "auth_header": "Authorization",
        "auth_prefix": "Bearer ",
    }
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage ArkSpace provider configuration.")
    parser.add_argument("--config-path", help="Override provider config path")
    parser.add_argument("--state-path", help="Override provider state path")
    subparsers = parser.add_subparsers(dest="command", required=True)

    configure = subparsers.add_parser("configure", help="Configure a provider endpoint")
    configure.add_argument("provider")
    configure.add_argument("--base-url", required=True)
    configure.add_argument("--endpoint-id", default="default")
    configure.add_argument("--capability")

    add_key = subparsers.add_parser("add-key", help="Add an environment-backed API key reference")
    add_key.add_argument("provider")
    add_key.add_argument("--env", required=True, help="Environment variable name that contains the key")
    add_key.add_argument("--header", help="HTTP header used by this provider")
    add_key.add_argument("--prefix", help="Prefix prepended to the secret value in the auth header")

    setup = subparsers.add_parser("setup", help="Set up a provider with sensible defaults")
    setup.add_argument("provider")
    setup.add_argument("--base-url", help="Provider base URL; defaults by provider when available")
    setup.add_argument(
        "--env",
        action="append",
        default=[],
        help="Environment variable name containing an API key; repeat or comma-separate for rotation",
    )
    setup.add_argument(
        "--save-secret",
        action="append",
        default=[],
        help="Environment variable name to reference and save in ArkSpace's private secret store",
    )
    setup.add_argument("--wizard", action="store_true", help="Prompt for a default provider setup without manual env names")
    setup.add_argument("--key-count", type=int, default=1, help="Number of API keys to collect in --wizard mode")
    setup.add_argument("--prompt", action="store_true", help="Prompt securely for each --save-secret value")
    setup.add_argument("--secret-stdin", action="store_true", help="Read one secret value per --save-secret from stdin")
    setup.add_argument("--check", action="store_true", help="Run provider resolution after writing setup")

    resolve = subparsers.add_parser("resolve", help="Resolve a configured provider")
    resolve.add_argument("provider")
    resolve.add_argument("--capability")
    resolve.add_argument("--require-secret", action="store_true")

    subparsers.add_parser("show", help="Print provider config with secret values omitted")
    subparsers.add_parser("paths", help="Print resolved config and state paths")
    return parser.parse_args()


def command_configure(args: argparse.Namespace) -> int:
    default_capability = DEFAULT_CAPABILITIES.get(args.provider) or "web_search"
    capabilities = default_capability if isinstance(default_capability, list) and not args.capability else None
    capability = args.capability or (default_capability[0] if isinstance(default_capability, list) else default_capability)
    path = set_provider_endpoint(
        args.provider,
        capability=capability,
        capabilities=capabilities,
        base_url=args.base_url,
        endpoint_id=args.endpoint_id,
        config_path=args.config_path,
    )
    print(f"configured provider {args.provider} endpoint {args.endpoint_id} in {path}")
    return 0


def command_add_key(args: argparse.Namespace) -> int:
    path = add_key_ref(
        args.provider,
        key_ref=f"env:{args.env}",
        auth_header=args.header,
        auth_prefix=args.prefix,
        config_path=args.config_path,
    )
    print(f"added key reference env:{args.env} for provider {args.provider} in {path}")
    return 0


def normalize_env_names(values: list[str]) -> list[str]:
    names: list[str] = []
    for value in values:
        for item in value.split(","):
            name = item.strip()
            if name and name not in names:
                names.append(name)
    return names


def collect_secret_values(names: list[str], args: argparse.Namespace) -> dict[str, str]:
    if not names:
        return {}
    if getattr(args, "prompt", False) and getattr(args, "secret_stdin", False):
        raise ProviderConfigError("use either --prompt or --secret-stdin, not both")
    if getattr(args, "secret_stdin", False):
        lines = [line.rstrip("\n") for line in sys.stdin.readlines()]
        if len(lines) < len(names):
            raise ProviderConfigError(f"expected {len(names)} secret values on stdin, got {len(lines)}")
        return {name: lines[index] for index, name in enumerate(names)}
    if getattr(args, "prompt", False):
        if not can_collect_interactive_secret():
            raise ProviderConfigError(
                "interactive secret input requires a TTY; run the wizard in an interactive terminal "
                "or use --secret-stdin"
            )
        try:
            return {name: getpass.getpass(f"{name}: ") for name in names}
        except EOFError as exc:
            raise ProviderConfigError(
                "interactive secret input ended before a key was entered; run the wizard in an interactive terminal "
                "or use --secret-stdin"
            ) from exc
    raise ProviderConfigError("use --prompt or --secret-stdin with --save-secret")


def can_collect_interactive_secret() -> bool:
    try:
        fd = sys.stdin.fileno()
    except (AttributeError, OSError):
        return False
    if not os.isatty(fd):
        return False
    try:
        termios.tcgetattr(fd)
    except termios.error:
        return False
    return True


def wizard_secret_names(provider: str, key_count: int) -> list[str]:
    if provider not in {"tavily", "exa", "firecrawl"}:
        raise ProviderConfigError(f"provider {provider} does not have a setup wizard")
    if key_count < 1:
        raise ProviderConfigError("--key-count must be at least 1")
    prefixes = {
        "exa": "EXA_API_KEY",
        "firecrawl": "FIRECRAWL_API_KEY",
        "tavily": "TAVILY_API_KEY",
    }
    prefix = prefixes[provider]
    if key_count == 1:
        return [prefix]
    return [f"{prefix}_{index}" for index in range(1, key_count + 1)]


def command_setup(args: argparse.Namespace) -> int:
    defaults = SETUP_DEFAULTS.get(args.provider)
    if not defaults:
        raise ProviderConfigError(f"provider {args.provider} does not have setup defaults")

    save_secret_values = getattr(args, "save_secret", []) or []
    if getattr(args, "wizard", False):
        if args.env or save_secret_values:
            raise ProviderConfigError("do not combine --wizard with --env or --save-secret")
        save_secret_values = wizard_secret_names(args.provider, args.key_count)
        if not args.secret_stdin:
            args.prompt = True

    secret_names = normalize_env_names(save_secret_values)
    env_names = normalize_env_names((args.env or []) + secret_names)
    secret_values = collect_secret_values(secret_names, args)

    capabilities = list(defaults["capabilities"])
    base_url = args.base_url or defaults["base_url"]
    path = set_provider_endpoint(
        args.provider,
        capability=capabilities[0],
        capabilities=capabilities,
        base_url=base_url,
        endpoint_id="default",
        config_path=args.config_path,
    )
    print(f"configured provider {args.provider} endpoint default in {path}")

    for env_name in env_names:
        path = add_key_ref(
            args.provider,
            key_ref=f"env:{env_name}",
            auth_header=defaults["auth_header"],
            auth_prefix=defaults["auth_prefix"],
            config_path=args.config_path,
        )
        print(f"added key reference env:{env_name} for provider {args.provider} in {path}")

    for env_name, value in secret_values.items():
        path = set_secret_value(env_name, value)
        print(f"saved secret env:{env_name} for provider {args.provider} in {path}")

    if not env_names:
        default_keys = {
            "exa": "EXA_API_KEY",
            "firecrawl": "FIRECRAWL_API_KEY",
            "tavily": "TAVILY_API_KEY",
        }
        default_key = default_keys.get(args.provider, f"{args.provider.upper()}_API_KEY")
        print(
            "Next: add and save an API key with "
            f"`{arkspace_command()} provider setup {args.provider} --save-secret {default_key} --prompt`"
        )

    if args.check:
        resolved = resolve_provider(
            args.provider,
            capability=capabilities[0],
            config_path=args.config_path,
            state_path=args.state_path,
            require_secret=True,
        )
        print(json.dumps(public_view(resolved), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def command_resolve(args: argparse.Namespace) -> int:
    resolved = resolve_provider(
        args.provider,
        capability=args.capability,
        config_path=args.config_path,
        state_path=args.state_path,
        require_secret=args.require_secret,
    )
    print(json.dumps(public_view(resolved), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def command_show(args: argparse.Namespace) -> int:
    data = load_config(args.config_path)
    print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def command_paths(args: argparse.Namespace) -> int:
    print(
        json.dumps(
            {
                "config_path": str(default_config_path(args.config_path)),
                "state_path": str(default_state_path(args.state_path)),
                "secrets_path": str(default_secrets_path()),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def main() -> int:
    args = parse_args()
    try:
        if args.command == "configure":
            return command_configure(args)
        if args.command == "add-key":
            return command_add_key(args)
        if args.command == "setup":
            return command_setup(args)
        if args.command == "resolve":
            return command_resolve(args)
        if args.command == "show":
            return command_show(args)
        if args.command == "paths":
            return command_paths(args)
    except ProviderConfigError as exc:
        print(f"provider configuration error: {exc}", file=sys.stderr)
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
