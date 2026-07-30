---
name: web-discover
description: Use when discovering public sources from a query or finding pages semantically related to a known URL; optionally select Exa, Tavily, or Firecrawl.
---

# Web Discover

Discover public sources through the configured provider registry. Select one explicit mode:

- `search`: accept a query and use `registry/search-providers.yaml`.
- `related`: accept a seed URL and use `registry/related-page-providers.yaml`.

Do not infer `related` from an arbitrary URL: use it only when the URL is the semantic seed. Do not silently substitute a user-requested provider. Report the actual provider, request ID when supplied, result URLs, and any fallback.

## Run

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py web search --provider tavily "agent skills frameworks" --output json
python3 <installed-arkspace-path>/scripts/arkspace.py web similar --provider exa https://example.com --output json
```

For setup or a failed provider check, use `provider-manager`; never ask users to edit provider files or expose keys.
