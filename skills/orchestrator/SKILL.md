---
name: orchestrator
description: Use when a user invokes ArkSpace, asks for general help, a cross-domain task, role selection, skill selection, provider routing, web search/fetch through ArkSpace, or when task scope is unclear.
---

# Orchestrator

Route work before expanding process. When invoked as `ark-space:orchestrator`, act as the ArkSpace entrypoint, not as a generic host assistant.

Use the lightest role and workflow that can safely complete the task. Route first by user intent, then by artifact type, then by risk. Escalate only when the task crosses domains, changes shared structure, requires long-term maintainability, or has unclear success criteria.

## Entry Contract

ArkSpace work runs through ArkSpace roles, workflows, skills, and registries. Host-native capabilities are not ArkSpace providers.

For any capability represented by a provider registry, use that registry as the authority before execution:

1. Choose the role from `roles/` or the default route table.
2. Choose the capability, such as `web_search` or `web_fetch`.
3. Read the matching provider registry, such as `registry/search-providers.yaml`.
4. Select the highest-priority active provider that matches the role, capability, and privacy requirements.
5. Run the provider's `checkCommand` when configuration state matters.
6. If a selected provider requires configuration and the check fails, route to `provider-manager` setup and stop before producing capability results.
7. Continue only after the provider check succeeds, another registered provider passes the same checks, or the user explicitly asks to bypass ArkSpace provider routing.
8. When stopped for missing configuration, present the missing capability, the setup command, and the value needed from the user before offering alternatives. If the user declines, defers, or cannot complete setup and still wants results, ask whether to continue with a clearly labeled non-ArkSpace fallback.

## Routing Workflow

1. Identify the primary task domain: code, docs, product, project, skills, knowledge management, research, or cross-domain.
2. Select the smallest useful role set from `roles/`.
3. For web tasks, choose the role first, then use `workflows/provider-capabilities.md` and the provider registry before execution.
4. Use one role for simple work.
5. Use multiple roles only when the task naturally crosses domains.
6. Ask one focused question when routing is unclear and a wrong choice would change the outcome.
7. Hand off skill-library maintenance to `skill-manager`.

## Default Routes

| User intent | Route |
|---|---|
| Implement, refactor, test, debug | `code/code-engineer` |
| Review code or assess regressions | `code/code-reviewer` |
| CI, PR, release-prep discussion, repository hygiene | `code/repo-maintainer` |
| Write new documentation | `docs/doc-writer` |
| Improve existing documentation | `docs/doc-editor` |
| Work with Obsidian, notes, Bases, Canvas, or knowledge files | `docs/knowledge-manager` |
| Web search, source discovery, general research, SearXNG | `docs/knowledge-manager` |
| Read, fetch, summarize, or extract a provided URL | `docs/knowledge-manager` |
| Shape requirements or PRDs | `product/prd-planner` |
| Build or evaluate a product demo | `product/demo-designer` |
| Compare products, competitors, market claims, or public evidence | `product/competitive-analyst` |
| Plan milestones, tasks, ownership, or delivery | `project/project-manager` |
| Coordinate handoffs, status, or multi-step delivery | `project/delivery-coordinator` |
| Create, adapt, validate, or sync skills | `skills/skill-manager` |

## Web Capability Selection

Web work splits into two provider capabilities:

| Capability | Input | Output | Registry |
|---|---|---|---|
| `web_search` | Query | Candidate URLs, snippets, source metadata | `registry/search-providers.yaml` |
| `web_fetch` | URL | Readable page content, Markdown/text, metadata | `registry/web-fetch-providers.yaml` |

Search and fetch are often chained: use `web_search` to discover candidate URLs, then `web_fetch` to read the selected primary sources.

Selection order:

1. Use the provider or skill the user explicitly names.
2. Read the provider registry entry before first use.
3. Select only registered active providers that match the requested capability.
4. If the selected provider has `checkCommand`, run it before using the provider.
5. If provider configuration is missing, use `provider-manager` to guide or run setup instead of asking the user to find config files by hand.
6. If `configRequired: true` and configuration is missing, stop at setup guidance before producing search or fetch results.
7. For sensitive, internal, personal, credential-bearing, or embargoed queries, use only a configured private/self-hosted provider or ask before public search.
8. Prefer configured API-backed or private providers when their required environment is available.
9. Use the highest-priority active provider that fits the role and query.
10. If a search provider only returns snippets, fetch or open primary sources before making factual claims.
11. Do not use search when the user already provided the exact URL unless discovery is explicitly needed.

When a provider entry includes `checkCommand`, run it when configuration state matters. Treat missing configuration as a routing signal: use `provider-manager` setup guidance or ask for the missing endpoint or key reference. Another ArkSpace provider is valid only if it is also registered, active, capability-compatible, and passes its own configuration check. Missing provider configuration is not a completed search or fetch task. Host-native fallback can be offered only after setup is declined, blocked, or explicitly bypassed, and it must be labeled as outside ArkSpace provider execution.

## Search Request Example

```text
User: [$ark-space:orchestrator] 帮我查询 claude-code-everything 项目
Route: docs/knowledge-manager -> web_search -> registry/search-providers.yaml -> highest-priority active provider -> checkCommand
If required configuration is missing: hand off to provider-manager setup and do not return project search results yet.
```

## Escalation Rules

Use direct execution for narrow, low-risk requests with clear success criteria.

Use design-first handling when the task changes shared structure, creates a new workflow, spans multiple domains, or needs user approval before implementation.

Use a multi-role flow when each role has a distinct artifact. Example: `product/prd-planner` creates requirements, `code/code-engineer` implements, and `docs/doc-writer` updates documentation.

Do not create a large plan for a small single-file task unless the user asks for planning.

## Handoff Format

When handing off to a role, include:

```text
Role: <role id>
Reason: <why this role is the smallest useful fit>
Inputs: <files, user request, constraints>
Expected output: <artifact or decision>
Escalation: <when to return to Orchestrator>
```
