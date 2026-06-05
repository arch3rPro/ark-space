#!/usr/bin/env python3
import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LIVE_PROMPT = "[$ark-space:orchestrator] 帮我查询 claude-code-everything 项目"


def read_text(path):
    return path.read_text(encoding="utf-8")


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    return 1


def require_text(path, needles):
    text = read_text(path)
    missing = [needle for needle in needles if needle not in text]
    if missing:
        for needle in missing:
            print(f"ERROR: {path.relative_to(ROOT)} is missing required routing text: {needle}", file=sys.stderr)
        return 1
    return 0


def require_regex(path, patterns):
    text = read_text(path)
    status = 0
    for pattern in patterns:
        if not re.search(pattern, text, re.MULTILINE | re.DOTALL):
            print(f"ERROR: {path.relative_to(ROOT)} does not match required routing pattern: {pattern}", file=sys.stderr)
            status = 1
    return status


def check_static():
    status = 0

    status |= require_text(
        ROOT / "skills" / "orchestrator" / "SKILL.md",
        [
            "act as the ArkSpace entrypoint, not as a generic host assistant",
            "Host-native capabilities are not ArkSpace providers",
            "registry/search-providers.yaml",
            "stop before producing capability results",
            LIVE_PROMPT,
        ],
    )
    status |= require_regex(
        ROOT / "skills" / "orchestrator" / "SKILL.md",
        [
            r"web_search.*registry/search-providers\.yaml",
            r"checkCommand.*configuration",
        ],
    )

    status |= require_text(
        ROOT / "workflows" / "provider-capabilities.md",
        [
            "ArkSpace provider registries are the authority",
            "registry/search-providers.yaml",
            "route to `provider-manager` for guided setup and stop before producing capability results",
            "Host-native search or fetch is outside ArkSpace provider routing",
        ],
    )

    status |= require_text(
        ROOT / "agents" / "orchestrator.md",
        [
            "provider-capabilities",
            "Provider registries are part of the route, not an optional enhancement",
        ],
    )

    status |= require_regex(
        ROOT / "registry" / "agents.yaml",
        [
            r"id: arkspace-orchestrator.*workflows: lightweight-routing,provider-capabilities,handoff-template,quality-gates",
        ],
    )
    status |= require_regex(
        ROOT / "registry" / "workflows.yaml",
        [
            r"id: provider-capabilities.*usedBy: arkspace-orchestrator,arkspace-knowledge-manager,arkspace-competitive-analyst",
        ],
    )

    generated_codex = ROOT / "integrations" / "codex" / "agents" / "arkspace-orchestrator.toml"
    generated_claude = ROOT / "integrations" / "claude-code" / "agents" / "arkspace-orchestrator.md"
    if generated_codex.exists():
        status |= require_text(generated_codex, ["Provider registries are part of the route"])
    if generated_claude.exists():
        status |= require_text(generated_claude, ["Provider registries are part of the route"])

    package_root = ROOT / "plugins" / "ark-space"
    for rel_path in [
        "agents/orchestrator.md",
        "registry/search-providers.yaml",
        "registry/web-fetch-providers.yaml",
        "workflows/provider-capabilities.md",
        "roles/orchestrator.yaml",
    ]:
        path = package_root / rel_path
        if not path.exists():
            print(f"ERROR: Codex package is missing routing file: {path.relative_to(ROOT)}", file=sys.stderr)
            status = 1

    if status == 0:
        print("arkspace orchestrator routing static smoke test passed")
    return status


def check_live_codex():
    cmd = [
        "codex",
        "exec",
        "--cd",
        "/tmp",
        "--dangerously-bypass-approvals-and-sandbox",
        LIVE_PROMPT,
    ]
    result = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
    output = result.stdout
    print(output)
    if result.returncode != 0:
        return fail(f"codex exec exited with {result.returncode}")

    lowered = output.lower()
    forbidden = [
        "websearch",
        "web search",
        "已搜索网页",
        "search_query",
        "使用联网搜索",
        "普通公网搜索",
        "public search",
    ]
    if any(item in lowered for item in forbidden):
        return fail("live routing used host-native web search instead of ArkSpace provider routing")

    required_any = [
        "provider-manager",
        "searxng",
        "SearXNG",
        "not configured",
        "missing",
        "配置",
    ]
    if not any(item in output for item in required_any):
        return fail("live routing did not surface provider setup or SearXNG configuration state")

    print("arkspace orchestrator routing live Codex smoke test passed")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Check ArkSpace Orchestrator routing behavior.")
    parser.add_argument("--live-codex", action="store_true", help="Run the installed Codex plugin against the acceptance prompt.")
    args = parser.parse_args()

    status = check_static()
    if args.live_codex:
        status |= check_live_codex()
    raise SystemExit(status)


if __name__ == "__main__":
    main()
