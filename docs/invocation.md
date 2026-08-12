# Invocation

ArkSpace supports direct skill invocation and Orchestrator-routed invocation. Public skills should expose both when the skill is user-visible and routable.

Invocation is part of the agent-loop contract. A public skill is not usable just because its files exist; the host must be able to discover the skill description, load the skill, and accept the documented slash path. See [Agent Loop Model](agent-loop-model.md).

## Direct Skill Path

Use a direct skill path when the caller knows the task capability. Provider selection is optional and only needed for an explicit provider request or provider-specific control:

```text
/ark-space:web-search search claude-code-everything
/ark-space:web-search find pages related to https://example.com/article
/ark-space:web-search search diffusion transformers
/ark-space:web-fetch extract https://example.com/article
/ark-space:web-site map https://docs.example.com
/ark-space:web-site crawl https://docs.example.com/docs
/ark-space:web-research research what changed in AI coding agents in 2025
/ark-space:web-extract extract product pricing from https://example.com
/ark-space:web-automation open https://example.com and snapshot
/ark-space:web-automation monitor https://example.com/blog
/ark-space:code-context find React hooks state management examples
```

Direct invocation is declared in `registry/skills.yaml` with `directInvocation` and must include `/ark-space:<skill-name>`. Slash invocation is the public contract for user-facing examples and host smoke tests.

## Orchestrator Path

Use the Orchestrator path when ArkSpace should choose the role, workflow, or capability; specify a provider only when its outcome would materially differ:

```text
/ark-space:orchestrator search current AI coding agent news
/ark-space:orchestrator search arXiv papers about diffusion transformers
/ark-space:orchestrator extract and summarize https://example.com
/ark-space:orchestrator map https://docs.example.com
/ark-space:orchestrator crawl https://docs.example.com/docs
/ark-space:orchestrator extract product pricing from https://example.com
/ark-space:orchestrator inspect https://example.com in a browser
/ark-space:orchestrator monitor https://example.com/blog
/ark-space:orchestrator find pages similar to https://example.com/article
/ark-space:orchestrator research the AI coding agents market
/ark-space:orchestrator help me run my weekly planning board
/ark-space:orchestrator capture these personal tasks into my Obsidian Kanban
```

Routable public skills declare `orchestratorInvocation` in `registry/skills.yaml`. The Orchestrator selects the role, capability, then provider policy. It must not silently replace a user-requested provider.

## Capability Split

| Capability | Input | Output | Registry |
| --- | --- | --- | --- |
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
