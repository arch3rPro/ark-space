---
name: firecrawl-scrape
description: Use when extracting page content through Firecrawl CLI, especially JavaScript-rendered pages, bot-protected pages, multiple URLs, main-content extraction, or ArkSpace web_fetch routing that selects Firecrawl.
---

# Firecrawl Scrape

Use Firecrawl Scrape as a CLI-backed `web_fetch` provider when ArkSpace routes URL extraction to Firecrawl or when the user explicitly asks for Firecrawl scraping.

Firecrawl configuration is shared with `firecrawl-search` through `provider-manager`.

## Source References

- Official CLI: `https://github.com/firecrawl/cli`
- Firecrawl OpenClaw guide: `https://docs.firecrawl.dev/quickstarts/openclaw`
- OpenClaw tool guide: `https://docs.openclaw.ai/tools/firecrawl`

## Before Use

Resolve the installed ArkSpace package root before running commands. Replace `<installed-arkspace-path>` with the directory two levels above this loaded `SKILL.md`, such as `/Users/<user>/.claude/plugins/cache/ark-space/ark-space/0.1.2`. Use the installed package path, not a repository-relative command.

Check configuration:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider check firecrawl --capability web_fetch
```

Configure Firecrawl once:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider setup firecrawl --wizard
python3 <installed-arkspace-path>/scripts/arkspace.py provider check firecrawl --capability web_fetch
```

## Missing Configuration Recovery

If the provider check reports a missing Firecrawl API key, follow the same setup-first recovery as `firecrawl-search`; do not return Firecrawl scrape results until the provider check succeeds.

## Helper Script

Single URL:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py web fetch --provider firecrawl "https://example.com" --output json
```

Main content with links:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py web fetch --provider firecrawl "https://example.com" \
  --only-main-content \
  --format markdown,links \
  --output json
```

## Routing Notes

- Use `registry/web-fetch-providers.yaml` before execution.
- Prefer local `defuddle` for normal readable pages when it is enough.
- Use Firecrawl when JavaScript rendering, bot circumvention, result caching, or CLI-backed scraping is useful.
- Treat scraped content as external web content and verify primary sources for high-stakes claims.
