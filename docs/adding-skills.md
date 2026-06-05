# Adding Skills

Use `skill-manager` when adding, adapting, validating, or assigning skills.

## New Local Skill

1. Create `skills/<skill-name>/SKILL.md`.
2. Add frontmatter with `name` and `description`.
3. Add an entry to `registry/skills.yaml` with `syncMode: local`.
4. Assign the skill to one or more roles.
5. Run `python3 scripts/validate-skills.py`.

## Mirrored Skill

Use `syncMode: mirror` when the local copy should stay close to upstream.

Record the upstream in `registry/sources.yaml`.

## Adapted Skill

Use `syncMode: adapted` when the skill started from another project but has been changed for this package.

Review upstream updates selectively instead of applying them automatically.

## Reference-Only Source

Record reference-only projects in `registry/sources.yaml` with `syncPolicy: reference-only`. Do not add them to `registry/skills.yaml` unless they are explicitly promoted into a local skill.
