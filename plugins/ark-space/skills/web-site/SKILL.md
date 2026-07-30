---
name: web-site
description: Use when discovering a known public site's URL structure or collecting content from many pages in one site section; optionally select Tavily or Firecrawl.
---

# Web Site

Operate on a known site through the configured provider registries. Select one explicit mode:

- `map`: discover URLs and structure through `registry/web-map-providers.yaml`.
- `crawl`: collect many pages through `registry/web-crawl-providers.yaml`.

Default to `map` when the exact page is unknown. Use `crawl` only when multi-page content is requested. Preserve crawl limits, include/exclude paths, depth, and actual provider in output. Do not silently substitute a user-requested provider.

## Run

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py site map --provider firecrawl https://docs.example.com --output json
python3 <installed-arkspace-path>/scripts/arkspace.py site crawl --provider firecrawl https://docs.example.com/docs --output json
```

For setup or a failed provider check, use `provider-manager`.
