---
name: web-search
description: Use when discovering public sources from a query, searching papers via arXiv, using a privacy-oriented SearXNG instance, or finding pages semantically related to a known URL; optionally select Exa MCP, Exa, Tavily, Firecrawl, Jina, DuckDuckGo, Brave, SearXNG, or arXiv.
---

# Web Search

Discover public sources through the configured provider registry. This is the single query-search entry point; provider-specific syntax, filters, and troubleshooting live in `docs/`.

Select one explicit mode:

- `search`: accept a query and use `registry/search-providers.yaml` (Exa MCP, Exa, Tavily, Firecrawl, Jina, DuckDuckGo, Brave, SearXNG, arXiv).
- `related`: accept a seed URL and use `registry/related-page-providers.yaml` (Exa similar links).

Do not infer `related` from an arbitrary URL: use it only when the URL is the semantic seed. Do not silently substitute a user-requested provider. Report the actual provider, request ID when supplied, result URLs, and any fallback.

## Before Use

Resolve the installed ArkSpace package root before running commands. Replace `<installed-arkspace-path>` with the directory two levels above this loaded `SKILL.md`, such as `/Users/<user>/.claude/plugins/cache/ark-space/ark-space/0.1.2`. Use the installed package path, not a repository-relative command.

Check a provider before searching when privacy, reproducibility, or reliability matters:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider check exa-mcp --capability web_search
python3 <installed-arkspace-path>/scripts/arkspace.py provider check jina --capability web_search
python3 <installed-arkspace-path>/scripts/arkspace.py provider check duckduckgo --capability web_search
python3 <installed-arkspace-path>/scripts/arkspace.py provider check brave --capability web_search
python3 <installed-arkspace-path>/scripts/arkspace.py provider check tavily --capability web_search
python3 <installed-arkspace-path>/scripts/arkspace.py provider check searxng
python3 <installed-arkspace-path>/scripts/arkspace.py provider check arxiv --capability web_search
```

If a check fails or a provider is unconfigured, use `provider-manager`; never ask users to edit provider files or expose keys. arXiv needs no key or setup. SearXNG needs a self-hosted URL (`provider configure searxng --base-url <url>`, `SEARXNG_URL`, or `--base-url`). The keyless providers `exa-mcp`, `jina`, and `duckduckgo` need no configuration; `brave` is keyed and needs `BRAVE_API_KEY`.

## Run

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py web search "agent skills frameworks" --output json
python3 <installed-arkspace-path>/scripts/arkspace.py web search --provider tavily "agent skills frameworks" --output json
python3 <installed-arkspace-path>/scripts/arkspace.py web search --provider arxiv "diffusion transformers" --max-results 5 --output json
python3 <installed-arkspace-path>/scripts/arkspace.py web search --provider searxng "privacy metasearch" --max-results 5 --output json
python3 <installed-arkspace-path>/scripts/arkspace.py web search --provider duckduckgo "agent skills" --max-results 5 --output json
python3 <installed-arkspace-path>/scripts/arkspace.py web search --providers exa-mcp,jina "agent skills" --max-results 5
python3 <installed-arkspace-path>/scripts/arkspace.py web similar --provider exa https://example.com --output json
```

A plain `web search` (no `--provider`) resolves the zero-config default `exa-mcp`.

## Provider Selection

Prefer a provider by the task, then by registry priority:

- **Exa MCP** — zero-config default web search: general queries with no key or setup. See `docs/exa-mcp.md`.
- **arXiv** — academic preprint discovery, arXiv IDs, authors, categories (`cs.AI`), title/abstract search, literature candidates. No key needed. See `docs/arxiv-search.md`.
- **SearXNG** — privacy-oriented or self-hosted metasearch, or when the user names an instance. See `docs/searxng-search.md`.
- **Exa** — semantic/neural discovery, coding docs, repositories, technical research, deep modes, structured output, and URL-seeded related pages.
- **Tavily** — broad current search, finance, news, LLM-optimized snippets, research synthesis.
- **Firecrawl** — when search should optionally scrape full page content or JS-heavy sources are likely; `web_search` is keyless.
- **Jina** — keyless general web search when no key is configured. See `docs/jina.md`.
- **DuckDuckGo** — keyless, explicit-only web search; used only when the caller names it. See `docs/duckduckgo.md`.
- **Brave** — keyed web search when a `BRAVE_API_KEY` is configured. See `docs/brave.md`.

### Default, chains, and explicit-only

- The default `web search` uses `exa-mcp`: keyless, zero-config, and with no hidden fallback. If the chosen provider is unreachable, the command fails rather than silently switching.
- `exa-mcp`, `jina`, `duckduckgo`, and `brave` accept only the common chain arguments (`query`, `--max-results`, `--timeout`, `--output`). Provider-specific flags are rejected; use an explicit matching `--provider` (for example `--provider exa`) for those options.
- `duckduckgo` is `explicitOnly: true`: it is never auto-selected by priority and never part of the default choice. It runs only when the caller names it.
- In a `--providers` chain, only common chain flags are forwarded to each candidate. Report which provider actually produced each result and any fallback.

When multiple skills or providers qualify, let Orchestrator choose the role first, then pick a provider from the registry. If the user provides an exact URL to read, route to a `web-fetch` provider instead of this skill.

## Result Handling

- Cite result URLs when using search output in an answer.
- Treat results as discovery: titles, URLs, snippets, and optional metadata, not full article content.
- Prefer opening primary sources from the result list before making factual claims.
- For current, legal, medical, financial, or other high-stakes facts, verify with primary sources after discovery.
- Respect arXiv API pacing for repeated paged requests; keep at least three seconds between repeated arXiv calls.

## Troubleshooting

| Symptom | Response |
| --- | --- |
| `401` / `403` | Key invalid or quota blocked; check the provider, use `provider-manager`, or switch provider |
| `429 Too Many Requests` | Rate limited; retry later, use another configured `web_search` provider, or a better SearXNG endpoint |
| SearXNG `403` / HTML for `format=json` | JSON format disabled on the instance; try another instance |
| Empty results | Retry with broader terms, different engines/categories, or another provider |
| Timeout | Use a self-hosted or faster provider, or reduce candidate count |
| Captcha/block page | Do not bypass; switch to a configured endpoint |
