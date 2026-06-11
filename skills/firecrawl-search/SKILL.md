---
name: firecrawl-search
description: Use when querying Firecrawl through ArkSpace web_search routing, especially when search results may need full-page scraping, news/web source selection, or Firecrawl CLI-backed web discovery.
---

# Firecrawl Search

Use Firecrawl as a CLI-backed `web_search` provider when ArkSpace routes search to Firecrawl or when the user explicitly asks for Firecrawl search.

Firecrawl configuration is managed by `provider-manager`; do not ask the user to edit config files by hand.

## Source References

- Official CLI: `https://github.com/firecrawl/cli`
- Firecrawl OpenClaw guide: `https://docs.firecrawl.dev/quickstarts/openclaw`
- OpenClaw tool guide: `https://docs.openclaw.ai/tools/firecrawl`

## Before Use

Resolve the installed ArkSpace package root before running commands. Replace `<installed-arkspace-path>` with the directory two levels above this loaded `SKILL.md`, such as `/Users/<user>/.claude/plugins/cache/ark-space/ark-space/0.1.2`. Use the installed package path, not a repository-relative command.

Check configuration:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider check firecrawl --capability web_search
```

Set up Firecrawl once:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider setup firecrawl --wizard
```

For multiple API keys:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider setup firecrawl --wizard --key-count 2
```

The Firecrawl CLI must also be available as `firecrawl`, or `npx` must be available for the helper fallback.

## Missing Configuration Recovery

If the provider check reports a missing Firecrawl API key:

1. Ask the user whether to start setup now: "Firecrawl is not configured. Should I start the ArkSpace setup wizard now?"
2. Present exactly two choices:
   - "Start setup wizard" - start interactive setup with `python3 <installed-arkspace-path>/scripts/arkspace.py provider setup firecrawl --wizard`.
   - "Not now" - leave Firecrawl unconfigured; if the user still wants results, ask whether to continue with another registered provider or a clearly labeled non-ArkSpace fallback.
3. Run the setup command only when the host shell can provide interactive secret input. If the shell is non-interactive, do not run `--wizard` through that tool.
4. In Claude Code non-interactive tool sessions, offer:
   - run `! python3 <installed-arkspace-path>/scripts/arkspace.py provider setup firecrawl --wizard` in the Claude prompt or terminal, or
   - paste the API key in chat and let the agent save it with `python3 <installed-arkspace-path>/scripts/arkspace.py provider setup firecrawl --save-secret FIRECRAWL_API_KEY --secret-stdin`.
5. Re-run the provider check after setup.
6. If setup succeeds, rerun or tell the user to rerun the original invocation, such as `/ark-space:firecrawl-search <query>`.
7. Do not return Firecrawl search results until the provider check succeeds.

## Helper Script

Basic search:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py web search --provider firecrawl "agent skills" --output json
```

Search and scrape result pages:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py web search --provider firecrawl "OpenClaw documentation" \
  --include-text \
  --max-results 5 \
  --output json
```

## Routing Notes

- Use `registry/search-providers.yaml` before execution.
- Prefer Firecrawl when search results should be paired with scraped content or when Firecrawl-specific web/news/category controls matter.
- Use `firecrawl-scrape` when the user provides a URL.
- Use `firecrawl-map` or `firecrawl-crawl` for known-site URL discovery or bulk extraction.
