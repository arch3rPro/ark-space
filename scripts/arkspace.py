#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(args):
    return subprocess.call(args, cwd=ROOT)


def main():
    parser = argparse.ArgumentParser(prog="arkspace")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("validate")

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
    smoke.add_argument("--host", choices=["codex", "claude-code"], required=True)
    smoke.add_argument("--local", action="store_true")

    sub.add_parser("doctor")

    args = parser.parse_args()
    if args.command == "validate":
        return run([sys.executable, "scripts/validate-skills.py"])
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
        cmd = [sys.executable, "scripts/smoke-test-callability.py", "--host", args.host]
        if args.local:
            cmd.append("--local")
        return run(cmd)
    if args.command == "doctor":
        status = 0
        status |= run([sys.executable, "scripts/validate-skills.py"])
        status |= run([sys.executable, "scripts/convert-agents.py", "--host", "all", "--check"])
        status |= run([sys.executable, "scripts/smoke-test-callability.py", "--host", "codex", "--local"])
        status |= run([sys.executable, "scripts/smoke-test-callability.py", "--host", "claude-code", "--local"])
        return status
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
