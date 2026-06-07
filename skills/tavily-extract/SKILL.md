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
python3 scripts/arkspace.py provider setup tavily --wizard
python3 scripts/arkspace.py provider check tavily --capability web_fetch
```

## Missing Configuration Recovery

If the provider check reports a missing Tavily API key:

1. Tell the user: "Tavily is not configured. I can start the ArkSpace setup wizard now."
2. Present one clear setup action. In Claude Code, use `! python3 <installed-arkspace-path>/scripts/arkspace.py provider setup tavily --wizard`. In other hosts, run the same command through the host's shell execution mechanism.
3. When the host supports shell execution and the user approves setup, run the setup command for them instead of asking them to edit config files.
4. Re-run the provider check after setup.
5. If setup succeeds, rerun or tell the user to rerun the original invocation, such as `/ark-space:tavily-extract <url>`.
6. Do not return Tavily extraction results until the provider check succeeds.
7. If the user declines, defers, or cannot complete setup and still wants results, ask whether to continue with a clearly labeled non-ArkSpace fallback.

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
