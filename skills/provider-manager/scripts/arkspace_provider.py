#!/usr/bin/env python3
"""Configure and inspect ArkSpace providers without editing config files by hand."""

from __future__ import annotations

import argparse
import json
import sys

from arkspace_runtime.provider_config import (
    ProviderConfigError,
    add_key_ref,
    default_config_path,
    default_state_path,
    load_config,
    public_view,
    resolve_provider,
    set_provider_endpoint,
)


DEFAULT_CAPABILITIES = {
    "searxng": "web_search",
    "tavily": ["web_search", "web_fetch"],
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
