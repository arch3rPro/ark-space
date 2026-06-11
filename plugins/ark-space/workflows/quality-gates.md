# Quality Gates

ArkSpace uses lightweight quality gates only when risk or handoff boundaries justify them.

## Default Gate

- Requirement is clear enough to proceed.
- Owner agent is selected.
- Expected artifact is named.
- Verification method is named.
- Handoff context is preserved when another agent takes over.
- Readiness level is named when the work involves skills, packages, installed hosts, or providers.

## Risk Levels

| Risk | Examples | Required Evidence |
|---|---|---|
| Documentation-only | README, docs, examples | File references and rendered or syntax check when available |
| Registry-only | Skill, agent, workflow, provider metadata | `python3 scripts/validate-skills.py` |
| Runtime wrapper | Provider scripts, CLI dispatch, config handling | Unit tests or mocked runtime tests plus validation |
| Package/install | Plugin manifests, package mirror, generated integrations | `python3 scripts/arkspace.py doctor` and package mirror checks |
| Installed host | Claude Code or Codex skill discovery/invocation | `python3 scripts/arkspace.py smoke-test --installed-host <host>` or direct host evidence |
| Live provider | Real provider execution | Provider-specific check or live call with bounded output |

## Retry Rule

When validation fails, fix the specific failure and rerun the same check. After three failed attempts on the same issue, stop and report the blocker with evidence, attempted fixes, and the smallest next decision needed.

If a gate fails because the environment is stale, refresh or reinstall the relevant package/cache before changing source behavior. Do not treat source validation as installed-host success.

## Evidence

Prefer direct evidence: command output, tests, screenshots, generated files, source citations, or exact file references. Do not mark work complete from intent alone.

## Invocation Evidence

| Layer | Evidence |
|---|---|
| Structure | Canonical skill exists at `skills/<skill-name>/SKILL.md`, with registry metadata in `registry/skills.yaml` |
| Direct invocation contract | `directInvocation` includes `/ark-space:<skill-name>` and the README Included Skills table lists the public skill |
| Orchestrator routing contract | Routable skills define `orchestratorInvocation`, capability metadata, and any provider registry entry needed by Orchestrator |
| Package | Packaged plugin content mirrors source files after `python3 scripts/arkspace.py package-codex` and `python3 scripts/arkspace.py doctor` |
| Installed host | A restarted host session discovers the installed plugin and accepts the documented `/ark-space:...` invocation |
| Provider readiness | `provider check` succeeds for the selected provider and capability |
| Live provider execution | Real provider call returns bounded results, or the task explicitly stops before live execution |

Installed-host success must be validated in the host. It must not be inferred from local script success, provider checks, or packaged file comparison alone.

## Readiness Labels

- Source-ready: repository validation and relevant tests pass.
- Package-ready: generated package mirrors the source tree.
- Installed-host-ready: the target host cache contains the expected package content and accepts documented invocation.
- Provider-ready: provider configuration is present and the selected provider check succeeds.
- Live-provider-ready: provider configuration is present and a real provider call or provider-specific dry run succeeds.

Use the most specific readiness label supported by evidence.

## Agent-Loop Readiness

For public skills, verify the following before treating a skill as usable in an agent-loop host:

- Discovery: frontmatter `description` explains when the host should load the skill.
- Direct callability: `registry/skills.yaml` declares `directInvocation` with `/ark-space:<skill-name>`.
- Orchestrator route: routable skills declare `orchestratorInvocation` with `/ark-space:orchestrator`.
- Role ownership: every active skill role maps to a callable agent in `registry/agents.yaml`.
- Package freshness: generated plugin/package files mirror the canonical source.
- Installed host: the target host discovers and accepts the documented invocation.

Failure at any layer should produce a readiness label and blocker, not a success claim.
