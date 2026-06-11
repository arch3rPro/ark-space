# ArkSpace

[中文](README.zh-CN.md) | English

ArkSpace is an Agent Skills workspace for Claude Code, Codex, and compatible AI-agent hosts. It packages reusable skills, callable agent roles, workflow protocols, provider routing metadata, and host adapters so an AI agent can select focused, reusable context for each task.

Skills are the public contract. Runtime scripts and provider CLIs support skills when a skill needs configuration, search, extraction, or validation.

## How Agents Use ArkSpace

Use ArkSpace from an AI-agent session with slash invocation.

```text
/ark-space:orchestrator search for the claude-code-everything project
/ark-space:arxiv-search search diffusion transformers
/ark-space:exa-search search Claude Code plugin docs
/ark-space:tavily-research research the AI coding agents market
/ark-space:firecrawl-scrape scrape https://example.com
```

Choose the entry path by intent:

| Path | Use When |
|---|---|
| `/ark-space:orchestrator ...` | You want ArkSpace to choose the role, workflow, capability, and provider. |
| `/ark-space:<skill-name> ...` | You already know the exact skill or provider to use. |
| `agents/*` | The host supports callable agents/subagents and should use a role-specific behavior profile. |

See [docs/invocation.md](docs/invocation.md) for the full invocation contract and capability split.

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
| `arkspace-orchestrator` | Lightweight routing, provider setup routing, workflow selection. |
| `arkspace-code-engineer` | Implementation, refactoring, tests, debugging. |
| `arkspace-code-reviewer` | Bug, regression, risk, and test-gap review. |
| `arkspace-doc-writer` | Project documentation and Obsidian-flavored Markdown when needed. |
| `arkspace-knowledge-manager` | Notes, Obsidian artifacts, source discovery, fetch, crawl, extraction. |
| `arkspace-prd-planner` | Requirements, scope, acceptance criteria, product decisions. |
| `arkspace-competitive-analyst` | Product, competitor, market, and public-evidence analysis. |
| `arkspace-project-manager` | Milestones, task breakdown, risks, status structures. |
| `arkspace-skill-manager` | Skill lifecycle, upstream provenance, registries, package integrity. |

## Included Skills

### Core And Governance

| Skill | Purpose |
|---|---|
| `orchestrator` | Route work to the smallest useful role, workflow, capability, and provider. |
| `skill-manager` | Create, adapt, validate, source-track, and govern ArkSpace skills. |
| `provider-manager` | Configure and inspect provider URLs, key references, readiness, and rotation. |

### Search, Fetch, And Research Providers

| Skill | Purpose |
|---|---|
| `searxng-search` | Query a configured self-hosted SearXNG instance. |
| `arxiv-search` | Search arXiv papers by keyword, author, title, category, or ID. |
| `defuddle` | Extract clean Markdown from normal web pages through Defuddle CLI. |
| `exa-search` | Semantic web, docs, repository, and domain-filtered discovery. |
| `exa-contents` | Fetch URL content, summaries, highlights, and metadata through Exa. |
| `exa-answer` | Answer focused research questions with concise cited synthesis. |
| `exa-context` | Retrieve implementation-oriented code context and API usage examples. |
| `exa-similar` | Find similar pages, projects, papers, products, or competitors from a known URL. |
| `tavily-search` | Broad current web search through Tavily. |
| `tavily-extract` | Extract readable content from URLs through Tavily. |
| `tavily-map` | Discover URLs and site structure through Tavily. |
| `tavily-crawl` | Crawl a website section and extract many pages through Tavily. |
| `tavily-research` | Run long-form cited research synthesis through Tavily. |

### Firecrawl Web Automation

| Skill | Purpose |
|---|---|
| `firecrawl-search` | Search through Firecrawl CLI with optional result scraping. |
| `firecrawl-scrape` | Scrape rendered or hard-to-read pages through Firecrawl CLI. |
| `firecrawl-map` | Discover site URLs through Firecrawl CLI. |
| `firecrawl-crawl` | Crawl site sections through Firecrawl CLI. |
| `firecrawl-agent` | Run schema-guided Firecrawl Agent extraction. |
| `firecrawl-browser` | Control Firecrawl remote browser sessions. |
| `firecrawl-interact` | Interact with a Firecrawl scraped page session. |
| `firecrawl-monitor` | Manage recurring Firecrawl monitors. |

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
| [docs/maintenance.md](docs/maintenance.md) | Maintainer commands for validation, packaging, host cache checks, and local development. |
| [docs/architecture.md](docs/architecture.md) | Framework layers and runtime entrypoints. |
| [docs/adding-skills.md](docs/adding-skills.md) | How to add or adapt skills. |
| [docs/platform-support.md](docs/platform-support.md) | Host adapter expectations and support notes. |
| [docs/improvement-backlog.md](docs/improvement-backlog.md) | Framework improvement backlog. |

## Development Contract

- Keep canonical skills in `skills/<skill-name>/SKILL.md`.
- Keep callable agent sources in `agents/`.
- Keep orchestration protocols in `workflows/`.
- Keep host-specific metadata in adapter directories only.
- Keep provider and source governance in `registry/`.
- Regenerate `integrations/` from `agents/`; generated files are derived outputs.
- Keep private configuration out of the package.

For maintainer validation and packaging commands, use [docs/maintenance.md](docs/maintenance.md).
