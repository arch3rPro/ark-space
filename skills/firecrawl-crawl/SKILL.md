---
name: firecrawl-crawl
description: Use when bulk extracting a website or site section through Firecrawl CLI, especially docs sections, many pages on one site, or ArkSpace web_crawl routing that selects Firecrawl.
---

# Firecrawl Crawl

Use Firecrawl Crawl as a CLI-backed `web_crawl` provider when ArkSpace needs multi-page extraction from a known site or site section.

## Before Use

Resolve the installed ArkSpace package root before running commands. Replace `<installed-arkspace-path>` with the directory two levels above this loaded `SKILL.md`, such as `/Users/<user>/.claude/plugins/cache/ark-space/ark-space/0.1.2`. Use the installed package path, not a repository-relative command.

Check configuration:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider check firecrawl --capability web_crawl
```

Set up Firecrawl:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider setup firecrawl --wizard
```

## Missing Configuration Recovery

If the provider check reports missing configuration, ask whether to start setup with `python3 <installed-arkspace-path>/scripts/arkspace.py provider setup firecrawl --wizard`. Do not crawl with Firecrawl until the provider check succeeds.

## Helper Script

Crawl a docs section:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py site crawl --provider firecrawl "https://docs.example.com" \
  --include-paths /docs \
  --limit 50 \
  --output json
```

## Routing Notes

- Use `registry/web-crawl-providers.yaml` before execution.
- Start with shallow depth and small limits.
- Use map first when the user only needs a specific page from a large site.
