# ArkSpace

[中文](README.zh-CN.md) | English

ArkSpace is an Agent Skills workspace for Claude Code, Codex, and compatible AI-agent hosts. It packages reusable skills, callable agent roles, workflow protocols, provider routing metadata, and host adapters so an AI agent can select focused, reusable context for each task.

Skills are the public contract. Runtime scripts and provider CLIs support skills when a skill needs configuration, search, extraction, or validation.

## How Agents Use ArkSpace

Use ArkSpace from an AI-agent session with slash invocation.

```text
/ark-space:orchestrator search for the claude-code-everything project
/ark-space:arxiv-search search diffusion transformers
/ark-space:web-discover search Claude Code plugin docs
/ark-space:web-research research the AI coding agents market
/ark-space:web-fetch extract https://example.com
```

Choose the entry path by intent:

| Path | Use When |
|---|---|
| `/ark-space:orchestrator ...` | You want ArkSpace to choose the role, workflow, capability, and provider. |
| `/ark-space:<skill-name> ...` | You know the task capability; select a provider only when its distinctive behavior matters. |
| `agents/*` | The host supports callable agents/subagents and should use a role-specific behavior profile. |

See [docs/invocation.md](docs/invocation.md) for the full invocation contract and capability split.

Personal execution examples:

```text
/ark-space:orchestrator help me run my weekly planning board
/ark-space:orchestrator capture these personal tasks into my Obsidian Kanban
```

## Core Model

ArkSpace has four host-neutral layers:

| Layer | Purpose |
|---|---|
| `skills/` | Canonical Agent Skills. Each public skill lives at `skills/<name>/SKILL.md`. |
| `agents/` | Callable role definitions that compose skills and workflows without duplicating skill bodies. |
| `workflows/` | Routing, handoff, provider selection, and quality-gate protocols. |
| `registry/` | Source governance, role ownership, skill inventory, provider metadata, and validation contracts. |

Host-specific files are adapters:

| Path | Purpose |
|---|---|
| `.claude-plugin/` | Claude Code plugin metadata. |
| `.codex-plugin/` | Codex plugin metadata. |
| `integrations/` | Generated host-native agent outputs. |
| `plugins/ark-space/` | Packaged Codex marketplace copy generated from canonical sources. |

Claude Code, Codex, and future hosts consume the same skill files through adapters.

## Callable Agents

| Agent | Owns |
|---|---|
| `orchestrator` | Lightweight routing, provider setup routing, workflow selection. |
| `code-engineer` | Implementation, refactoring, tests, debugging. |
| `code-reviewer` | Bug, regression, risk, and test-gap review. |
| `doc-writer` | Project documentation and Obsidian-flavored Markdown when needed. |
| `web-researcher` | Web search, URL extraction, crawling, monitors, and source-grounded research. |
| `knowledge-manager` | Notes, Obsidian artifacts, Bases, Canvas, Kanban, and vault organization. |
| `prd-planner` | Requirements, scope, acceptance criteria, product decisions. |
| `competitive-analyst` | Product, competitor, market, and public-evidence analysis, with web operations handed to the web researcher when needed. |
| `project-manager` | Milestones, task breakdown, risks, status structures. |
| `personal-assistant` | Personal task capture, weekly planning, Kanban-first personal execution, and personal project upkeep. |
| `skill-manager` | Skill lifecycle, upstream provenance, registries, package integrity. |

## Included Skills

### Core And Governance

| Skill | Purpose |
|---|---|
| `orchestrator` | Route work to the smallest useful role, workflow, capability, and provider. |
| `skill-manager` | Create, adapt, validate, source-track, and govern ArkSpace skills. |
| `provider-manager` | Configure and inspect provider URLs, key references, readiness, and rotation. |

### Personal Execution

| Skill | Purpose |
|---|---|
| `drive-me` | Turn personal execution friction, scope drift, or stalled work into one bounded next-action plan. |

### Product Requirements

| Skill | Purpose |
|---|---|
| `prd-create` | Write R&D-ready PRDs from accessible products or prototypes, confirmed workflows, and review decisions. |

### Search, Fetch, And Research

| Skill | Purpose |
|---|---|
| `searxng-search` | Query a configured self-hosted SearXNG instance. |
| `arxiv-search` | Search arXiv papers by keyword, author, title, category, or ID. |
| `defuddle` | Extract clean Markdown from normal web pages through Defuddle CLI. |
| `web-discover` | Search public sources or find pages related to a known URL. |
| `web-fetch` | Extract URL content through Exa, Tavily, or Firecrawl. |
| `web-site` | Map a site or crawl a requested site section. |
| `web-research` | Produce cited research through Exa or Tavily. |
| `web-extract` | Extract schema-shaped public data through Firecrawl. |
| `web-automation` | Interact with live pages or manage recurring monitors. |
| `code-context` | Retrieve implementation-oriented examples and API usage context through Exa. |

Provider-specific implementations are internal adapters. Public skills remain capability-based; select an explicit mode and pass a provider only when a user requests it or its distinctive controls are required.

### Knowledge And Obsidian Tools

| Skill | Purpose |
|---|---|
| `json-canvas` | Create and edit JSON Canvas files. |
| `obsidian-bases` | Create and edit Obsidian Bases. |
| `obsidian-cli` | Interact with Obsidian through the CLI. |
| `obsidian-kanban` | Create and maintain Obsidian Kanban boards. |
| `obsidian-markdown` | Create and edit Obsidian-flavored Markdown. |

The Obsidian skills are retained as knowledge-management tools within the broader ArkSpace package.

## Provider Configuration

ArkSpace keeps private provider configuration outside the public repository. When a provider is missing a URL or API key, the skill should guide the user through setup with local configuration and private secrets.

Provider setup supports:

- self-hosted service URLs such as SearXNG
- API-backed providers such as Exa, Tavily, and Firecrawl
- multiple API keys with rotation
- local private secret storage or environment-variable references

See [docs/provider-configuration.md](docs/provider-configuration.md) for command setup, manual recovery, and agent-guided setup.

## Documentation

| Document | Purpose |
|---|---|
| [docs/invocation.md](docs/invocation.md) | Slash invocation, direct skills, Orchestrator routing, capability split. |
| [docs/provider-configuration.md](docs/provider-configuration.md) | Provider URLs, API keys, multi-key rotation, setup recovery. |
| [docs/roadmap.md](docs/roadmap.md) | Project roadmap, development workstreams, and release readiness checks. |
| [docs/maintenance.md](docs/maintenance.md) | Maintainer commands for validation, packaging, host cache checks, and local development. |
| [docs/architecture.md](docs/architecture.md) | Framework layers and runtime entrypoints. |
| [docs/adding-skills.md](docs/adding-skills.md) | How to add or adapt skills. |
| [docs/platform-support.md](docs/platform-support.md) | Host adapter expectations and support notes. |

## Development Contract

- Keep canonical skills in `skills/<skill-name>/SKILL.md`.
- Keep callable agent sources in `agents/`.
- Keep orchestration protocols in `workflows/`.
- Keep host-specific metadata in adapter directories only.
- Keep provider and source governance in `registry/`.
- Regenerate `integrations/` from `agents/`; generated files are derived outputs.
- Keep private configuration out of the package.

For maintainer validation and packaging commands, use [docs/maintenance.md](docs/maintenance.md).
