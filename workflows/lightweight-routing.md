# Lightweight Routing

ArkSpace routes work by intent, artifact, risk, and readiness. The host agent loop decides whether to invoke a skill or agent; ArkSpace keeps that decision surface small and verifiable.

## Routing Order

1. Identify the user's primary intent.
2. Select the smallest useful callable agent.
3. Select the skill set required by that agent.
4. For web work, select the capability, then follow `workflows/provider-capabilities.md` before execution.
5. Check whether the selected path is ready: skill discoverability, direct invocation, provider configuration, package freshness, or installed-host availability.
6. Execute, hand off, or stop with the smallest actionable blocker.
7. Ask one focused question only when a wrong route would materially change the result.

## Agent-Loop Route Cycle

Use this cycle for Orchestrator-routed tasks:

```text
classify intent
  -> choose owner role
  -> choose workflow shape
  -> choose capability and provider when needed
  -> check readiness
  -> execute or stop
  -> verify evidence
```

The Orchestrator should not expand into a large plan when a direct skill invocation or single owner role can finish the task. It should also not mark a task complete when the host cannot discover the selected skill, a provider is not configured, or an installed package is stale.

## Route Shape

Use the simplest route that can produce verified output.

| Shape | Use When | Pattern |
|---|---|---|
| Single agent | One domain owns the artifact | Orchestrator -> owner agent -> evidence |
| Sequential workflow | Work has dependent phases | Orchestrator -> planner/researcher -> implementer/writer -> reviewer/gate |
| Parallel workflow | Independent research or review tracks can run without shared state | Orchestrator -> independent owners -> merge evidence |
| Stop and report | Required skill, host support, provider config, or evidence is unavailable | Orchestrator -> blocker report -> smallest next action |

## Default Routes

| Intent | Agent |
|---|---|
| Implement, refactor, test, debug | `agents/code/code-engineer.md` |
| Review code or assess regressions | `agents/code/code-reviewer.md` |
| Write or improve documentation | `agents/docs/doc-writer.md` |
| Work with notes, Obsidian, Bases, Canvas, Kanban, or knowledge files | `agents/docs/knowledge-manager.md` |
| Web search, source discovery, URL extraction, or general web research | `agents/docs/web-researcher.md` |
| Shape requirements, scope, PRDs, or acceptance criteria | `agents/product/prd-planner.md` |
| Compare products, competitors, market claims, or public evidence | `agents/product/competitive-analyst.md` |
| Plan milestones, tasks, risks, or delivery structure | `agents/project/project-manager.md` |
| Create, adapt, validate, or govern skills | `agents/skills/skill-manager.md` |

## Escalation

Use design-first handling when the task changes shared structure, creates a new workflow, spans multiple domains, or needs explicit approval before implementation.

Escalate from direct skill execution to Orchestrator when the caller did not name a skill, the request crosses domains, provider choice matters, configuration is missing, or verification requires more than one owner role.

## Workflow Templates

| Template | Flow |
|---|---|
| PRD to implementation | `prd-planner` clarifies scope -> `code-engineer` implements -> `code-reviewer` checks risk -> `doc-writer` updates docs when needed |
| Research to documentation | `web-researcher` gathers and fetches sources -> `doc-writer` writes the artifact -> quality gate verifies source/file references |
| Competitive evidence | `competitive-analyst` evaluates evidence -> optional `web-researcher` gathers hard-to-fetch sources -> optional `prd-planner` converts findings into product decisions |
| Skill adoption | `skill-manager` records source and registry metadata -> `code-engineer` implements runtime scripts when needed -> `skill-manager` validates package and installed-host evidence |
| Provider setup | `provider-manager` checks configuration -> setup flow persists local config -> original owner retries the requested provider task |

## Provider Routing Boundary

The Orchestrator routes provider work; it does not need to own every provider skill directly. Provider skills should belong to the agent roles that execute the work. Keep `registry/skills.yaml`, `registry/agents.yaml`, and `agents/*.md` aligned so this boundary is enforceable.

Host-native search, fetch, browser, or file tools are outside ArkSpace provider routing unless they are explicitly represented by an ArkSpace skill and registry entry. If a host-native fallback is used after setup is declined or blocked, label the output as outside ArkSpace provider execution.
