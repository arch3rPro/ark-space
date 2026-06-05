# Architecture

ArkSpace is a creative workspace for orchestrating reusable agent skills, roles, and workflows.

The canonical skill source is `skills/<skill-name>/SKILL.md`. Claude Code, Codex, and future hosts should consume the same skill files instead of maintaining platform-specific copies.

## Layers

- `skills/`: executable skill instructions.
- `roles/`: role definitions that compose skills for common work types.
- `registry/`: governance metadata for skills, roles, and upstream sources.
- `registry/search-providers.yaml`: provider registry for `web_search` skills so roles can discover sources without hard-coding one provider.
- `registry/web-fetch-providers.yaml`: provider registry for `web_fetch` skills so roles can read URLs without hard-coding one extractor.
- `.claude-plugin/`: Claude Code plugin metadata.
- `.codex-plugin/`: Codex plugin metadata.
- `overlays/`: examples and documentation for private local customization.
- `reference/`: optional local or tracked area for upstream projects used as design reference.

## Default Entry

The default role is `orchestrator`. It uses lightweight routing to choose the smallest useful role and workflow for a task.

## Web Providers

Web skills are selected as providers after role routing.

`web_search` takes a query and returns candidate URLs, snippets, and source metadata. `web_fetch` takes a URL and returns readable content such as Markdown, text, or extraction metadata. A general source-discovery request routes to `docs/knowledge-manager`, while a competitor or market-evidence request routes to `product/competitive-analyst`; both roles can search with `searxng-search` and then fetch selected URLs with `defuddle`.

When more web skills are added, register each provider with its capability, required environment, privacy posture, priority, roles, and output fields. User-explicit providers win, sensitive queries require a private/self-hosted provider or confirmation, and snippet-only search output should be followed by fetch/extraction before factual claims.

## Existing Obsidian Skills

The Obsidian skills remain active. They are now classified as documentation and knowledge-management tooling rather than the identity of the whole repository.
