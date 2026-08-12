# DuckDuckGo (web search)

`duckduckgo` is a keyless, explicit-only `web_search` provider backed by the
DuckDuckGo HTML endpoint. It needs no API key and no setup.

## Explicit-only semantics

DuckDuckGo is marked `explicitOnly: true` in `registry/search-providers.yaml`.
That means it is **never auto-selected** by priority and never part of the
default provider choice: it is used only when the caller names it, either with
`--provider duckduckgo` or as an entry in a `--providers` chain.

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py web search --provider duckduckgo "agent skills" --max-results 5 --output json
python3 <installed-arkspace-path>/scripts/arkspace.py web search --providers exa-mcp,duckduckgo "agent skills" --max-results 5
```

## Caveats

- HTML scraping can be rate-limited or blocked by DuckDuckGo; treat it as a
  best-effort provider.
- It is a `_COMMON_ONLY_PROVIDERS` member: only the common chain arguments are
  accepted.
- A genuine zero-result query and an HTML-selector drift are intentionally
  indistinguishable and both surface as an invalid/empty response; retry with a
  broader query or switch provider.
- `provider check duckduckgo` verifies registration and keyless status; it
  performs no network call.
