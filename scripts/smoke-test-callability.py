#!/usr/bin/env python3
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CORE_AGENT_STEMS = {
    "arkspace-orchestrator",
    "arkspace-knowledge-manager",
    "arkspace-skill-manager",
}


def check_local():
    required = [
        ROOT / "skills" / "orchestrator" / "SKILL.md",
        ROOT / "skills" / "skill-manager" / "SKILL.md",
        ROOT / "agents" / "orchestrator.md",
        ROOT / "registry" / "agents.yaml",
        ROOT / "workflows" / "lightweight-routing.md",
    ]
    missing = [path for path in required if not path.exists()]
    for path in missing:
        print(f"missing: {path.relative_to(ROOT)}")
    return 1 if missing else 0


def check_generated(host):
    suffix = ".toml" if host == "codex" else ".md"
    base = ROOT / "integrations" / host / "agents"
    missing = [stem for stem in CORE_AGENT_STEMS if not (base / f"{stem}{suffix}").exists()]
    for stem in missing:
        print(f"missing generated agent: {host}/{stem}{suffix}")
    return 1 if missing else 0


def main():
    parser = argparse.ArgumentParser(description="Check ArkSpace local runtime entrypoints.")
    parser.add_argument("--host", choices=["codex", "claude-code"], required=True)
    parser.add_argument("--local", action="store_true")
    args = parser.parse_args()

    status = check_local()
    status |= check_generated(args.host)
    if status == 0:
        print(f"arkspace callability smoke test passed for {args.host}")
    raise SystemExit(status)


if __name__ == "__main__":
    main()
