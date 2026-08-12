# Provider Capabilities

Web providers are selected after role routing. ArkSpace provider registries are the authority for provider choice.

## Capabilities

| Capability | Input | Output |
| --- | --- | --- |
| `web_search` | Query | Candidate URLs, snippets, and source metadata |
| `web_fetch` | URL | Readable page content, Markdown or text, and extraction metadata |
| `web_map` | Site URL | Discovered URLs and site structure |
| `web_crawl` | Site URL | Extracted content from many pages |
| `structured_extract` | Prompt, URLs, optional schema | Schema-shaped extracted data or async job status |
| `web_interact` | Browser instruction or scrape ID | Browser action output, session metadata, or live view links |
| `web_monitor` | Monitor target, schedule, goal | Monitor IDs, checks, statuses, and change results |
| `deep_research` | Research prompt | Cited synthesized report or async task status |
| `code_context` | Coding query | Repository-grounded examples, API syntax, framework usage, and token-efficient code context |
| `related_pages` | URL | Similar pages, adjacent resources, comparable projects, or related sources |

## Selection

1. Use the provider or skill named by the user when it exists in the matching registry.
2. Check the provider registry before first use.
3. Select only active registered providers that match the requested capability.
4. Run the selected provider's `checkCommand` when configuration state matters.
5. If required configuration is missing, route to `provider-manager` for guided setup and stop before producing capability results.
6. Prefer configured providers that match the task's privacy and evidence requirements.
7. Use fetch after search when factual claims need source content beyond snippets.
8. When stopped for missing configuration, the next action is provider setup. If the user declines, defers, or cannot complete setup and still wants results, ask whether to continue with a clearly labeled non-ArkSpace fallback.

## Provider Fit

| Provider | Best fit |
| --- | --- |
| Exa MCP (`exa-mcp`) | Zero-config default web search: general queries, no key or setup |
| SearXNG | Self-hosted or private metasearch where the endpoint is controlled by the user |
| Exa | Semantic search, technical docs, repositories, concept discovery, domain/date filtered search, concise cited answers, code context, similar-page discovery |
| Firecrawl | CLI-backed search, scraping, site mapping, crawling, structured extraction, browser interaction, and monitoring for JS-heavy or bot-protected pages; `web_search` and `web_fetch` are keyless |
| Tavily | Broad current web search, JavaScript-heavy extraction, site mapping, crawling, and long-form research reports |
| Jina (`jina`) | Keyless general web search when no key is configured; anonymous Reader-backed results |
| DuckDuckGo (`duckduckgo`) | Keyless, explicit-only web search; used only when the caller names it, never auto-selected |
| Brave (`brave`) | Keyed web search when a `BRAVE_API_KEY` is configured |
| Defuddle | Local URL extraction when no API provider is needed |

## Provider Selection Notes

- `exa-mcp` is the zero-config default `web_search` provider. A plain `web
  search` command resolves it with no key or setup and no hidden fallback: if
  the chosen provider is unreachable, the command fails rather than silently
  switching.
- The keyless providers `exa-mcp`, `jina`, and `duckduckgo` accept only the
  common chain arguments (`query`, `--max-results`, `--timeout`, `--output`).
  Provider-specific flags are rejected; use an explicit matching `--provider`
  for those options.
- `duckduckgo` is `explicitOnly: true`: it is never part of the default or
  priority selection and runs only when the caller names it.
- `brave` is keyed and requires `BRAVE_API_KEY`. A live Brave run uses a
  dedicated test credential; an unconfigured Brave never invalidates
  deterministic checks.

## Registry Authority

Use these registries before executing web capabilities:

| Capability | Registry |
| --- | --- |
| `web_search` | `registry/search-providers.yaml` |
| `web_fetch` | `registry/web-fetch-providers.yaml` |
| `web_map` | `registry/web-map-providers.yaml` |
| `web_crawl` | `registry/web-crawl-providers.yaml` |
| `structured_extract` | `registry/structured-extract-providers.yaml` |
| `web_interact` | `registry/web-interact-providers.yaml` |
| `web_monitor` | `registry/web-monitor-providers.yaml` |
| `deep_research` | `registry/deep-research-providers.yaml` |
| `code_context` | `registry/code-context-providers.yaml` |
| `related_pages` | `registry/related-page-providers.yaml` |

Another ArkSpace provider is a valid fallback only when it is registered, active, capability-compatible, and passes its own configuration check.

Host-native search or fetch is outside ArkSpace provider routing. Use it only after the provider setup path is declined, blocked, or explicitly bypassed by the user, and label the result as outside ArkSpace provider execution.
