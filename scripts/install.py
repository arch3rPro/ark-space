#!/usr/bin/env python3
import argparse
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_DESTS = {
    "codex": Path.home() / ".codex" / "agents",
    "claude-code": Path.home() / ".claude" / "agents",
}

ENV_DESTS = {
    "codex": "CODEX_AGENTS_DIR",
    "claude-code": "CLAUDE_AGENTS_DIR",
}

SOURCE_DIRS = {
    "codex": ROOT / "integrations" / "codex" / "agents",
    "claude-code": ROOT / "integrations" / "claude-code" / "agents",
}


def selected_files(host, selected):
    source = SOURCE_DIRS[host]
    suffix = ".toml" if host == "codex" else ".md"
    if not source.exists():
        raise SystemExit(f"generated agents missing: {source.relative_to(ROOT)}")
    files = sorted(source.glob(f"*{suffix}"))
    if selected:
        wanted = {item.strip() for item in selected.split(",") if item.strip()}
        files = [path for path in files if path.stem in wanted or path.name in wanted]
    return files


def install(host, dest, selected, link, dry_run):
    files = selected_files(host, selected)
    if not files:
        raise SystemExit(f"no generated agents found for {host}")
    if not dry_run:
        dest.mkdir(parents=True, exist_ok=True)
    for src in files:
        target = dest / src.name
        action = "link" if link else "copy"
        print(f"{action}: {src.relative_to(ROOT)} -> {target}")
        if dry_run:
            continue
        if target.exists() or target.is_symlink():
            target.unlink()
        if link:
            target.symlink_to(src)
        else:
            shutil.copy2(src, target)
    print(f"installed {len(files)} {host} agents")


def main():
    parser = argparse.ArgumentParser(description="Install generated ArkSpace agents for a host.")
    parser.add_argument("--host", choices=["codex", "claude-code"], required=True)
    parser.add_argument("--agents", help="comma-separated generated agent stems or filenames")
    parser.add_argument("--path", type=Path)
    parser.add_argument("--link", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    env_var = ENV_DESTS[args.host]
    dest = args.path or Path(os.environ.get(env_var, DEFAULT_DESTS[args.host]))
    install(args.host, dest, args.agents, args.link, args.dry_run)


if __name__ == "__main__":
    main()
