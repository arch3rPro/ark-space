# Contributing

ArkSpace is a skills package, not a runtime service. Contributions should keep the package portable across Claude Code, Codex, and compatible Agent Skills hosts.

## Before You Start

1. Read `README.md`, `AGENTS.md`, and `docs/architecture.md`.
2. Check `registry/skills.yaml`, `registry/roles.yaml`, and `registry/sources.yaml` before changing skills or roles.
3. Keep the change focused on one problem.
4. Preserve upstream attribution and license obligations for reused or adapted skills.

## Package Rules

- Keep canonical skill content under `skills/<skill-name>/SKILL.md`.
- Do not create separate Claude-specific or Codex-specific skill bodies.
- Keep platform metadata in `.claude-plugin/` and `.codex-plugin/`.
- Keep role composition in `roles/`.
- Keep source and ownership metadata in `registry/`.
- Do not commit private overlay files.

## Adding Or Updating Skills

Use `skill-manager` for skill lifecycle changes.

For a local skill:

1. Create `skills/<skill-name>/SKILL.md`.
2. Add `name` and `description` frontmatter.
3. Add the skill to `registry/skills.yaml` with `syncMode: local`.
4. Assign it to one or more roles.
5. Run validation.

For adapted external work:

1. Record the upstream in `registry/sources.yaml`.
2. Use `syncMode: adapted` in `registry/skills.yaml`.
3. Keep a concise note about why the local version diverges.
4. Review upstream changes selectively.

## Validation

Run this before submitting changes:

```bash
python3 scripts/validate-skills.py
```

For plugin manifest changes, also run:

```bash
python3 -m json.tool .claude-plugin/plugin.json >/dev/null
python3 -m json.tool .claude-plugin/marketplace.json >/dev/null
python3 -m json.tool .codex-plugin/plugin.json >/dev/null
```

## Release Boundary

Do not publish plugins, push branches, create tags, change versions, or run release workflows unless release work is explicitly requested.
