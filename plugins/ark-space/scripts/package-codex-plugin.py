#!/usr/bin/env python3
import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "plugins" / "ark-space"
INTERNAL_PACKAGE_EXCLUDES = {
    Path("docs/improvement-backlog.md"),
}
PACKAGE_ITEMS = [
    ".codex-plugin",
    "agents",
    "docs",
    "registry",
    "roles",
    "skills",
    "scripts",
    "workflows",
    "README.md",
    "README.zh-CN.md",
    "LICENSE",
    "NOTICE.md",
]
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", "superpowers")


def copy_item(name):
    source = ROOT / name
    target = PACKAGE_DIR / name
    if source.is_dir():
        shutil.copytree(source, target, ignore=IGNORE)
    else:
        shutil.copy2(source, target)


def remove_internal_package_paths():
    for rel_path in INTERNAL_PACKAGE_EXCLUDES:
        target = PACKAGE_DIR / rel_path
        if target.exists():
            target.unlink()


def main():
    parser = argparse.ArgumentParser(
        description="Rebuild the Codex marketplace package under plugins/ark-space."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only report whether the package directory exists; use validate for drift checks.",
    )
    args = parser.parse_args()

    if args.check:
        if not PACKAGE_DIR.exists():
            raise SystemExit("Codex package directory is missing")
        print(f"Codex package directory exists: {PACKAGE_DIR.relative_to(ROOT)}")
        return 0

    if PACKAGE_DIR.exists():
        shutil.rmtree(PACKAGE_DIR)
    PACKAGE_DIR.mkdir(parents=True)

    for item in PACKAGE_ITEMS:
        copy_item(item)

    remove_internal_package_paths()

    print(f"rebuilt Codex package: {PACKAGE_DIR.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
