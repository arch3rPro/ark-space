# Roadmap And Development Plan

[中文](roadmap.zh-CN.md) | English

ArkSpace is moving from a useful local skills collection into a durable multi-host agent skills package. The roadmap is outcome-focused: each phase states the user or maintainer outcome first, then the development work needed to get there.

## Product Direction

ArkSpace should make agent work easier to route, reuse, verify, and install across hosts without fragmenting skill bodies by platform.

The project keeps four durable product promises:

- Skills remain the public capability contract in `skills/<skill-name>/SKILL.md`.
- Callable agents remain role owners in `agents/`, with generated host outputs under `integrations/`.
- Workflows and registries make routing, provider selection, source governance, and validation explicit.
- Private provider configuration and personal overlays stay outside the public package.

## Roadmap

| Phase | Outcome | Primary Work | Success Signal |
|---|---|---|---|
| 1. Invocation ergonomics | Users can call agents and skills with short, predictable names. | Keep agent names aligned with file names, docs, registries, generated integrations, and installed-host smoke tests. | `orchestrator`, `knowledge-manager`, and other short agent names are discoverable in Codex and Claude Code adapters without stale `arkspace-*` aliases. |
| 2. Package reliability | Maintainers can change canonical sources without drifting generated packages. | Harden `convert`, `package-codex`, validation, stale-copy checks, and local cache refresh guidance. | `python3 scripts/arkspace.py doctor` clearly separates source, package, integration, and installed-host readiness. |
| 3. Provider readiness | Web and research skills fail with actionable setup guidance instead of silent provider substitution. | Improve provider config diagnostics, key rotation checks, setup recovery, and capability-specific provider registries. | Missing SearXNG, Exa, Firecrawl, or Tavily configuration produces a clear setup path and no unsupported fallback claims. |
| 4. Knowledge management depth | Obsidian-related skills remain useful inside the broader ArkSpace package. | Clarify when to use direct file edits versus `obsidian` CLI, keep Bases, Kanban, Canvas, and Markdown skills aligned with Obsidian behavior, and add examples where workflow ambiguity exists. | Knowledge-management tasks route cleanly between `knowledge-manager`, `personal-assistant`, and direct Obsidian skills. |
| 5. Host expansion | New hosts can consume the same skills and agents without duplicating behavior. | Document adapter requirements, add generator targets only when a host contract is clear, and keep host-specific metadata out of canonical skill bodies. | A new host adapter can be added by extending generation and validation, not by forking skills. |
| 6. Contributor readiness | External contributors can add skills, providers, and agents without breaking governance contracts. | Tighten `docs/adding-skills.md`, registry examples, source provenance rules, and validation error messages. | A new active public skill can be added with clear source governance, role ownership, invocation metadata, and passing validation. |

## Development Plan

### Workstream 1: Invocation And Agent Names

Goal: make callable agents easy to remember and consistent across source, generated, packaged, and installed states.

Planned work:

- Keep `registry/agents.yaml` ids equal to agent frontmatter `name` values.
- Keep generated files named from the short agent name.
- Keep handoff references inside `agents/` using the same short names.
- Keep callability smoke tests focused on the actual names users invoke.

Validation:

```bash
python3 scripts/validate-skills.py
python3 scripts/arkspace.py doctor
python3 scripts/arkspace.py doctor --installed-host codex
```

Run the installed-host gate only after refreshing the local host cache.

### Workstream 2: Source, Package, And Cache Integrity

Goal: make it obvious whether a change is valid in source only, package output, or an installed host cache.

Planned work:

- Treat `plugins/ark-space/` as generated package output from canonical root sources.
- Keep `integrations/` generated from `agents/`.
- Improve stale-copy checks when package files differ from canonical files.
- Keep maintenance docs explicit about when to run `convert`, `package-codex`, `doctor`, and cache refresh commands.

Validation:

```bash
python3 scripts/arkspace.py convert --host all
python3 scripts/arkspace.py package-codex
python3 scripts/arkspace.py doctor
```

### Workstream 3: Provider Runtime Maturity

Goal: make provider-backed skills reliable enough for regular research and web workflows.

Planned work:

- Keep capability registries split by task shape: search, fetch, map, crawl, structured extract, interaction, monitor, deep research, code context, and related pages.
- Improve provider checks so each capability verifies the exact helper it needs.
- Keep private endpoint and secret handling outside committed package files.
- Preserve explicit missing-configuration behavior instead of pretending a provider ran.

Validation:

```bash
python3 scripts/arkspace.py provider check searxng --capability web_search
python3 scripts/arkspace.py provider check exa --capability web_search
python3 scripts/arkspace.py provider check tavily --capability web_search
python3 scripts/arkspace.py provider check firecrawl --capability web_search
```

Provider checks prove local configuration resolution. They do not replace end-to-end host smoke tests.

### Workstream 4: Obsidian And Knowledge Management

Goal: preserve the original Obsidian value while keeping ArkSpace general-purpose.

Planned work:

- Document which Obsidian operations require `obsidian` CLI and which are direct file edits.
- Keep `obsidian-markdown`, `obsidian-bases`, `obsidian-kanban`, `obsidian-cli`, and `json-canvas` focused and composable.
- Keep `personal-assistant` centered on Kanban-first personal execution.
- Keep `knowledge-manager` centered on broader vault organization, Bases, Canvas, notes, and taxonomy.

Validation:

- For file-level changes, validate Markdown, YAML, JSON, and board structure.
- For app/runtime changes, verify through `obsidian` CLI against a running Obsidian instance.
- For package changes, run the normal ArkSpace validation gates.

### Workstream 5: Documentation And Contributor Flow

Goal: make the project easier to maintain without tribal knowledge.

Planned work:

- Keep README user-facing and concise.
- Keep `docs/` focused on architecture, invocation, platform support, provider setup, roadmap, and maintenance.
- Keep `AGENTS.md` and `CLAUDE.md` agent-facing.
- Keep source governance rules visible when adding or adapting skills.

Validation:

```bash
python3 scripts/validate-skills.py
```

Run the broader doctor command when documentation changes reflect structural behavior, generated outputs, package layout, or host support.

## Release Readiness Checklist

Before publishing, tagging, or sending a version, list the workflow-level checks that actually ran:

- Source registry and skill validation.
- Generated integration freshness.
- Codex package freshness.
- Direct invocation smoke tests for Codex and Claude Code.
- Installed-host smoke tests for each host claimed as ready.
- Provider capability checks when the release changes provider behavior.

If any item cannot be exercised in the current environment, document that exact gap instead of calling the release fully verified.

## Not In Scope Yet

- Duplicating skill bodies for a specific host.
- Publishing private overlays or local provider secrets.
- Treating `reference/` content as runtime package content.
- Adding a new host adapter before its invocation, packaging, and validation contract is clear.
