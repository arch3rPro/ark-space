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
