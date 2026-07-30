---
name: web-extract
description: Use when extracting structured facts from public URLs with a natural-language goal and optional JSON schema.
---

# Web Extract

Extract structured data through the configured provider selected by `registry/structured-extract-providers.yaml`. Accept a prompt, URLs, schema, model, budget, wait, and output controls. Preserve asynchronous status and cancellation semantics; report the actual provider and request ID.

## Run

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py structured extract --provider firecrawl "extract product pricing" --urls https://example.com --output json
```

For setup or a failed provider check, use `provider-manager`.
