---
name: tavily-crawl
description: Use when crawling a website section through Tavily Crawl to collect content from many pages, download docs, bulk extract pages, or apply path/domain filters with extraction controls.
---

# Tavily Crawl

Use Tavily Crawl when ArkSpace needs extracted content from many pages under a known site or site section.

Tavily configuration is shared with all Tavily skills through `provider-manager`.

## Source References

- Official docs: `https://docs.tavily.com/documentation/agent-skills`
- API reference: `https://docs.tavily.com/documentation/api-reference/endpoint/crawl`
- Official skills: `https://github.com/tavily-ai/skills/tree/main/skills/tavily-crawl`

## Before Use

Check configuration:

```bash
python3 scripts/arkspace.py provider check tavily --capability web_crawl
```

Configure Tavily once:

```bash
python3 scripts/arkspace.py provider setup tavily --wizard
```

## Missing Configuration Recovery

If the provider check reports a missing Tavily API key or missing Tavily capability:

1. Ask the user whether to start setup now: "Tavily is not configured. Should I start the ArkSpace setup wizard now?"
2. Present exactly two choices:
   - "Start setup wizard" - start interactive setup with `python3 <installed-arkspace-path>/scripts/arkspace.py provider setup tavily --wizard`.
   - "Not now" - leave Tavily unconfigured; if the user still wants results, ask whether to continue with a clearly labeled non-ArkSpace fallback.
3. Run the setup command for the user only when the host shell can provide interactive secret input. If the shell is non-interactive, do not run `--wizard` through that tool.
4. In Claude Code non-interactive tool sessions, tell the user the wizard needs interactive secret input and offer:
   - run `! python3 <installed-arkspace-path>/scripts/arkspace.py provider setup tavily --wizard` in the Claude prompt or terminal, or
   - paste the API key in chat and let the agent save it with `python3 <installed-arkspace-path>/scripts/arkspace.py provider setup tavily --save-secret TAVILY_API_KEY --secret-stdin`.
5. Re-run the provider check after setup.
6. If setup succeeds, rerun or tell the user to rerun the original invocation, such as `/ark-space:tavily-crawl <url>`.
7. Do not return Tavily Crawl results until the provider check succeeds.
8. If the user declines, defers, or cannot complete setup and still wants results, ask whether to continue with a clearly labeled non-ArkSpace fallback.

## Helper Script

Basic crawl:

```bash
python3 scripts/arkspace.py site crawl --provider tavily "https://docs.example.com" --output json
```

Conservative documentation crawl:

```bash
python3 scripts/arkspace.py site crawl --provider tavily "https://docs.example.com" \
  --max-depth 1 \
  --limit 20 \
  --select-paths "/docs/.*" \
  --output json
```

Semantic crawl for agent context:

```bash
python3 scripts/arkspace.py site crawl --provider tavily "https://docs.example.com" \
  --instructions "Find authentication and API key setup docs" \
  --chunks-per-source 3 \
  --output json
```

## Routing Notes

- Use `tavily-map` before crawling when the site structure is unknown.
- Use `tavily-extract` instead when only one or a few exact URLs are needed.
- Start with small `--limit` and shallow `--max-depth`; increase only when needed.
