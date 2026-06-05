# Agent Guidance

ArkSpace is a creative workspace for orchestrating reusable agent skills, roles, and workflows. Follow these instructions when working in this project.

## Project Contract

- Keep canonical skills in `skills/<skill-name>/SKILL.md`.
- Do not create separate Claude-specific or Codex-specific skill bodies.
- Use `.claude-plugin/` and `.codex-plugin/` only for platform metadata.
- Use `roles/` for role composition and routing metadata.
- Use `registry/` for source governance, role ownership, and skill inventory.
- Keep personal or private configuration out of the public package; use ignored files under `overlays/`.

## Default Workflow

- Use `orchestrator` for lightweight task routing.
- Use `skill-manager` for skill creation, adaptation, registry updates, source tracking, and package validation.
- Prefer the smallest safe change that satisfies the request.
- Ask one focused question only when a wrong assumption would materially change the result.
- For cross-domain or structural changes, design first before editing.

## Validation

Run this after changes to skills, roles, registries, plugin manifests, README, docs, or agent guidance:

```bash
python3 scripts/validate-skills.py
```

For plugin manifest edits, also validate JSON:

```bash
python3 -m json.tool .claude-plugin/plugin.json >/dev/null
python3 -m json.tool .claude-plugin/marketplace.json >/dev/null
python3 -m json.tool .codex-plugin/plugin.json >/dev/null
```

## Source Governance

Use these modes consistently:

- `mirror`: keep close to upstream.
- `adapted`: preserve upstream provenance but merge updates selectively.
- `local`: maintain directly in this repository.
- `reference-only`: record in `registry/sources.yaml`; do not add to `registry/skills.yaml` unless promoted into a local skill.

When adapting external work, preserve license and attribution requirements.

## Boundaries

- Do not publish, tag, push releases, or run version workflows unless explicitly requested.
- Do not delete existing Obsidian skills; they are knowledge-management tooling.
- Do not commit private overlay files such as `overlays/personal.yaml` or `overlays/private-skills.yaml`.
- Do not treat `reference/` as runtime package content.
- Leave unrelated untracked or user-created files alone.

## Documentation Style

- README is user-facing project documentation.
- `docs/` explains architecture and maintenance.
- `AGENTS.md` and `CLAUDE.md` are agent-facing operating instructions.
- Keep public docs concise, concrete, and aligned with the current repository state.
