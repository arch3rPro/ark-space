# Architecture

ArkSpace is a creative workspace for orchestrating reusable agent skills, callable agent roles, and workflows.

The canonical skill source is `skills/<skill-name>/SKILL.md`. Claude Code, Codex, and future hosts should consume the same skill files instead of maintaining platform-specific copies.

## Layers

- `skills/`: callable skill instructions and reusable capabilities.
- `agents/`: callable role source files shared by host adapters.
- `workflows/`: host-neutral routing, handoff, quality, and provider-capability protocols.
- `integrations/`: generated host-native agent outputs.
- `roles/`: existing role metadata kept during migration.
- `registry/`: governance metadata for skills, agents, workflows, providers, roles, and upstream sources.
- `.agents/plugins/marketplace.json`: Codex marketplace catalog that points at `plugins/ark-space/` as the installable plugin package.
- `plugins/ark-space/`: Codex marketplace package copy. It must mirror the root `.codex-plugin/`, `skills/`, `scripts/`, README, license, and notice files; validation fails if it drifts.
- `.claude-plugin/`: Claude Code plugin metadata.
- `.codex-plugin/`: Codex plugin metadata.
- `overlays/`: examples and documentation for private local customization.
- `reference/`: optional local or tracked area for upstream projects used as design reference.

## Runtime Entry

ArkSpace has two runtime entrypoints:

- `skills/orchestrator/SKILL.md` for hosts that activate skills.
- `agents/orchestrator.md` for hosts that activate agents or subagents.

The Orchestrator uses `workflows/lightweight-routing.md` to choose the smallest useful callable agent and skill set.

## Callable Agents

Agents are role owners. They compose skills and workflows without duplicating skill bodies.

Initial agents cover code, docs, product, project, knowledge management, and skill governance. Their inventory lives in `registry/agents.yaml`.

## Workflows

Workflows are reusable protocols:

- `workflows/lightweight-routing.md`: routing and escalation.
- `workflows/handoff-template.md`: role-to-role context transfer.
- `workflows/quality-gates.md`: evidence, retry, and completion checks.
- `workflows/provider-capabilities.md`: `web_search` and `web_fetch` capability selection.

## Web Providers

Web skills are selected as providers after role routing.

`web_search` takes a query and returns candidate URLs, snippets, and source metadata. `web_fetch` takes a URL and returns readable content such as Markdown, text, or extraction metadata.

A general source-discovery request routes to `agents/docs/knowledge-manager.md`. A competitor or market-evidence request routes to `agents/product/competitive-analyst.md`. Those agents then select a configured provider skill such as `searxng-search` for search or `defuddle` for fetch.

Provider configuration is metadata-driven. Registry entries declare whether configuration is required, which environment variables are recommended or compatible, how to check availability, and what to do when configuration is missing. Actual URLs, API keys, and private endpoints stay in the host environment or local ignored settings.

## Generated Integrations

Run:

```bash
python3 scripts/arkspace.py convert --host all
```

This regenerates host-native agent files under `integrations/`. Do not edit generated files directly.

## Process Documents

Local process specs and plans may live under ignored `docs/superpowers/` while working. They are not repository content and should not be committed.

## Existing Obsidian Skills

The Obsidian skills remain active. They are classified as documentation and knowledge-management tooling rather than the identity of the whole repository.
