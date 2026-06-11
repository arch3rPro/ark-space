# Agent Loop Model

ArkSpace is designed for AI-agent hosts that run an agent loop: the host loads compact context, the model decides whether to answer or call capabilities, capability results return to the model, and the loop repeats until the task is complete.

ArkSpace does not replace that loop. It gives the loop a smaller and more reliable decision surface.

## Mapping

| Agent-loop part | ArkSpace layer | Responsibility |
|---|---|---|
| Initial context | README, `AGENTS.md`, `CLAUDE.md`, plugin metadata | Explain what ArkSpace is and how it is invoked. |
| Skill descriptions | `skills/<name>/SKILL.md` frontmatter | Make skills discoverable before their full bodies are loaded. |
| Role behavior | `agents/` | Define the owner, scope, stop conditions, and quality expectations for a task type. |
| Reusable protocols | `workflows/` | Route, hand off, select providers, and verify completion without duplicating skill bodies. |
| Capability metadata | `registry/` | Record skill inventory, role ownership, provider capabilities, priorities, setup commands, and source provenance. |
| Deterministic execution | `scripts/` and provider CLIs | Check configuration, run provider calls, rotate keys, and return compact evidence. |
| Host adapters | `.claude-plugin/`, `.codex-plugin/`, `integrations/`, `plugins/ark-space/` | Translate the same canonical skills and agents into host-native packaging and invocation. |

## Runtime Shape

```text
user request
  -> host agent loop sees ArkSpace skill descriptions
  -> direct skill or /ark-space:orchestrator is selected
  -> Orchestrator classifies intent and chooses the smallest owner role
  -> workflow selects capability and provider metadata when needed
  -> provider check verifies local configuration
  -> runtime script or host tool executes the capability
  -> result returns to the agent loop
  -> quality gate decides whether to finish, retry, hand off, or stop
```

## Layer Boundaries

- **Agent** owns task strategy. It decides what good output looks like for code, docs, product, project, knowledge, or skill-governance work.
- **Skill** owns reusable context. It should be callable directly and concise enough for the host to load only when needed.
- **Workflow** owns repeatable process. It keeps routing, provider selection, handoff, and verification consistent across agents.
- **Provider** owns an external capability contract. A provider can search, fetch, crawl, extract, monitor, or provide code context, but it is selected after role routing.
- **Runtime script** owns deterministic execution. It should check configuration, run provider calls, and return bounded output.
- **Host adapter** owns syntax and packaging. Claude Code, Codex, and future hosts can expose different invocation surfaces without changing canonical skill bodies.

## Readiness States

ArkSpace uses explicit readiness labels so source changes are not confused with real host usability.

| Label | Meaning |
|---|---|
| `source-ready` | Repository validation and focused tests pass. |
| `package-ready` | Generated plugin/package content mirrors the source tree. |
| `installed-host-ready` | The target host discovers the installed plugin and accepts the documented invocation. |
| `provider-ready` | Required provider configuration resolves locally. |
| `live-provider-ready` | A real provider call or provider-specific dry run succeeds. |

A task is only complete at the readiness level proven by evidence. For example, a provider script passing locally is not evidence that a slash invocation works in a refreshed host session.

## Design Rules

- Keep canonical skill bodies host-neutral.
- Treat skill frontmatter descriptions as routing-critical API, not decoration.
- Route by role first, then workflow, then provider capability.
- Keep provider configuration outside public package files.
- Stop at the smallest actionable blocker when the selected skill, provider, or host invocation is unavailable.
- Label host-native fallback results as outside ArkSpace execution.
