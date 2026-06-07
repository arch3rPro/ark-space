#!/usr/bin/env python3
import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LIVE_PROMPT = "[$ark-space:orchestrator] 帮我查询 claude-code-everything 项目"
REGISTRY_ROUTED_CAPABILITIES = {
    "web_search",
    "web_fetch",
    "knowledge_management",
    "provider_configuration",
    "skill_governance",
}


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


def parse_simple_yaml_value(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def parse_simple_yaml_key_value(text, path, lineno):
    if ":" not in text:
        raise ValueError(f"{path.relative_to(ROOT)}:{lineno}: expected key: value")
    key, value = text.split(":", 1)
    key = key.strip()
    if not key:
        raise ValueError(f"{path.relative_to(ROOT)}:{lineno}: expected non-empty key")
    return key, parse_simple_yaml_value(value)


def parse_registry_skills(path):
    entries = []
    current = None
    in_skills = False
    saw_skills = False

    for lineno, line in enumerate(read_text(path).splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()

        if indent == 0:
            in_skills = stripped == "skills:"
            saw_skills = saw_skills or in_skills
            continue

        if not in_skills:
            continue

        if indent == 2 and stripped.startswith("- "):
            current = {}
            entries.append(current)
            remainder = stripped[2:].strip()
            if remainder:
                key, value = parse_simple_yaml_key_value(remainder, path, lineno)
                current[key] = value
            continue

        if indent != 4:
            raise ValueError(f"{path.relative_to(ROOT)}:{lineno}: expected two-space skill item or four-space property")

        if current is None:
            raise ValueError(f"{path.relative_to(ROOT)}:{lineno}: expected skill list item")

        key, value = parse_simple_yaml_key_value(stripped, path, lineno)
        if key in current:
            raise ValueError(f"{path.relative_to(ROOT)}:{lineno}: duplicate key {key}")
        current[key] = value

    if not saw_skills:
        raise ValueError(f"{path.relative_to(ROOT)} is missing required top-level skills:")
    if not entries:
        raise ValueError(f"{path.relative_to(ROOT)} must contain at least one skill entry")

    return entries


def parse_capabilities(value):
    return {capability.strip() for capability in value.split(",") if capability.strip()}


def is_active_public_skill(entry):
    return entry.get("status", "").strip() == "active" and entry.get("public", "").strip().lower() == "true"


def check_registry_route_examples():
    path = ROOT / "registry" / "skills.yaml"
    try:
        entries = parse_registry_skills(path)
    except ValueError as exc:
        return fail(str(exc))

    status = 0
    for entry in entries:
        if not is_active_public_skill(entry):
            continue

        capabilities = parse_capabilities(entry.get("capabilities", ""))
        routed_capabilities = sorted(capabilities & REGISTRY_ROUTED_CAPABILITIES)
        if not routed_capabilities:
            continue

        invocation = entry.get("orchestratorInvocation", "")
        if "$ark-space:orchestrator" not in invocation:
            name = entry.get("name", "<unnamed>")
            print(
                "ERROR: registry/skills.yaml active public skill "
                f"{name} has routed capabilities {','.join(routed_capabilities)} "
                'but orchestratorInvocation does not contain "$ark-space:orchestrator"',
                file=sys.stderr,
            )
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

    status |= check_registry_route_examples()

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
        "普通网页搜索",
        "public search",
        "绕过 ArkSpace provider",
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
