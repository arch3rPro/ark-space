#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HOST_DEFAULT_CACHE = {
    "codex": Path.home() / ".codex" / "plugins" / "cache" / "ark-space" / "ark-space",
    "claude-code": Path.home() / ".claude" / "plugins" / "cache" / "ark-space" / "ark-space",
}

HOST_SOURCE_ROOT = {
    "codex": ROOT / "plugins" / "ark-space",
    "claude-code": ROOT,
}

HOST_REQUIRED_FILES = {
    "codex": [
        ".codex-plugin/plugin.json",
        "README.md",
        "registry/search-providers.yaml",
        "registry/web-fetch-providers.yaml",
        "registry/code-context-providers.yaml",
        "registry/related-page-providers.yaml",
        "scripts/arkspace.py",
        "skills/orchestrator/SKILL.md",
        "skills/provider-manager/SKILL.md",
        "skills/provider-manager/scripts/arkspace_provider.py",
        "skills/provider-manager/scripts/arkspace_runtime/exa_client.py",
        "skills/provider-manager/scripts/arkspace_runtime/provider_config.py",
        "skills/searxng-search/SKILL.md",
        "skills/exa-search/SKILL.md",
        "skills/exa-contents/SKILL.md",
        "skills/exa-answer/SKILL.md",
        "skills/exa-context/SKILL.md",
        "skills/exa-similar/SKILL.md",
        "skills/tavily-search/SKILL.md",
        "skills/tavily-extract/SKILL.md",
    ],
    "claude-code": [
        ".claude-plugin/plugin.json",
        ".claude-plugin/marketplace.json",
        "README.md",
        "registry/search-providers.yaml",
        "registry/web-fetch-providers.yaml",
        "registry/code-context-providers.yaml",
        "registry/related-page-providers.yaml",
        "scripts/arkspace.py",
        "skills/orchestrator/SKILL.md",
        "skills/provider-manager/SKILL.md",
        "skills/provider-manager/scripts/arkspace_provider.py",
        "skills/provider-manager/scripts/arkspace_runtime/exa_client.py",
        "skills/provider-manager/scripts/arkspace_runtime/provider_config.py",
        "skills/searxng-search/SKILL.md",
        "skills/exa-search/SKILL.md",
        "skills/exa-contents/SKILL.md",
        "skills/exa-answer/SKILL.md",
        "skills/exa-context/SKILL.md",
        "skills/exa-similar/SKILL.md",
        "skills/tavily-search/SKILL.md",
        "skills/tavily-extract/SKILL.md",
    ],
}


def read_text(path):
    return path.read_text(encoding="utf-8")


def newest_cache_dir(cache_root):
    if not cache_root.exists():
        return None
    candidates = [path for path in cache_root.iterdir() if path.is_dir()]
    if not candidates:
        return None
    return sorted(candidates, key=lambda path: (path.stat().st_mtime, path.name))[-1]


def check_installed_host(host, cache_root):
    source_root = HOST_SOURCE_ROOT[host]
    installed_root = newest_cache_dir(cache_root)
    if installed_root is None:
        print(f"ERROR: installed {host} ArkSpace cache not found under {cache_root}", file=sys.stderr)
        return 1

    status = 0
    for rel_path in HOST_REQUIRED_FILES[host]:
        source_path = source_root / rel_path
        installed_path = installed_root / rel_path

        if not source_path.exists():
            print(f"ERROR: source file missing for {host}: {source_path.relative_to(ROOT)}", file=sys.stderr)
            status = 1
            continue
        if not installed_path.exists():
            print(f"ERROR: installed {host} cache missing: {installed_path}", file=sys.stderr)
            status = 1
            continue
        if read_text(source_path) != read_text(installed_path):
            print(f"ERROR: installed {host} cache is stale for {rel_path}", file=sys.stderr)
            status = 1

    if status == 0:
        print(f"arkspace installed-host smoke test passed for {host}: {installed_root}")
    return status


def main():
    parser = argparse.ArgumentParser(description="Check installed ArkSpace plugin cache for a host.")
    parser.add_argument("--host", choices=["codex", "claude-code"], required=True)
    parser.add_argument("--cache-root", help="Override host plugin cache root for tests.")
    args = parser.parse_args()

    cache_root = Path(args.cache_root).expanduser() if args.cache_root else HOST_DEFAULT_CACHE[args.host]
    raise SystemExit(check_installed_host(args.host, cache_root))


if __name__ == "__main__":
    main()
