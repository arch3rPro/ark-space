# Quality Gates

ArkSpace uses lightweight quality gates only when risk or handoff boundaries justify them.

## Default Gate

- Requirement is clear enough to proceed.
- Owner agent is selected.
- Expected artifact is named.
- Verification method is named.
- Handoff context is preserved when another agent takes over.

## Retry Rule

When validation fails, fix the specific failure and rerun the same check. After three failed attempts on the same issue, stop and report the blocker with evidence, attempted fixes, and the smallest next decision needed.

## Evidence

Prefer direct evidence: command output, tests, screenshots, generated files, source citations, or exact file references. Do not mark work complete from intent alone.

## Invocation Evidence

| Layer | Evidence |
|---|---|
| Structure | Canonical skill exists at `skills/<skill-name>/SKILL.md`, with registry metadata in `registry/skills.yaml` |
| Direct invocation contract | `directInvocation` includes `$ark-space:<skill-name>` and the README Included Skills table lists the public skill |
| Orchestrator routing contract | Routable skills define `orchestratorInvocation`, capability metadata, and any provider registry entry needed by Orchestrator |
| Package | Packaged plugin content mirrors source files after `python3 scripts/arkspace.py package-codex` and `python3 scripts/arkspace.py doctor` |
| Installed host | A restarted host session discovers the installed plugin and accepts the documented `$ark-space:...` invocation |

Installed-host success must be validated in the host. It must not be inferred from local script success, provider checks, or packaged file comparison alone.
