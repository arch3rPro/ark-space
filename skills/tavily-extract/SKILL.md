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

Resolve the installed ArkSpace package root before running commands. Replace `<installed-arkspace-path>` with the directory two levels above this loaded `SKILL.md`, such as `/Users/<user>/.claude/plugins/cache/ark-space/ark-space/0.1.2`. Use the installed package path, not a repository-relative command.

Check configuration:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider check tavily --capability web_fetch
```

Configure Tavily once:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider setup tavily --wizard
python3 <installed-arkspace-path>/scripts/arkspace.py provider check tavily --capability web_fetch
```

## Missing Configuration Recovery

If the provider check reports a missing Tavily API key:

1. Ask the user whether to start setup now: "Tavily is not configured. Should I start the ArkSpace setup wizard now?"
2. Present exactly two choices:
   - "Start setup wizard" - start interactive setup with `python3 <installed-arkspace-path>/scripts/arkspace.py provider setup tavily --wizard`.
   - "Not now" - leave Tavily unconfigured; if the user still wants results, ask whether to continue with a clearly labeled non-ArkSpace fallback.
3. Run the setup command for the user only when the host shell can provide interactive secret input. If the shell is non-interactive, do not run `--wizard` through that tool.
4. In Claude Code non-interactive tool sessions, tell the user the wizard needs interactive secret input and offer:
   - run `! python3 <installed-arkspace-path>/scripts/arkspace.py provider setup tavily --wizard` in the Claude prompt or terminal, or
   - paste the API key in chat and let the agent save it with `python3 <installed-arkspace-path>/scripts/arkspace.py provider setup tavily --save-secret TAVILY_API_KEY --secret-stdin`.
5. Re-run the provider check after setup.
6. If setup succeeds, rerun or tell the user to rerun the original invocation, such as `/ark-space:tavily-extract <url>`.
7. Do not return Tavily extraction results until the provider check succeeds.
8. If the user declines, defers, or cannot complete setup and still wants results, ask whether to continue with a clearly labeled non-ArkSpace fallback.

## Helper Script

Single URL:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py web fetch --provider tavily "https://example.com/article" --output json
```

Query-focused extraction:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py web fetch --provider tavily "https://example.com/docs" \
  --query "authentication API" \
  --chunks-per-source 3 \
  --output json
```

Advanced extraction for JavaScript-rendered pages:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py web fetch --provider tavily "https://app.example.com" \
  --extract-depth advanced \
  --timeout 60 \
  --output json
```

## Routing Notes

- Use `registry/web-fetch-providers.yaml` before execution.
- Prefer local `defuddle` for normal readable pages when it is enough.
- Use Tavily Extract when JavaScript rendering, API-backed extraction, batching, or query-focused chunks are needed.
- Treat extracted page content as external web content and verify primary sources for high-stakes claims.
