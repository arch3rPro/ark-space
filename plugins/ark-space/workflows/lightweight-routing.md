# Lightweight Routing

ArkSpace routes work by intent, artifact, and risk.

## Routing Order

1. Identify the user's primary intent.
2. Select the smallest useful callable agent.
3. Select the skill set required by that agent.
4. For web work, select the capability, then follow `workflows/provider-capabilities.md` before execution.
5. Ask one focused question only when a wrong route would materially change the result.

## Default Routes

| Intent | Agent |
|---|---|
| Implement, refactor, test, debug | `agents/code/code-engineer.md` |
| Review code or assess regressions | `agents/code/code-reviewer.md` |
| Write or improve documentation | `agents/docs/doc-writer.md` |
| Work with notes, Obsidian, web search, URL extraction, or knowledge files | `agents/docs/knowledge-manager.md` |
| Shape requirements, scope, PRDs, or acceptance criteria | `agents/product/prd-planner.md` |
| Compare products, competitors, market claims, or public evidence | `agents/product/competitive-analyst.md` |
| Plan milestones, tasks, risks, or delivery structure | `agents/project/project-manager.md` |
| Create, adapt, validate, or govern skills | `agents/skills/skill-manager.md` |

## Escalation

Use design-first handling when the task changes shared structure, creates a new workflow, spans multiple domains, or needs explicit approval before implementation.
