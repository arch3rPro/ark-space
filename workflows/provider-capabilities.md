# Provider Capabilities

Web providers are selected after role routing.

## Capabilities

| Capability | Input | Output |
|---|---|---|
| `web_search` | Query | Candidate URLs, snippets, and source metadata |
| `web_fetch` | URL | Readable page content, Markdown or text, and extraction metadata |

## Selection

1. Use the provider or skill named by the user when available.
2. Check the provider registry before first use.
3. If required configuration is missing, route to `provider-manager` for guided setup.
4. Prefer configured providers that match the task's privacy and evidence requirements.
5. Use fetch after search when factual claims need source content beyond snippets.
