---
name: web-fetch
description: Read supplied public URL(s) into readable content, metadata, or links; optionally select Exa, Tavily, or Firecrawl.
---

# Web Fetch

Read supplied URL(s) through the configured provider selected by `registry/web-fetch-providers.yaml`. For ambiguous web intent, apply `workflows/web-capability-routing.md`. Accept portable controls for URLs, output format, main-content extraction, wait time, and content limits. Report the actual provider and any fallback.

- Prefer Firecrawl for rendered or difficult pages.
- Prefer Exa for Exa result IDs, highlights, summaries, or related content.
- Prefer Tavily for simple URL extraction.
- Do not silently substitute a user-requested provider.

## Run

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py web fetch --provider firecrawl https://example.com --output json
```

For setup or a failed provider check, use `provider-manager`; never ask users to edit provider files or expose keys.
