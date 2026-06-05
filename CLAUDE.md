# Claude Code Guidance

ArkSpace packages reusable agent skills, roles, registries, and plugin metadata for Claude Code and Codex.

## Start Here

- Default to the `orchestrator` skill/role for lightweight routing.
- Use `skill-manager` for creating, adapting, validating, or assigning skills.
- Read `AGENTS.md` for cross-agent project rules; this file adds Claude Code-specific orientation.

## Repository Rules

- Keep skills in `skills/<skill-name>/SKILL.md`.
- Keep callable agent role sources in `agents/`.
- Keep workflow protocols in `workflows/`.
- Keep generated host-native agent outputs in `integrations/`.
- Keep legacy role metadata in `roles/` during migration.
- Keep source, role, and skill governance in `registry/`.
- Keep Claude plugin metadata in `.claude-plugin/`.
- Keep Codex plugin metadata in `.codex-plugin/`.
- Do not duplicate skill bodies per platform.

## Validation

After changing package structure, skills, roles, registries, manifests, README, or agent guidance, run:

```bash
python3 scripts/validate-skills.py
```

For structural changes, run:

```bash
python3 scripts/arkspace.py doctor
```

After changing plugin JSON, run:

```bash
python3 -m json.tool .claude-plugin/plugin.json >/dev/null
python3 -m json.tool .claude-plugin/marketplace.json >/dev/null
python3 -m json.tool .codex-plugin/plugin.json >/dev/null
```

## Release Boundary

Do not publish plugins, push branches, create tags, run release workflows, or change versions unless the user explicitly asks for release/version work.

## Private Overlay Boundary

Do not commit:

- `overlays/personal.yaml`
- `overlays/private-skills.yaml`
- `docs/superpowers/`

Commit only overlay examples and documentation.

## Claude Code Notes

- `.claude-plugin/plugin.json` describes this package for Claude Code.
- `.claude-plugin/marketplace.json` describes local marketplace packaging.
- Claude Code should consume the shared `skills/` tree rather than a separate `.claude/skills` copy.
- Callable Claude Code agent files are generated from `agents/` into `integrations/claude-code/agents/`.
- Do not edit generated integrations by hand; update `agents/` and regenerate.
