#!/usr/bin/env python3
import json
import re
import sys
import tomllib
import filecmp
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALID_SYNC_MODES = {"mirror", "adapted", "local", "reference-only"}
VALID_PROVIDER_STATUS = {"active", "experimental", "disabled"}


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


def split_csv(value):
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_frontmatter(path):
    text = read_text(path)
    if not text.startswith("---\n"):
        fail(f"{path} is missing YAML frontmatter")
    try:
        _, frontmatter, _ = text.split("---", 2)
    except ValueError:
        fail(f"{path} has unterminated YAML frontmatter")

    data = {}
    current_list = None
    for raw in frontmatter.splitlines():
        if not raw.strip():
            continue
        if raw.startswith("  - ") and current_list:
            data[current_list].append(raw[4:].strip())
            continue
        if ": " in raw:
            key, value = raw.split(": ", 1)
            key = key.strip()
            value = value.strip()
            if value:
                data[key] = value
                current_list = None
            else:
                data[key] = []
                current_list = key
    return data


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


def iter_package_files(path):
    return sorted(
        item
        for item in path.rglob("*")
        if item.is_file()
        and "__pycache__" not in item.parts
        and item.suffix not in {".pyc", ".pyo"}
    )


def validate_codex_package_copy(package_dir):
    if not package_dir.exists():
        fail(f"Codex package directory is missing: {package_dir.relative_to(ROOT)}")
    if not package_dir.is_dir():
        fail(f"Codex package path must be a directory: {package_dir.relative_to(ROOT)}")

    symlinks = sorted(item for item in package_dir.rglob("*") if item.is_symlink())
    if symlinks:
        rendered = ", ".join(str(item.relative_to(ROOT)) for item in symlinks[:5])
        fail(f"Codex package directory must contain real files, not symlinks: {rendered}")

    required_paths = [
        ".codex-plugin/plugin.json",
        "skills/orchestrator/SKILL.md",
        "skills/provider-manager/SKILL.md",
        "skills/searxng-search/SKILL.md",
        "scripts/arkspace_provider.py",
        "README.md",
        "LICENSE",
        "NOTICE.md",
    ]
    for rel_path in required_paths:
        if not (package_dir / rel_path).exists():
            fail(f"Codex package directory is missing {rel_path}")

    mirrored_roots = [".codex-plugin", "skills", "scripts"]
    mirrored_files = ["README.md", "LICENSE", "NOTICE.md"]
    for rel_root in mirrored_roots:
        source_dir = ROOT / rel_root
        package_subdir = package_dir / rel_root
        source_files = [item.relative_to(source_dir) for item in iter_package_files(source_dir)]
        package_files = [item.relative_to(package_subdir) for item in iter_package_files(package_subdir)]
        if source_files != package_files:
            fail(f"Codex package {rel_root}/ file list does not match repository source")
        for rel_file in source_files:
            if not filecmp.cmp(source_dir / rel_file, package_subdir / rel_file, shallow=False):
                fail(f"Codex package file is stale: {package_subdir / rel_file}")

    for rel_file in mirrored_files:
        if not filecmp.cmp(ROOT / rel_file, package_dir / rel_file, shallow=False):
            fail(f"Codex package file is stale: {package_dir / rel_file}")


def validate_registry_files():
    registry_dir = ROOT / "registry"
    for filename in ["sources.yaml", "skills.yaml", "roles.yaml", "agents.yaml", "workflows.yaml"]:
        path = registry_dir / filename
        if not path.exists():
            fail(f"missing {path}")

    skills = parse_simple_yaml_list(registry_dir / "skills.yaml", "skills")
    roles = parse_simple_yaml_list(registry_dir / "roles.yaml", "roles")
    sources = parse_simple_yaml_list(registry_dir / "sources.yaml", "sources")
    agents = parse_simple_yaml_list(registry_dir / "agents.yaml", "agents")
    workflows = parse_simple_yaml_list(registry_dir / "workflows.yaml", "workflows")
    provider_registry_paths = [
        registry_dir / "search-providers.yaml",
        registry_dir / "web-fetch-providers.yaml",
    ]

    source_ids = {item.get("id") for item in sources if item.get("id")}
    role_ids = {item.get("id") for item in roles if item.get("id")}
    skill_names = {item.get("name") for item in skills if item.get("name")}
    workflow_ids = {item.get("id") for item in workflows if item.get("id")}

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
        if not path_value:
            fail(f"skill {name} is missing path")
        # Registry skill paths are directories; the entrypoint must be <path>/SKILL.md.
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

    agents_text = read_text(registry_dir / "agents.yaml")
    if not re.search(r"^defaultAgent:\s*arkspace-orchestrator$", agents_text, re.MULTILINE):
        fail("registry/agents.yaml must set defaultAgent: arkspace-orchestrator")

    for item in agents:
        agent_id = item.get("id")
        path_value = item.get("path")
        if not agent_id:
            fail("registry/agents.yaml contains an agent without id")
        if not path_value:
            fail(f"agent {agent_id} is missing path")
        agent_path = ROOT / path_value
        if not agent_path.exists():
            fail(f"agent {agent_id} path does not exist: {path_value}")
        frontmatter = parse_frontmatter(agent_path)
        if frontmatter.get("name") != agent_id:
            fail(f"agent {agent_id} id must match frontmatter name in {path_value}")
        for skill in split_csv(item.get("skills")):
            if skill not in skill_names:
                fail(f"agent {agent_id} references unknown skill {skill}")
        for workflow in split_csv(item.get("workflows")):
            if workflow not in workflow_ids:
                fail(f"agent {agent_id} references unknown workflow {workflow}")

    required_workflows = {
        "lightweight-routing",
        "handoff-template",
        "quality-gates",
        "provider-capabilities",
    }
    missing_workflows = required_workflows - workflow_ids
    if missing_workflows:
        fail(f"registry/workflows.yaml is missing required workflows: {', '.join(sorted(missing_workflows))}")

    for item in workflows:
        workflow_id = item.get("id")
        path_value = item.get("path")
        if not workflow_id:
            fail("registry/workflows.yaml contains a workflow without id")
        if not path_value:
            fail(f"workflow {workflow_id} is missing path")
        if not (ROOT / path_value).exists():
            fail(f"workflow {workflow_id} path does not exist: {path_value}")

    for provider_path in provider_registry_paths:
        if not provider_path.exists():
            continue
        provider_text = read_text(provider_path)
        if not re.search(r"^default(Search|Fetch)Policy:\s*.+$", provider_text, re.MULTILINE):
            fail(f"{provider_path} must set defaultSearchPolicy or defaultFetchPolicy")
        providers = parse_simple_yaml_list(provider_path, "providers")
        for item in providers:
            provider_id = item.get("id")
            skill = item.get("skill")
            status = item.get("status")
            config_required = item.get("configRequired")
            missing_config_behavior = item.get("missingConfigBehavior")
            if not provider_id:
                fail(f"{provider_path} contains a provider without id")
            if not skill:
                fail(f"search provider {provider_id} is missing skill")
            if skill not in skill_names:
                fail(f"search provider {provider_id} references unknown skill {skill}")
            if status not in VALID_PROVIDER_STATUS:
                fail(f"search provider {provider_id} has invalid status {status}")
            if config_required and config_required not in {"true", "false"}:
                fail(f"search provider {provider_id} has invalid configRequired {config_required}")
            if config_required == "true" and not missing_config_behavior:
                fail(f"search provider {provider_id} must set missingConfigBehavior when configRequired is true")
            if item.get("recommendedEnv") and not item.get("checkCommand"):
                fail(f"search provider {provider_id} with recommendedEnv must set checkCommand")


def validate_agent_frontmatter():
    agent_files = sorted((ROOT / "agents").rglob("*.md"))
    if not agent_files:
        fail("no agents/**/*.md files found")

    workflow_registry = parse_simple_yaml_list(ROOT / "registry" / "workflows.yaml", "workflows")
    workflow_ids = {item.get("id") for item in workflow_registry if item.get("id")}

    for path in agent_files:
        data = parse_frontmatter(path)
        for key in ["name", "description", "domain"]:
            if not data.get(key):
                fail(f"{path} frontmatter is missing {key}")
        for skill in data.get("skills", []):
            if not (ROOT / "skills" / skill / "SKILL.md").exists():
                fail(f"{path} references missing skill {skill}")
        for workflow in data.get("workflows", []):
            if workflow not in workflow_ids:
                fail(f"{path} references unknown workflow {workflow}")


def validate_generated_integrations():
    codex_dir = ROOT / "integrations" / "codex" / "agents"
    if codex_dir.exists():
        if not (codex_dir / "arkspace-orchestrator.toml").exists():
            fail("integrations/codex/agents must include arkspace-orchestrator.toml")
        for path in sorted(codex_dir.glob("*.toml")):
            try:
                tomllib.loads(read_text(path))
            except tomllib.TOMLDecodeError as exc:
                fail(f"{path} is invalid TOML: {exc}")

    claude_dir = ROOT / "integrations" / "claude-code" / "agents"
    if claude_dir.exists():
        if not (claude_dir / "arkspace-orchestrator.md").exists():
            fail("integrations/claude-code/agents must include arkspace-orchestrator.md")
        for path in sorted(claude_dir.glob("*.md")):
            data = parse_frontmatter(path)
            for key in ["name", "description"]:
                if not data.get(key):
                    fail(f"{path} frontmatter is missing {key}")


def validate_platform_manifests():
    validate_json(ROOT / ".claude-plugin" / "plugin.json")
    validate_json(ROOT / ".claude-plugin" / "marketplace.json")
    validate_json(ROOT / ".codex-plugin" / "plugin.json")
    validate_json(ROOT / ".agents" / "plugins" / "marketplace.json")

    codex = json.loads(read_text(ROOT / ".codex-plugin" / "plugin.json"))
    if codex.get("skills") != "./skills/":
        fail(".codex-plugin/plugin.json must set skills to ./skills/")

    marketplace = json.loads(read_text(ROOT / ".agents" / "plugins" / "marketplace.json"))
    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        fail(".agents/plugins/marketplace.json must define plugins[]")
    ark_space = next((item for item in plugins if item.get("name") == "ark-space"), None)
    if not ark_space:
        fail(".agents/plugins/marketplace.json must include ark-space")
    source = ark_space.get("source")
    if not isinstance(source, dict) or source.get("path") != "./plugins/ark-space":
        fail(".agents/plugins/marketplace.json ark-space source.path must be ./plugins/ark-space")
    policy = ark_space.get("policy")
    if not isinstance(policy, dict):
        fail(".agents/plugins/marketplace.json ark-space must define policy")

    validate_codex_package_copy(ROOT / "plugins" / "ark-space")


def main():
    validate_skill_frontmatter()
    validate_agent_frontmatter()
    validate_registry_files()
    validate_generated_integrations()
    validate_platform_manifests()
    print("skills package validation passed")


if __name__ == "__main__":
    main()
