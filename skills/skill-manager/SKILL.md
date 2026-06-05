---
name: skill-manager
description: Manage this Agent Skills package by creating skills, recording upstream sources, assigning roles, validating registries, and guiding mirror, adapted, local, and reference-only skill updates.
---

# Skill Manager

Manage skills as durable package assets, not one-off prompt snippets.

Use this skill when creating a skill, adapting an external skill, recording upstream provenance, assigning a skill to a role, validating the skills package, or preparing a selective upstream update.

## Workflow

1. Classify the request: create, adapt, mirror, validate, assign role, document, or review upstream changes.
2. Check `registry/skills.yaml`, `registry/sources.yaml`, and `registry/roles.yaml` before editing.
3. Keep skill bodies under `skills/<skill-name>/SKILL.md`.
4. Record source provenance for every reused or adapted skill.
5. Assign each active skill to at least one role unless it is intentionally standalone.
6. Run `python3 scripts/validate-skills.py` after registry, role, manifest, or skill changes.

## Sync Modes

| syncMode | Meaning | Update behavior |
|---|---|---|
| `mirror` | External skill kept close to upstream | Prefer direct sync, preserve upstream behavior, record version or commit when available |
| `adapted` | External skill changed for this package | Compare upstream changes and merge selectively |
| `local` | Skill created here | Maintain directly |
| `reference-only` | Upstream used only as design reference | Do not publish it as a local skill unless explicitly promoted |

## Creating a Skill

1. Create `skills/<skill-name>/SKILL.md`.
2. Add YAML frontmatter with `name` and `description`.
3. Keep instructions host-neutral unless the skill is intentionally platform-specific.
4. Add the skill to `registry/skills.yaml`.
5. Add or update any needed source in `registry/sources.yaml`.
6. Assign the skill to one or more roles.
7. Run validation.

## Adapting an External Skill

1. Record the upstream in `registry/sources.yaml`.
2. Add the skill with `syncMode: adapted`.
3. Keep a concise note about why it diverges from upstream.
4. Preserve license and attribution requirements.
5. Review upstream updates manually before merging.

## Validation

Run:

```bash
python3 scripts/validate-skills.py
```

Validation must pass before committing registry, role, skill, or manifest changes.
