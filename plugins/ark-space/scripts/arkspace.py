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
    ("tavily", "web_map"): [sys.executable, "skills/tavily-map/scripts/tavily_map.py", "--check"],
    ("tavily", "web_crawl"): [sys.executable, "skills/tavily-crawl/scripts/tavily_crawl.py", "--check"],
    ("tavily", "deep_research"): [sys.executable, "skills/tavily-research/scripts/tavily_research.py", "--check"],
    ("exa", "web_search"): [sys.executable, "skills/exa-search/scripts/exa_search.py", "--check"],
    ("exa", "web_fetch"): [sys.executable, "skills/exa-contents/scripts/exa_contents.py", "--check"],
    ("exa", "deep_research"): [sys.executable, "skills/exa-answer/scripts/exa_answer.py", "--check"],
    ("exa", "code_context"): [sys.executable, "skills/exa-context/scripts/exa_context.py", "--check"],
    ("exa", "related_pages"): [sys.executable, "skills/exa-similar/scripts/exa_similar.py", "--check"],
}

WEB_SEARCH_COMMANDS = {
    "exa": [sys.executable, "skills/exa-search/scripts/exa_search.py"],
    "searxng": [sys.executable, "skills/searxng-search/scripts/searxng_search.py"],
    "tavily": [sys.executable, "skills/tavily-search/scripts/tavily_search.py"],
}

WEB_FETCH_COMMANDS = {
    "exa": [sys.executable, "skills/exa-contents/scripts/exa_contents.py"],
    "tavily": [sys.executable, "skills/tavily-extract/scripts/tavily_extract.py"],
}

WEB_SIMILAR_COMMANDS = {
    "exa": [sys.executable, "skills/exa-similar/scripts/exa_similar.py"],
}

SITE_MAP_COMMANDS = {
    "tavily": [sys.executable, "skills/tavily-map/scripts/tavily_map.py"],
}

SITE_CRAWL_COMMANDS = {
    "tavily": [sys.executable, "skills/tavily-crawl/scripts/tavily_crawl.py"],
}

RESEARCH_COMMANDS = {
    "exa": [sys.executable, "skills/exa-answer/scripts/exa_answer.py"],
    "tavily": [sys.executable, "skills/tavily-research/scripts/tavily_research.py"],
}

CODE_CONTEXT_COMMANDS = {
    "exa": [sys.executable, "skills/exa-context/scripts/exa_context.py"],
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

    provider_setup = provider_sub.add_parser("setup")
    provider_setup.add_argument("provider")
    provider_setup.add_argument("--base-url")
    provider_setup.add_argument("--env", action="append", default=[])
    provider_setup.add_argument("--save-secret", action="append", default=[])
    provider_setup.add_argument("--wizard", action="store_true")
    provider_setup.add_argument("--key-count")
    provider_setup.add_argument("--prompt", action="store_true")
    provider_setup.add_argument("--secret-stdin", action="store_true")
    provider_setup.add_argument("--check", action="store_true")
    provider_setup.add_argument("--config-path")
    provider_setup.add_argument("--state-path")

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
    web_search.add_argument("--search-type")
    web_search.add_argument("--category")
    web_search.add_argument("--freshness")
    web_search.add_argument("--start-crawl-date")
    web_search.add_argument("--end-crawl-date")
    web_search.add_argument("--start-published-date")
    web_search.add_argument("--end-published-date")
    web_search.add_argument("--include-text", action="store_true")
    web_search.add_argument("--include-highlights", action="store_true")
    web_search.add_argument("--include-summary", action="store_true")
    web_search.add_argument("--text-max-characters")
    web_search.add_argument("--highlight-query")
    web_search.add_argument("--highlight-num-sentences")
    web_search.add_argument("--highlights-per-url")
    web_search.add_argument("--highlight-max-characters")
    web_search.add_argument("--summary-query")
    web_search.add_argument("--additional-queries")
    web_search.add_argument("--user-location")
    web_search.add_argument("--moderation", action="store_true")
    web_search.add_argument("--output-schema")
    web_search.add_argument("--system-prompt")
    web_search.add_argument("--stream", action="store_true")
    web_search.add_argument("--base-url")
    web_search.add_argument("--config-path")
    web_search.add_argument("--state-path")
    web_search.add_argument("--timeout")
    web_search.add_argument("--output", choices=["json", "markdown"])

    web_fetch = web_sub.add_parser("fetch")
    web_fetch.add_argument("urls", nargs="*")
    web_fetch.add_argument("--provider", required=True, choices=sorted(WEB_FETCH_COMMANDS))
    web_fetch.add_argument("--ids")
    web_fetch.add_argument("--query")
    web_fetch.add_argument("--extract-depth")
    web_fetch.add_argument("--chunks-per-source")
    web_fetch.add_argument("--include-images", action="store_true")
    web_fetch.add_argument("--include-summary", action="store_true")
    web_fetch.add_argument("--include-highlights", action="store_true")
    web_fetch.add_argument("--text-max-characters")
    web_fetch.add_argument("--highlight-query")
    web_fetch.add_argument("--highlight-num-sentences")
    web_fetch.add_argument("--highlights-per-url")
    web_fetch.add_argument("--highlight-max-characters")
    web_fetch.add_argument("--summary-query")
    web_fetch.add_argument("--max-age-hours")
    web_fetch.add_argument("--subpages")
    web_fetch.add_argument("--subpage-target")
    web_fetch.add_argument("--include-links", action="store_true")
    web_fetch.add_argument("--timeout")
    web_fetch.add_argument("--config-path")
    web_fetch.add_argument("--state-path")
    web_fetch.add_argument("--output", choices=["json", "markdown"])

    web_similar = web_sub.add_parser("similar")
    web_similar.add_argument("url")
    web_similar.add_argument("--provider", required=True, choices=sorted(WEB_SIMILAR_COMMANDS))
    web_similar.add_argument("--max-results")
    web_similar.add_argument("--search-type")
    web_similar.add_argument("--include-domains")
    web_similar.add_argument("--exclude-domains")
    web_similar.add_argument("--start-crawl-date")
    web_similar.add_argument("--end-crawl-date")
    web_similar.add_argument("--start-published-date")
    web_similar.add_argument("--end-published-date")
    web_similar.add_argument("--include-text", action="store_true")
    web_similar.add_argument("--include-highlights", action="store_true")
    web_similar.add_argument("--include-summary", action="store_true")
    web_similar.add_argument("--timeout")
    web_similar.add_argument("--config-path")
    web_similar.add_argument("--state-path")
    web_similar.add_argument("--output", choices=["json", "markdown"])

    site = sub.add_parser("site")
    site_sub = site.add_subparsers(dest="site_command", required=True)
    site_map = site_sub.add_parser("map")
    site_map.add_argument("url")
    site_map.add_argument("--provider", required=True, choices=sorted(SITE_MAP_COMMANDS))
    site_map.add_argument("--instructions")
    site_map.add_argument("--max-depth")
    site_map.add_argument("--max-breadth")
    site_map.add_argument("--limit")
    site_map.add_argument("--select-paths")
    site_map.add_argument("--exclude-paths")
    site_map.add_argument("--select-domains")
    site_map.add_argument("--exclude-domains")
    site_map.add_argument("--allow-external", action="store_true")
    site_map.add_argument("--no-external", action="store_true")
    site_map.add_argument("--include-usage", action="store_true")
    site_map.add_argument("--timeout")
    site_map.add_argument("--config-path")
    site_map.add_argument("--state-path")
    site_map.add_argument("--output", choices=["json", "markdown"])

    site_crawl = site_sub.add_parser("crawl")
    site_crawl.add_argument("url")
    site_crawl.add_argument("--provider", required=True, choices=sorted(SITE_CRAWL_COMMANDS))
    site_crawl.add_argument("--instructions")
    site_crawl.add_argument("--chunks-per-source")
    site_crawl.add_argument("--max-depth")
    site_crawl.add_argument("--max-breadth")
    site_crawl.add_argument("--limit")
    site_crawl.add_argument("--select-paths")
    site_crawl.add_argument("--exclude-paths")
    site_crawl.add_argument("--select-domains")
    site_crawl.add_argument("--exclude-domains")
    site_crawl.add_argument("--allow-external", action="store_true")
    site_crawl.add_argument("--no-external", action="store_true")
    site_crawl.add_argument("--include-images", action="store_true")
    site_crawl.add_argument("--include-favicon", action="store_true")
    site_crawl.add_argument("--extract-depth")
    site_crawl.add_argument("--format")
    site_crawl.add_argument("--include-usage", action="store_true")
    site_crawl.add_argument("--timeout")
    site_crawl.add_argument("--config-path")
    site_crawl.add_argument("--state-path")
    site_crawl.add_argument("--output", choices=["json", "markdown"])

    research = sub.add_parser("research")
    research_sub = research.add_subparsers(dest="research_command", required=True)
    research_run = research_sub.add_parser("run")
    research_run.add_argument("input")
    research_run.add_argument("--provider", required=True, choices=sorted(RESEARCH_COMMANDS))
    research_run.add_argument("--model")
    research_run.add_argument("--citation-format")
    research_run.add_argument("--include-domains")
    research_run.add_argument("--exclude-domains")
    research_run.add_argument("--output-length")
    research_run.add_argument("--output-schema")
    research_run.add_argument("--wait", action="store_true")
    research_run.add_argument("--poll-interval")
    research_run.add_argument("--timeout")
    research_run.add_argument("--config-path")
    research_run.add_argument("--state-path")
    research_run.add_argument("--output", choices=["json", "markdown"])

    research_status = research_sub.add_parser("status")
    research_status.add_argument("request_id")
    research_status.add_argument("--provider", required=True, choices=sorted(RESEARCH_COMMANDS))
    research_status.add_argument("--poll-interval")
    research_status.add_argument("--timeout")
    research_status.add_argument("--config-path")
    research_status.add_argument("--state-path")
    research_status.add_argument("--output", choices=["json", "markdown"])

    code = sub.add_parser("code")
    code_sub = code.add_subparsers(dest="code_command", required=True)
    code_context = code_sub.add_parser("context")
    code_context.add_argument("query")
    code_context.add_argument("--provider", required=True, choices=sorted(CODE_CONTEXT_COMMANDS))
    code_context.add_argument("--tokens")
    code_context.add_argument("--timeout")
    code_context.add_argument("--config-path")
    code_context.add_argument("--state-path")
    code_context.add_argument("--output", choices=["json", "markdown"])

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
    smoke.add_argument("--installed-host", choices=["codex", "claude-code"])
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
    if args.command == "site":
        return run_or_cli_error(site_command, args)
    if args.command == "research":
        return run_or_cli_error(research_command, args)
    if args.command == "code":
        return run_or_cli_error(code_command, args)
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
        if args.installed_host:
            return run([sys.executable, "scripts/smoke-test-installed-host.py", "--host", args.installed_host])
        if not args.host:
            parser.error("smoke-test requires --host, --installed-host, or --routing")
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
        print("[arkspace doctor] installed-host: unverified (run smoke-test --installed-host codex|claude-code)")
        return status
    return 2


def provider_command(args):
    if args.provider_command == "check":
        capability = args.capability or "web_search"
        command = PROVIDER_CHECK_COMMANDS.get((args.provider, capability))
        if not command:
            raise CliError(f"provider {args.provider} does not have a {capability} check")
        return append_path_flags([*command], args, include_state=args.provider in {"tavily", "exa"})

    cmd = [sys.executable, "scripts/arkspace_provider.py"]
    cmd = append_path_flags(cmd, args, include_state=True)
    cmd.append(args.provider_command)
    if args.provider_command in {"configure", "add-key", "setup", "resolve"}:
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
    if args.provider_command == "setup":
        if args.base_url:
            cmd.extend(["--base-url", args.base_url])
        for env_name in args.env:
            cmd.extend(["--env", env_name])
        for env_name in args.save_secret:
            cmd.extend(["--save-secret", env_name])
        if args.wizard:
            cmd.append("--wizard")
        if args.key_count:
            cmd.extend(["--key-count", args.key_count])
        if args.prompt:
            cmd.append("--prompt")
        if args.secret_stdin:
            cmd.append("--secret-stdin")
        if args.check:
            cmd.append("--check")
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
            if (
                args.search_depth
                or args.topic
                or args.include_domains
                or args.exclude_domains
                or args.include_answer
                or args.search_type
                or args.category
                or args.freshness
                or args.start_crawl_date
                or args.end_crawl_date
                or args.start_published_date
                or args.end_published_date
                or args.include_text
                or args.include_highlights
                or args.include_summary
                or args.text_max_characters
                or args.highlight_query
                or args.highlight_num_sentences
                or args.highlights_per_url
                or args.highlight_max_characters
                or args.summary_query
                or args.additional_queries
                or args.user_location
                or args.output_schema
                or args.system_prompt
                or args.stream
                or args.moderation
            ):
                raise CliError("searxng web search does not support Exa/Tavily-specific search options")
            cmd = append_value_flags(cmd, args, ["base_url", "time_range", "config_path", "timeout", "output"])
            if args.max_results:
                cmd.extend(["--limit", args.max_results])
            return cmd
        if args.provider == "exa":
            if args.base_url:
                raise CliError("exa web search does not accept --base-url; use provider setup exa --base-url <url>")
            if args.search_depth or args.topic or args.time_range or args.include_answer:
                raise CliError("exa web search does not support Tavily-specific search options")
            for name in [
                "max_results",
                "search_type",
                "category",
                "freshness",
                "include_domains",
                "exclude_domains",
                "start_crawl_date",
                "end_crawl_date",
                "start_published_date",
                "end_published_date",
                "text_max_characters",
                "highlight_query",
                "highlight_num_sentences",
                "highlights_per_url",
                "highlight_max_characters",
                "summary_query",
                "additional_queries",
                "user_location",
                "output_schema",
                "system_prompt",
                "timeout",
                "config_path",
                "state_path",
                "output",
            ]:
                value = getattr(args, name)
                if value:
                    cmd.extend([f"--{name.replace('_', '-')}", value])
            for name in ["include_text", "include_highlights", "include_summary", "stream"]:
                if getattr(args, name):
                    cmd.append(f"--{name.replace('_', '-')}")
            if args.moderation:
                cmd.append("--moderation")
            return cmd
        if args.base_url:
            raise CliError("tavily web search does not accept --base-url; use provider setup tavily --base-url <url>")
        if (
            args.search_type
            or args.category
            or args.freshness
            or args.start_crawl_date
            or args.end_crawl_date
            or args.start_published_date
            or args.end_published_date
            or args.include_text
            or args.include_highlights
            or args.include_summary
            or args.text_max_characters
            or args.highlight_query
            or args.highlight_num_sentences
            or args.highlights_per_url
            or args.highlight_max_characters
            or args.summary_query
            or args.additional_queries
            or args.user_location
            or args.output_schema
            or args.system_prompt
            or args.stream
            or args.moderation
        ):
            raise CliError("tavily web search does not support Exa-specific search options")
        for name in ["max_results", "search_depth", "topic", "time_range", "include_domains", "exclude_domains", "timeout", "config_path", "state_path", "output"]:
            value = getattr(args, name)
            if value:
                cmd.extend([f"--{name.replace('_', '-')}", value])
        if args.include_answer:
            cmd.append("--include-answer")
        return cmd

    if args.web_command == "fetch":
        cmd = [*WEB_FETCH_COMMANDS[args.provider], *args.urls]
        if args.provider == "exa":
            if args.query or args.extract_depth or args.chunks_per_source or args.include_images:
                raise CliError("exa web fetch does not support Tavily-specific fetch options")
            for name in [
                "ids",
                "text_max_characters",
                "highlight_query",
                "highlight_num_sentences",
                "highlights_per_url",
                "highlight_max_characters",
                "summary_query",
                "max_age_hours",
                "subpages",
                "subpage_target",
                "timeout",
                "config_path",
                "state_path",
                "output",
            ]:
                value = getattr(args, name)
                if value:
                    cmd.extend([f"--{name.replace('_', '-')}", value])
            for name in ["include_summary", "include_highlights", "include_links"]:
                if getattr(args, name):
                    cmd.append(f"--{name.replace('_', '-')}")
            return cmd
        if not args.urls:
            raise CliError("tavily web fetch requires at least one URL")
        if (
            args.ids
            or args.text_max_characters
            or args.highlight_query
            or args.highlight_num_sentences
            or args.highlights_per_url
            or args.highlight_max_characters
            or args.summary_query
            or args.max_age_hours
            or args.subpages
            or args.subpage_target
            or args.include_links
        ):
            raise CliError("tavily web fetch does not support Exa-specific fetch options")
        for name in ["query", "extract_depth", "chunks_per_source", "timeout", "config_path", "state_path", "output"]:
            value = getattr(args, name)
            if value:
                cmd.extend([f"--{name.replace('_', '-')}", value])
        if args.include_images:
            cmd.append("--include-images")
        return cmd

    if args.web_command == "similar":
        cmd = [*WEB_SIMILAR_COMMANDS[args.provider], args.url]
        for name in [
            "max_results",
            "search_type",
            "include_domains",
            "exclude_domains",
            "start_crawl_date",
            "end_crawl_date",
            "start_published_date",
            "end_published_date",
            "timeout",
            "config_path",
            "state_path",
            "output",
        ]:
            value = getattr(args, name)
            if value:
                cmd.extend([f"--{name.replace('_', '-')}", value])
        for name in ["include_text", "include_highlights", "include_summary"]:
            if getattr(args, name):
                cmd.append(f"--{name.replace('_', '-')}")
        return cmd

    raise ValueError(f"unknown web command {args.web_command}")


def site_command(args):
    if args.site_command == "map":
        cmd = [*SITE_MAP_COMMANDS[args.provider], args.url]
        for name in [
            "instructions",
            "max_depth",
            "max_breadth",
            "limit",
            "select_paths",
            "exclude_paths",
            "select_domains",
            "exclude_domains",
            "timeout",
            "config_path",
            "state_path",
            "output",
        ]:
            value = getattr(args, name)
            if value:
                cmd.extend([f"--{name.replace('_', '-')}", value])
        append_boolean_pair(cmd, args, "allow_external", "no_external", "--allow-external", "--no-external")
        if args.include_usage:
            cmd.append("--include-usage")
        return cmd

    if args.site_command == "crawl":
        cmd = [*SITE_CRAWL_COMMANDS[args.provider], args.url]
        for name in [
            "instructions",
            "chunks_per_source",
            "max_depth",
            "max_breadth",
            "limit",
            "select_paths",
            "exclude_paths",
            "select_domains",
            "exclude_domains",
            "extract_depth",
            "format",
            "timeout",
            "config_path",
            "state_path",
            "output",
        ]:
            value = getattr(args, name)
            if value:
                cmd.extend([f"--{name.replace('_', '-')}", value])
        append_boolean_pair(cmd, args, "allow_external", "no_external", "--allow-external", "--no-external")
        for name in ["include_images", "include_favicon", "include_usage"]:
            if getattr(args, name):
                cmd.append(f"--{name.replace('_', '-')}")
        return cmd

    raise ValueError(f"unknown site command {args.site_command}")


def research_command(args):
    if args.research_command == "run":
        cmd = [*RESEARCH_COMMANDS[args.provider], args.input]
        if args.provider == "exa":
            if args.model or args.citation_format or args.include_domains or args.exclude_domains or args.output_length or args.output_schema or args.wait or args.poll_interval:
                raise CliError("exa research run does not support Tavily Research task options")
            for name in ["timeout", "config_path", "state_path", "output"]:
                value = getattr(args, name)
                if value:
                    cmd.extend([f"--{name.replace('_', '-')}", value])
            return cmd
        for name in [
            "model",
            "citation_format",
            "include_domains",
            "exclude_domains",
            "output_length",
            "output_schema",
            "poll_interval",
            "timeout",
            "config_path",
            "state_path",
            "output",
        ]:
            value = getattr(args, name)
            if value:
                cmd.extend([f"--{name.replace('_', '-')}", value])
        if args.wait:
            cmd.append("--wait")
        return cmd

    if args.research_command == "status":
        if args.provider == "exa":
            raise CliError("exa research status is not supported; Exa Answer returns synchronously")
        cmd = [*RESEARCH_COMMANDS[args.provider], "--status", args.request_id]
        for name in ["poll_interval", "timeout", "config_path", "state_path", "output"]:
            value = getattr(args, name)
            if value:
                cmd.extend([f"--{name.replace('_', '-')}", value])
        return cmd

    raise ValueError(f"unknown research command {args.research_command}")


def code_command(args):
    if args.code_command == "context":
        cmd = [*CODE_CONTEXT_COMMANDS[args.provider], args.query]
        for name in ["tokens", "timeout", "config_path", "state_path", "output"]:
            value = getattr(args, name)
            if value:
                cmd.extend([f"--{name.replace('_', '-')}", value])
        return cmd

    raise ValueError(f"unknown code command {args.code_command}")


def append_value_flags(cmd, args, names):
    for name in names:
        value = getattr(args, name)
        if value:
            cmd.extend([f"--{name.replace('_', '-')}", value])
    return cmd


def append_boolean_pair(cmd, args, true_attr, false_attr, true_flag, false_flag):
    if getattr(args, true_attr):
        cmd.append(true_flag)
    if getattr(args, false_attr):
        cmd.append(false_flag)
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
