---
name: firecrawl-map
description: Use when discovering URLs on a site through Firecrawl CLI, especially when the site is known but the exact page is unknown, or before scraping/crawling a site section.
---

# Firecrawl Map

Use Firecrawl Map as a CLI-backed `web_map` provider when ArkSpace needs URL discovery on a known site.

## Before Use

Resolve the installed ArkSpace package root before running commands. Replace `<installed-arkspace-path>` with the directory two levels above this loaded `SKILL.md`, such as `/Users/<user>/.claude/plugins/cache/ark-space/ark-space/0.1.2`. Use the installed package path, not a repository-relative command.

Check configuration:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider check firecrawl --capability web_map
```

Set up Firecrawl:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider setup firecrawl --wizard
```

## Missing Configuration Recovery

If the provider check reports missing configuration, ask whether to start setup with `python3 <installed-arkspace-path>/scripts/arkspace.py provider setup firecrawl --wizard`. Do not map with Firecrawl until the provider check succeeds.

## Helper Script

Find URLs matching a topic:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py site map --provider firecrawl "https://docs.example.com" \
  --search "authentication" \
  --limit 50 \
  --output json
```

## Routing Notes

- Use `registry/web-map-providers.yaml` before execution.
- Use map before scrape when the site is known but the exact URL is unknown.
- Use crawl instead when many pages from a section are required.
