---
name: firecrawl-agent
description: Use when running Firecrawl Agent for structured extraction, schema-guided web data collection, or ArkSpace structured_extract routing that selects Firecrawl.
---

# Firecrawl Agent

Use Firecrawl Agent as a CLI-backed `structured_extract` provider when the user needs schema-shaped data from one or more web pages, especially when the task is more than a simple scrape.

## Source References

- Official CLI: `https://github.com/firecrawl/cli`
- Firecrawl OpenClaw guide: `https://docs.firecrawl.dev/quickstarts/openclaw`
- OpenClaw tool guide: `https://docs.openclaw.ai/tools/firecrawl`

## Before Use

Resolve the installed ArkSpace package root before running commands. Replace `<installed-arkspace-path>` with the directory two levels above this loaded `SKILL.md`, such as `/Users/<user>/.claude/plugins/cache/ark-space/ark-space/0.1.2`. Use the installed package path, not a repository-relative command.

Check configuration:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider check firecrawl --capability structured_extract
```

Set up Firecrawl:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider setup firecrawl --wizard
```

## Missing Configuration Recovery

If the provider check reports missing configuration, ask whether to start setup with `python3 <installed-arkspace-path>/scripts/arkspace.py provider setup firecrawl --wizard`. Do not run Firecrawl Agent until the provider check succeeds.

## Helper Script

Run a schema-guided extraction:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py structured extract --provider firecrawl \
  "extract product names and prices" \
  --urls "https://example.com/pricing" \
  --schema '{"type":"object"}' \
  --wait \
  --output json
```

Check a job:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py structured extract --provider firecrawl <job-id> --status --output json
```

## Routing Notes

- Use `registry/structured-extract-providers.yaml` before execution.
- Prefer `firecrawl-scrape` for reading a known URL without schema extraction.
- Prefer `firecrawl-crawl` for bulk extraction across many pages before synthesizing manually.
