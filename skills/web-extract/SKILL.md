---
name: web-extract
description: Extract requested structured fields or schema from supplied public URL(s) with a natural-language goal.
---

# Web Extract

Extract requested structured fields or schema from supplied URL(s) through the configured provider selected by `registry/structured-extract-providers.yaml`. For ambiguous web intent, apply `workflows/web-capability-routing.md`. Accept a prompt, URLs, schema, model, budget, wait, and output controls. Preserve asynchronous status and cancellation semantics; report the actual provider and request ID.

## Run

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py structured extract --provider firecrawl "extract product pricing" --urls https://example.com --output json
```

For setup or a failed provider check, use `provider-manager`.
