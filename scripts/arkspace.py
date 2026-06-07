#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PROVIDER_CHECK_COMMANDS = {
    ("searxng", "web_search"): [sys.executable, "skills/searxng-search/scripts/searxng_search.py", "--check"],
    ("tavily", "web_search"): [sys.executable, "skills/tavily-search/scripts/tavily_search.py", "--check"],
    ("tavily", "web_fetch"): [sys.executable, "skills/tavily-extract/scripts/tavily_extract.py", "--check"],
}

WEB_SEARCH_COMMANDS = {
    "searxng": [sys.executable, "skills/searxng-search/scripts/searxng_search.py"],
    "tavily": [sys.executable, "skills/tavily-search/scripts/tavily_search.py"],
}

WEB_FETCH_COMMANDS = {
    "tavily": [sys.executable, "skills/tavily-extract/scripts/tavily_extract.py"],
}


class CliError(ValueError):
    pass


def run(args):
    return subprocess.call(args, cwd=ROOT)


def run_gate(label, args):
    print(f"[arkspace doctor] {label}")
    return run(args)


def main():
    parser = argparse.ArgumentParser(prog="arkspace")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("validate")
    sub.add_parser("package-codex")

    provider = sub.add_parser("provider")
    provider_sub = provider.add_subparsers(dest="provider_command", required=True)
    provider_configure = provider_sub.add_parser("configure")
    provider_configure.add_argument("provider")
    provider_configure.add_argument("--base-url", required=True)
    provider_configure.add_argument("--endpoint-id")
    provider_configure.add_argument("--capability")
    provider_configure.add_argument("--config-path")
    provider_configure.add_argument("--state-path")

    provider_add_key = provider_sub.add_parser("add-key")
    provider_add_key.add_argument("provider")
    provider_add_key.add_argument("--env", required=True)
    provider_add_key.add_argument("--header")
    provider_add_key.add_argument("--prefix")
    provider_add_key.add_argument("--config-path")
    provider_add_key.add_argument("--state-path")

    provider_resolve = provider_sub.add_parser("resolve")
    provider_resolve.add_argument("provider")
    provider_resolve.add_argument("--capability")
    provider_resolve.add_argument("--require-secret", action="store_true")
    provider_resolve.add_argument("--config-path")
    provider_resolve.add_argument("--state-path")

    provider_check = provider_sub.add_parser("check")
    provider_check.add_argument("provider")
    provider_check.add_argument("--capability", default="web_search")
    provider_check.add_argument("--config-path")
    provider_check.add_argument("--state-path")

    provider_show = provider_sub.add_parser("show")
    provider_show.add_argument("--config-path")
    provider_show.add_argument("--state-path")
    provider_paths = provider_sub.add_parser("paths")
    provider_paths.add_argument("--config-path")
    provider_paths.add_argument("--state-path")

    web = sub.add_parser("web")
    web_sub = web.add_subparsers(dest="web_command", required=True)
    web_search = web_sub.add_parser("search")
    web_search.add_argument("query")
    web_search.add_argument("--provider", required=True, choices=sorted(WEB_SEARCH_COMMANDS))
    web_search.add_argument("--max-results")
    web_search.add_argument("--search-depth")
    web_search.add_argument("--topic")
    web_search.add_argument("--time-range")
    web_search.add_argument("--include-domains")
    web_search.add_argument("--exclude-domains")
    web_search.add_argument("--include-answer", action="store_true")
    web_search.add_argument("--base-url")
    web_search.add_argument("--config-path")
    web_search.add_argument("--state-path")
    web_search.add_argument("--timeout")
    web_search.add_argument("--output", choices=["json", "markdown"])

    web_fetch = web_sub.add_parser("fetch")
    web_fetch.add_argument("urls", nargs="+")
    web_fetch.add_argument("--provider", required=True, choices=sorted(WEB_FETCH_COMMANDS))
    web_fetch.add_argument("--query")
    web_fetch.add_argument("--extract-depth")
    web_fetch.add_argument("--chunks-per-source")
    web_fetch.add_argument("--include-images", action="store_true")
    web_fetch.add_argument("--timeout")
    web_fetch.add_argument("--config-path")
    web_fetch.add_argument("--state-path")
    web_fetch.add_argument("--output", choices=["json", "markdown"])

    convert = sub.add_parser("convert")
    convert.add_argument("--host", choices=["codex", "claude-code", "all"], default="all")
    convert.add_argument("--check", action="store_true")

    install = sub.add_parser("install")
    install.add_argument("--host", choices=["codex", "claude-code"], required=True)
    install.add_argument("--agents")
    install.add_argument("--path")
    install.add_argument("--link", action="store_true")
    install.add_argument("--dry-run", action="store_true")

    smoke = sub.add_parser("smoke-test")
    smoke.add_argument("--host", choices=["codex", "claude-code"])
    smoke.add_argument("--local", action="store_true")
    smoke.add_argument("--routing", action="store_true")
    smoke.add_argument("--live-codex", action="store_true")

    sub.add_parser("doctor")

    args = parser.parse_args()
    if args.command == "validate":
        return run([sys.executable, "scripts/validate-skills.py"])
    if args.command == "package-codex":
        return run([sys.executable, "scripts/package-codex-plugin.py"])
    if args.command == "provider":
        return run_or_cli_error(provider_command, args)
    if args.command == "web":
        return run_or_cli_error(web_command, args)
    if args.command == "convert":
        cmd = [sys.executable, "scripts/convert-agents.py", "--host", args.host]
        if args.check:
            cmd.append("--check")
        return run(cmd)
    if args.command == "install":
        cmd = [sys.executable, "scripts/install.py", "--host", args.host]
        for flag in ("agents", "path"):
            value = getattr(args, flag)
            if value:
                cmd.extend([f"--{flag}", value])
        if args.link:
            cmd.append("--link")
        if args.dry_run:
            cmd.append("--dry-run")
        return run(cmd)
    if args.command == "smoke-test":
        if args.routing:
            cmd = [sys.executable, "scripts/smoke-test-orchestrator-routing.py"]
            if args.live_codex:
                cmd.append("--live-codex")
            return run(cmd)
        if not args.host:
            parser.error("smoke-test requires --host unless --routing is used")
        cmd = [sys.executable, "scripts/smoke-test-callability.py", "--host", args.host]
        if args.local:
            cmd.append("--local")
        return run(cmd)
    if args.command == "doctor":
        status = 0
        status |= run_gate("structure: unit tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests"])
        status |= run_gate("package: codex mirror", [sys.executable, "scripts/package-codex-plugin.py", "--check"])
        status |= run_gate("registry/docs: skill contract", [sys.executable, "scripts/validate-skills.py"])
        status |= run_gate("integrations: generated agents", [sys.executable, "scripts/convert-agents.py", "--host", "all", "--check"])
        status |= run_gate(
            "direct-invocation-contract: codex",
            [sys.executable, "scripts/smoke-test-callability.py", "--host", "codex", "--local"],
        )
        status |= run_gate(
            "direct-invocation-contract: claude-code",
            [sys.executable, "scripts/smoke-test-callability.py", "--host", "claude-code", "--local"],
        )
        status |= run_gate("orchestrator-routing-contract: static", [sys.executable, "scripts/smoke-test-orchestrator-routing.py"])
        print("[arkspace doctor] installed-host: unverified")
        return status
    return 2


def provider_command(args):
    if args.provider_command == "check":
        capability = args.capability or "web_search"
        command = PROVIDER_CHECK_COMMANDS.get((args.provider, capability))
        if not command:
            raise CliError(f"provider {args.provider} does not have a {capability} check")
        return append_path_flags([*command], args, include_state=args.provider == "tavily")

    cmd = [sys.executable, "scripts/arkspace_provider.py"]
    cmd = append_path_flags(cmd, args, include_state=True)
    cmd.append(args.provider_command)
    if args.provider_command in {"configure", "add-key", "resolve"}:
        cmd.append(args.provider)
    if args.provider_command == "configure":
        cmd.extend(["--base-url", args.base_url])
        if args.endpoint_id:
            cmd.extend(["--endpoint-id", args.endpoint_id])
        if args.capability:
            cmd.extend(["--capability", args.capability])
    if args.provider_command == "add-key":
        cmd.extend(["--env", args.env])
        if args.header:
            cmd.extend(["--header", args.header])
        if args.prefix:
            cmd.extend(["--prefix", args.prefix])
    if args.provider_command == "resolve":
        if args.capability:
            cmd.extend(["--capability", args.capability])
        if args.require_secret:
            cmd.append("--require-secret")
    return cmd


def web_command(args):
    if args.web_command == "search":
        cmd = [*WEB_SEARCH_COMMANDS[args.provider], args.query]
        if args.provider == "searxng":
            if args.search_depth or args.topic or args.include_domains or args.exclude_domains or args.include_answer:
                raise CliError("searxng web search does not support Tavily-specific search options")
            cmd = append_value_flags(cmd, args, ["base_url", "time_range", "config_path", "timeout", "output"])
            if args.max_results:
                cmd.extend(["--limit", args.max_results])
            return cmd
        if args.base_url:
            raise CliError("tavily web search does not accept --base-url; configure the endpoint with provider configure")
        for name in ["max_results", "search_depth", "topic", "time_range", "include_domains", "exclude_domains", "timeout", "config_path", "state_path", "output"]:
            value = getattr(args, name)
            if value:
                cmd.extend([f"--{name.replace('_', '-')}", value])
        if args.include_answer:
            cmd.append("--include-answer")
        return cmd

    if args.web_command == "fetch":
        cmd = [*WEB_FETCH_COMMANDS[args.provider], *args.urls]
        for name in ["query", "extract_depth", "chunks_per_source", "timeout", "config_path", "state_path", "output"]:
            value = getattr(args, name)
            if value:
                cmd.extend([f"--{name.replace('_', '-')}", value])
        if args.include_images:
            cmd.append("--include-images")
        return cmd

    raise ValueError(f"unknown web command {args.web_command}")


def append_value_flags(cmd, args, names):
    for name in names:
        value = getattr(args, name)
        if value:
            cmd.extend([f"--{name.replace('_', '-')}", value])
    return cmd


def append_path_flags(cmd, args, *, include_state: bool):
    if getattr(args, "config_path", None):
        cmd.extend(["--config-path", args.config_path])
    if include_state and getattr(args, "state_path", None):
        cmd.extend(["--state-path", args.state_path])
    return cmd


def run_or_cli_error(builder, args):
    try:
        return run(builder(args))
    except CliError as exc:
        print(f"arkspace: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
