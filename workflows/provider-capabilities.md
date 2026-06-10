# Provider Capabilities

Web providers are selected after role routing. ArkSpace provider registries are the authority for provider choice.

## Capabilities

| Capability | Input | Output |
|---|---|---|
| `web_search` | Query | Candidate URLs, snippets, and source metadata |
| `web_fetch` | URL | Readable page content, Markdown or text, and extraction metadata |
| `web_map` | Site URL | Discovered URLs and site structure |
| `web_crawl` | Site URL | Extracted content from many pages |
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
|---|---|
| SearXNG | Self-hosted or private metasearch where the endpoint is controlled by the user |
| Exa | Semantic search, technical docs, repositories, concept discovery, domain/date filtered search, concise cited answers, code context, similar-page discovery |
| Tavily | Broad current web search, JavaScript-heavy extraction, site mapping, crawling, and long-form research reports |
| Defuddle | Local URL extraction when no API provider is needed |

## Registry Authority

Use these registries before executing web capabilities:

| Capability | Registry |
|---|---|
| `web_search` | `registry/search-providers.yaml` |
| `web_fetch` | `registry/web-fetch-providers.yaml` |
| `web_map` | `registry/web-map-providers.yaml` |
| `web_crawl` | `registry/web-crawl-providers.yaml` |
| `deep_research` | `registry/deep-research-providers.yaml` |
| `code_context` | `registry/code-context-providers.yaml` |
| `related_pages` | `registry/related-page-providers.yaml` |

Another ArkSpace provider is a valid fallback only when it is registered, active, capability-compatible, and passes its own configuration check.

Host-native search or fetch is outside ArkSpace provider routing. Use it only after the provider setup path is declined, blocked, or explicitly bypassed by the user, and label the result as outside ArkSpace provider execution.
