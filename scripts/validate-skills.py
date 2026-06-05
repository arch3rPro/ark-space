#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALID_SYNC_MODES = {"mirror", "adapted", "local", "reference-only"}


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_text(path):
    return path.read_text(encoding="utf-8")


def parse_simple_yaml_list(path, top_key):
    text = read_text(path)
    lines = text.splitlines()
    try:
        start = next(index for index, line in enumerate(lines) if line.strip() == f"{top_key}:")
    except StopIteration:
        fail(f"{path} must contain '{top_key}:'")

    items = []
    current = None
    for raw in lines[start + 1:]:
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.endswith(":") and not line.startswith("  "):
            break
        if line.startswith("  - "):
            if current:
                items.append(current)
            current = {}
            rest = line[4:]
            if ": " in rest:
                key, value = rest.split(": ", 1)
                current[key] = clean_scalar(value)
        elif current is not None and line.startswith("    ") and ": " in stripped:
            key, value = stripped.split(": ", 1)
            current[key] = clean_scalar(value)
    if current:
        items.append(current)
    return items


def clean_scalar(value):
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    return value


def validate_skill_frontmatter():
    skill_files = sorted((ROOT / "skills").glob("*/SKILL.md"))
    if not skill_files:
        fail("no skills/*/SKILL.md files found")

    for path in skill_files:
        text = read_text(path)
        if not text.startswith("---\n"):
            fail(f"{path} is missing YAML frontmatter")
        end = text.find("\n---\n", 4)
        if end == -1:
            fail(f"{path} has unterminated YAML frontmatter")
        frontmatter = text[4:end]
        if not re.search(r"^name:\s*.+$", frontmatter, re.MULTILINE):
            fail(f"{path} frontmatter is missing name")
        if not re.search(r"^description:\s*.+$", frontmatter, re.MULTILINE):
            fail(f"{path} frontmatter is missing description")


def validate_json(path):
    try:
        json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        fail(f"{path} is invalid JSON: {exc}")


def validate_registry_files():
    registry_dir = ROOT / "registry"
    for filename in ["sources.yaml", "skills.yaml", "roles.yaml"]:
        path = registry_dir / filename
        if not path.exists():
            fail(f"missing {path}")

    skills = parse_simple_yaml_list(registry_dir / "skills.yaml", "skills")
    roles = parse_simple_yaml_list(registry_dir / "roles.yaml", "roles")
    sources = parse_simple_yaml_list(registry_dir / "sources.yaml", "sources")

    source_ids = {item.get("id") for item in sources if item.get("id")}
    role_ids = {item.get("id") for item in roles if item.get("id")}

    roles_text = read_text(registry_dir / "roles.yaml")
    if not re.search(r"^defaultRole:\s*orchestrator$", roles_text, re.MULTILINE):
        fail("registry/roles.yaml must set defaultRole: orchestrator")

    if "orchestrator" not in role_ids:
        fail("registry/roles.yaml must include id: orchestrator")

    for item in skills:
        name = item.get("name")
        path_value = item.get("path")
        sync_mode = item.get("syncMode")
        if not name:
            fail("registry/skills.yaml contains a skill without name")
        if sync_mode not in VALID_SYNC_MODES:
            fail(f"skill {name} has invalid syncMode {sync_mode}")
        if path_value:
            skill_path = ROOT / path_value
            if not skill_path.exists():
                fail(f"skill {name} path does not exist: {path_value}")
            if not (skill_path / "SKILL.md").exists():
                fail(f"skill {name} path is missing SKILL.md: {path_value}")
        upstream_id = item.get("upstreamId")
        if upstream_id and upstream_id not in source_ids:
            fail(f"skill {name} references unknown upstreamId {upstream_id}")

    for item in roles:
        role_id = item.get("id")
        path_value = item.get("path")
        if not role_id:
            fail("registry/roles.yaml contains a role without id")
        if path_value and not (ROOT / path_value).exists():
            fail(f"role {role_id} path does not exist: {path_value}")


def validate_platform_manifests():
    validate_json(ROOT / ".claude-plugin" / "plugin.json")
    validate_json(ROOT / ".claude-plugin" / "marketplace.json")
    validate_json(ROOT / ".codex-plugin" / "plugin.json")

    codex = json.loads(read_text(ROOT / ".codex-plugin" / "plugin.json"))
    if codex.get("skills") != "./skills/":
        fail(".codex-plugin/plugin.json must set skills to ./skills/")


def main():
    validate_skill_frontmatter()
    validate_registry_files()
    validate_platform_manifests()
    print("skills package validation passed")


if __name__ == "__main__":
    main()
