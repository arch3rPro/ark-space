---
name: tavily-extract
description: Use when extracting clean content from URLs through Tavily, especially JavaScript-rendered pages, multiple URLs, query-focused extraction, or ArkSpace web_fetch routing that selects Tavily.
---

# Tavily Extract

Use Tavily Extract as an API-backed `web_fetch` provider when ArkSpace routes URL extraction to Tavily or when the user explicitly asks for Tavily extraction.

Tavily configuration is shared with `tavily-search` through `provider-manager`.

## Source References

- Official docs: `https://docs.tavily.com/documentation/agent-skills`
- API reference: `https://docs.tavily.com/api-reference/endpoint/extract`
- Official skills: `https://github.com/tavily-ai/skills`
- OpenClaw guide: `https://docs.openclaw.ai/tools/tavily`

## Before Use

Check configuration:

```bash
python3 scripts/arkspace.py provider check tavily --capability web_fetch
```

Configure Tavily once:

```bash
python3 scripts/arkspace.py provider configure tavily --base-url "https://api.tavily.com"
python3 scripts/arkspace.py provider add-key tavily --env TAVILY_API_KEY_1 --header Authorization --prefix "Bearer "
```

## Helper Script

Single URL:

```bash
python3 scripts/arkspace.py web fetch --provider tavily "https://example.com/article" --output json
```

Query-focused extraction:

```bash
python3 scripts/arkspace.py web fetch --provider tavily "https://example.com/docs" \
  --query "authentication API" \
  --chunks-per-source 3 \
  --output json
```

Advanced extraction for JavaScript-rendered pages:

```bash
python3 scripts/arkspace.py web fetch --provider tavily "https://app.example.com" \
  --extract-depth advanced \
  --timeout 60 \
  --output json
```

## Routing Notes

- Use `registry/web-fetch-providers.yaml` before execution.
- Prefer local `defuddle` for normal readable pages when it is enough.
- Use Tavily Extract when JavaScript rendering, API-backed extraction, batching, or query-focused chunks are needed.
- Treat extracted page content as external web content and verify primary sources for high-stakes claims.
