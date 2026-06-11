# Improvement Backlog

This backlog records framework-level improvements that should make ArkSpace more usable, more practical, and harder to regress. It is not a release promise; use it to prioritize design and validation work before adding more provider surface area.

## P0: Usability And Correctness

- Make installed-host verification a release gate. Source validation and package checks are not enough; Claude Code and Codex caches must be checked before calling a change usable.
- Generate installed-host smoke expectations from active skills, provider registries, and runtime scripts.
- Enforce consistency between `registry/skills.yaml` role ownership, `registry/agents.yaml` skill lists, `agents/*.md` frontmatter, and generated `integrations/`.
- Decide whether `orchestrator` owns provider skills directly or only routes to agents that own them. Encode that decision in registries and validation.
- Expand provider setup UX so missing configuration leads to a clear setup choice, persistent local configuration, verification, and retry guidance.

## P1: Agent And Workflow Depth

- Add role decision rules to each callable agent: when to execute, when to hand off, when to ask one focused question, and when to stop with evidence.
- Add domain-specific operating guidance to agents without duplicating skill bodies. Examples: code project inspection, review severity, documentation scope, competitive evidence quality, and skill lifecycle governance.
- Define common workflow templates for multi-agent tasks, such as PRD-to-implementation, research-to-documentation, provider-adoption, and skill-adaptation flows.
- Extend `workflows/lightweight-routing.md` from a static intent table into conditional routing guidance for single-agent, sequential, and parallel work.
- Replace purely free-form handoff payloads with an optional structured context object for workflows that need reliable downstream consumption.

## P1: Provider And Runtime Robustness

- Make provider capability registries the source of truth for CLI dispatch where practical. Avoid duplicating provider support in separate hard-coded command maps.
- Add provider priority, explicit fallback policy, and unavailable-provider handling at the capability level.
- Add mocked runtime tests for provider wrappers, including authentication failure, rate limits, retry behavior, and multi-key rotation.
- Normalize provider setup and check behavior across API providers, self-hosted services, and CLI-backed providers.
- Keep provider-specific runtime details inside scripts and registries, not inside host-specific skill bodies.

## P1: Quality Gates

- Split quality gates by risk level: documentation-only, registry-only, runtime wrapper, package/installation, and host invocation.
- Require automated evidence where available: validation, unit tests, smoke tests, installed-host checks, live provider dry runs, or exact host invocation output.
- Define rollback or recovery guidance for failed gates.
- Track the difference between source readiness, package readiness, installed-host readiness, and live provider readiness.

## P2: State And Observability

- Record workflow state for multi-agent tasks when the task spans multiple handoffs or generated artifacts.
- Track which agent or skill was selected, why it was selected, what evidence completed the task, and where it failed.
- Add lightweight session logs for routing, provider selection, configuration misses, and validation failures.
- Add retrospective summaries for repeated failures so framework gaps become durable backlog items.

## P2: Host Adapter Expansion

- Keep `agents/`, `skills/`, and `workflows/` host-neutral.
- Treat Claude Code, Codex, and future hosts as adapter targets that translate invocation syntax, generated agent format, and available provider/tool equivalents.
- Add a host capability matrix before supporting a new host. The matrix should cover skill discovery, slash invocation, environment access, script execution, HTTP access, secret handling, and file-system access.
- Map provider behavior explicitly for each host through native tools or the ArkSpace runtime.

## Evaluation Criteria

ArkSpace is meaningfully usable only when these are true:

- A user can discover and invoke public skills in a fresh Claude Code or Codex session.
- The Orchestrator can route common requests to the documented role and skill path.
- Provider setup persists local configuration without requiring committed secrets.
- Multi-key provider rotation works under tested failure modes.
- Validation catches registry, agent, generated integration, package, and installed-host drift.
- Documentation matches the behavior available in the installed host, not only the source tree.
