#!/usr/bin/env python3
import argparse
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = ROOT / "agents"
INTEGRATIONS_DIR = ROOT / "integrations"
SUPPORTED_HOSTS = ("codex", "claude-code")


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def parse_frontmatter(path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path.relative_to(ROOT)} is missing frontmatter")
    try:
        _, frontmatter, body = text.split("---", 2)
    except ValueError as exc:
        raise ValueError(f"{path.relative_to(ROOT)} has unterminated frontmatter") from exc

    data = {}
    current_list = None
    for raw in frontmatter.splitlines():
        if not raw.strip():
            continue
        if raw.startswith("  - ") and current_list:
            data[current_list].append(raw[4:].strip())
            continue
        if raw.endswith(":") and not raw.startswith(" "):
            key = raw[:-1].strip()
            data[key] = []
            current_list = key
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
    return data, body.lstrip()


def slugify(value):
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def toml_string(value):
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\b", "\\b")
        .replace("\t", "\\t")
        .replace("\n", "\\n")
        .replace("\f", "\\f")
        .replace("\r", "\\r")
    )
    return f'"{escaped}"'


def agent_files():
    if not AGENTS_DIR.exists():
        fail("agents/ directory does not exist")
    return sorted(AGENTS_DIR.rglob("*.md"))


def validate_agent_data(path, data):
    for key in ("name", "description"):
        if key not in data or not data[key]:
            raise ValueError(f"{path.relative_to(ROOT)} missing {key}")


def codex_toml(data, body):
    return (
        f"name = {toml_string(data['name'])}\n"
        f"description = {toml_string(data['description'])}\n"
        f"developer_instructions = {toml_string(body.rstrip() + chr(10))}\n"
    )


def claude_agent(data, body):
    return (
        "---\n"
        f"name: {data['name']}\n"
        f"description: {data['description']}\n"
        "---\n\n"
        f"{body.rstrip()}\n"
    )


def render(host):
    outputs = {}
    for path in agent_files():
        data, body = parse_frontmatter(path)
        validate_agent_data(path, data)
        slug = slugify(data["name"])
        if host == "codex":
            target = INTEGRATIONS_DIR / "codex" / "agents" / f"{slug}.toml"
            outputs[target] = codex_toml(data, body)
        elif host == "claude-code":
            target = INTEGRATIONS_DIR / "claude-code" / "agents" / f"{slug}.md"
            outputs[target] = claude_agent(data, body)
        else:
            raise ValueError(f"unsupported host: {host}")
    return outputs


def validate_outputs(host, outputs):
    if host == "codex":
        for content in outputs.values():
            tomllib.loads(content)


def write_outputs(outputs):
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def check_outputs(outputs):
    stale = []
    for path, expected in outputs.items():
        if not path.exists() or path.read_text(encoding="utf-8") != expected:
            stale.append(path)
    for path in stale:
        print(f"stale: {path.relative_to(ROOT)}", file=sys.stderr)
    return 1 if stale else 0


def main():
    parser = argparse.ArgumentParser(description="Generate host-native ArkSpace agent files.")
    parser.add_argument("--host", choices=(*SUPPORTED_HOSTS, "all"), default="all")
    parser.add_argument("--check", action="store_true", help="check generated files without writing")
    args = parser.parse_args()

    hosts = SUPPORTED_HOSTS if args.host == "all" else (args.host,)
    status = 0
    for host in hosts:
        outputs = render(host)
        validate_outputs(host, outputs)
        if args.check:
            status |= check_outputs(outputs)
        else:
            write_outputs(outputs)
            print(f"generated {len(outputs)} {host} agents")
    raise SystemExit(status)


if __name__ == "__main__":
    main()
