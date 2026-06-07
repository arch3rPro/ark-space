#!/usr/bin/env python3
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CORE_AGENT_STEMS = {
    "arkspace-orchestrator",
    "arkspace-knowledge-manager",
    "arkspace-skill-manager",
}


def read_text(path):
    return path.read_text(encoding="utf-8")


def clean_scalar(value):
    value = value.strip()
    if not value:
        return ""
    if value[0] in {'"', "'"} and value[-1:] == value[0]:
        return value[1:-1]
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    return value


def parse_simple_yaml_list(text, list_name):
    items = []
    current = None
    in_list = False

    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if not in_list:
            if line == f"{list_name}:":
                in_list = True
            continue

        if not line.startswith(" "):
            break

        if stripped.startswith("- "):
            if current is not None:
                items.append(current)
            current = {}
            remainder = stripped[2:].strip()
            if remainder:
                if ":" not in remainder:
                    raise ValueError(f"line {line_number}: expected key: value")
                key, value = remainder.split(":", 1)
                current[key.strip()] = clean_scalar(value)
            continue

        if current is None:
            raise ValueError(f"line {line_number}: expected list item")
        if ":" not in stripped:
            raise ValueError(f"line {line_number}: expected key: value")
        key, value = stripped.split(":", 1)
        current[key.strip()] = clean_scalar(value)

    if current is not None:
        items.append(current)
    if not in_list:
        raise ValueError(f"missing {list_name}:")
    return items


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


def check_direct_invocations():
    registry_path = ROOT / "registry" / "skills.yaml"
    try:
        skills = parse_simple_yaml_list(read_text(registry_path), "skills")
    except FileNotFoundError:
        print(f"missing registry: {registry_path.relative_to(ROOT)}")
        return 1
    except ValueError as exc:
        print(f"invalid registry/skills.yaml: {exc}")
        return 1

    status = 0
    for item in skills:
        if item.get("status") != "active" or item.get("public") is not True:
            continue

        name = str(item.get("name", "")).strip()
        path = str(item.get("path", "")).strip()
        label = name or path or "<unnamed skill>"

        if not name:
            print(f"missing skill name for active public skill: {label}")
            status = 1
            continue

        if not path:
            print(f"missing skill path for active public skill: {name}")
            status = 1
        elif not (ROOT / path / "SKILL.md").exists():
            print(f"missing direct skill entrypoint for {name}: {path}/SKILL.md")
            status = 1

        expected = f"$ark-space:{name}"
        direct_invocation = str(item.get("directInvocation", ""))
        if expected not in direct_invocation:
            print(f"missing direct invocation for {name}: directInvocation must contain {expected}")
            status = 1

    return status


def main():
    parser = argparse.ArgumentParser(description="Check ArkSpace local runtime entrypoints.")
    parser.add_argument("--host", choices=["codex", "claude-code"], required=True)
    parser.add_argument("--local", action="store_true")
    args = parser.parse_args()

    status = check_local()
    status |= check_direct_invocations()
    status |= check_generated(args.host)
    if status == 0:
        print(f"arkspace callability smoke test passed for {args.host}")
    raise SystemExit(status)


if __name__ == "__main__":
    main()
