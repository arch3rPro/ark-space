---
name: web-research
description: Synthesize a cited answer across multiple public sources; optionally select Exa or Tavily.
---

# Web Research

Synthesize cited research across multiple public sources through the configured provider selected by `registry/deep-research-providers.yaml`. For ambiguous web intent, apply `workflows/web-capability-routing.md`. Accept a research prompt plus portable source, domain, timeout, and output controls. Report the actual provider, citations, request ID when supplied, and any fallback.

- Prefer Tavily for broad or long-form research synthesis.
- Prefer Exa for concise, focused cited answers.
- Do not silently substitute a user-requested provider.

## Run

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py research run --provider tavily "AI coding agents market" --output json
```

For setup or a failed provider check, use `provider-manager`.
