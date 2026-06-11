# Adding Skills

Use `skill-manager` when adding, adapting, validating, or assigning skills.

## New Local Skill

1. Create `skills/<skill-name>/SKILL.md`.
2. Add frontmatter with `name` and `description`.
3. Add an entry to `registry/skills.yaml` with `syncMode: local`.
4. Assign the skill to one or more roles.
5. Run `python3 scripts/validate-skills.py`.

## Public Skill Checklist

1. Create `skills/<skill-name>/SKILL.md`.
2. Add a `registry/skills.yaml` entry with `public: true`.
3. Set `directInvocation` and include `/ark-space:<skill-name>`.
4. Set `capabilities` for each user-visible capability.
5. Add `orchestratorInvocation` when the skill is routable through Orchestrator.
6. Add a provider registry entry for `web_search` or `web_fetch` provider skills.
7. Add a README Included Skills row.
8. Run `python3 scripts/arkspace.py doctor`.

## Mirrored Skill

Use `syncMode: mirror` when the local copy should stay close to upstream.

Record the upstream in `registry/sources.yaml`.

## Adapted Skill

Use `syncMode: adapted` when the skill started from another project but has been changed for this package.

Review upstream updates selectively and merge only the changes that fit the local adaptation.

## Reference-Only Source

Record reference-only projects in `registry/sources.yaml` with `syncPolicy: reference-only`. Add them to `registry/skills.yaml` only after they are explicitly promoted into a local skill.
