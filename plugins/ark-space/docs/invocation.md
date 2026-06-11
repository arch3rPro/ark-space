# Invocation

ArkSpace supports direct skill invocation and Orchestrator-routed invocation. Public skills should expose both when the skill is user-visible and routable.

## Direct Skill Path

Use a direct skill path when the caller already knows the skill or provider to use:

```text
/ark-space:tavily-search search claude-code-everything
/ark-space:searxng-search search claude-code-everything
/ark-space:exa-search search Claude Code plugin docs
/ark-space:exa-contents extract https://example.com/article
/ark-space:exa-answer answer what changed in AI coding agents in 2025
/ark-space:exa-context find React hooks state management examples
/ark-space:exa-similar find pages similar to https://example.com/article
/ark-space:firecrawl-search search OpenClaw documentation
/ark-space:firecrawl-scrape scrape https://example.com
/ark-space:firecrawl-map map https://docs.example.com
/ark-space:firecrawl-crawl crawl https://docs.example.com/docs
/ark-space:firecrawl-agent extract product pricing from https://example.com
/ark-space:firecrawl-browser open https://example.com and snapshot
/ark-space:firecrawl-interact interact with scrape <scrape-id>
/ark-space:firecrawl-monitor create monitor for https://example.com/blog
/ark-space:tavily-extract extract https://example.com
/ark-space:tavily-map map https://docs.example.com
/ark-space:tavily-crawl crawl https://docs.example.com/docs
/ark-space:tavily-research research the AI coding agents market
```

Direct invocation is declared in `registry/skills.yaml` with `directInvocation` and must include `/ark-space:<skill-name>`. Slash invocation is the public contract for user-facing examples and host smoke tests.

## Orchestrator Path

Use the Orchestrator path when ArkSpace should choose the role, workflow, provider capability, or provider:

```text
/ark-space:orchestrator use Tavily to search claude-code-everything
/ark-space:orchestrator use Exa to search Claude Code plugin docs
/ark-space:orchestrator use Exa to find React hooks state management examples
/ark-space:orchestrator use Firecrawl to scrape https://example.com
/ark-space:orchestrator use Firecrawl Agent to extract product pricing from https://example.com
/ark-space:orchestrator use Firecrawl Browser to inspect https://example.com
/ark-space:orchestrator use Firecrawl Monitor for https://example.com/blog
/ark-space:orchestrator find pages similar to https://example.com/article
/ark-space:orchestrator search for the claude-code-everything project
/ark-space:orchestrator fetch and summarize https://example.com
/ark-space:orchestrator use Tavily to deeply research the AI coding agents market
```

Routable public skills declare `orchestratorInvocation` in `registry/skills.yaml`. The Orchestrator selects the role first, then the capability and provider registry.

## Capability Split

| Capability | Input | Output | Registry |
|---|---|---|---|
| `web_search` | Query | Candidate URLs, snippets, source metadata | `registry/search-providers.yaml` |
| `web_fetch` | URL | Extracted page content, Markdown/text, metadata | `registry/web-fetch-providers.yaml` |
| `web_map` | Site URL | Discovered URLs and site structure | `registry/web-map-providers.yaml` |
| `web_crawl` | Site URL | Extracted content from many pages | `registry/web-crawl-providers.yaml` |
| `structured_extract` | Prompt, URLs, optional schema | Schema-shaped extracted data or async job status | `registry/structured-extract-providers.yaml` |
| `web_interact` | Browser instruction or scrape ID | Browser action output, session metadata, or live view links | `registry/web-interact-providers.yaml` |
| `web_monitor` | Monitor target, schedule, goal | Monitor IDs, checks, statuses, and change results | `registry/web-monitor-providers.yaml` |
| `deep_research` | Research prompt | Cited synthesized report or async task status | `registry/deep-research-providers.yaml` |
| `code_context` | Coding query | Repository-grounded examples and API usage context | `registry/code-context-providers.yaml` |
| `related_pages` | URL | Similar pages, adjacent resources, comparable projects, related sources | `registry/related-page-providers.yaml` |

Use `web_search` to discover sources from a query. Use `related_pages` when the user provides a URL and wants similar pages or comparable resources. Use `web_fetch` to read a known URL or a URL selected from search/map/similar results. Use `web_map` when the site is known but the exact URL is not. Use `web_crawl` when the user needs many pages from a site section. Use `structured_extract` when the user needs schema-shaped data. Use `web_interact` when the page must be operated in a browser or an existing scrape session. Use `web_monitor` for recurring checks. Use `deep_research` when the requested output is a report or comparison. Use `code_context` when a coding task needs examples or API usage context beyond the local repository.

## Configuration

Provider configuration lives outside committed package files. For Tavily:

```bash
python3 scripts/arkspace.py provider setup tavily --wizard
python3 scripts/arkspace.py provider check tavily
```

For Exa:

```bash
python3 scripts/arkspace.py provider setup exa --wizard --key-count 2
python3 scripts/arkspace.py provider check exa
```

For Firecrawl:

```bash
python3 scripts/arkspace.py provider setup firecrawl --wizard --key-count 2
python3 scripts/arkspace.py provider check firecrawl
```

Provider checks prove the local ArkSpace provider configuration resolves. Host discovery is verified separately with installed-host smoke tests.
