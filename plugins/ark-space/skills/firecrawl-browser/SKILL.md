---
name: firecrawl-browser
description: Use when controlling a Firecrawl remote browser session through ArkSpace web_interact routing, especially for opening pages, snapshots, clicks, or simple browser actions.
---

# Firecrawl Browser

Use Firecrawl Browser as a CLI-backed `web_interact` provider when the user needs live browser interaction rather than static search, fetch, map, or crawl.

## Source References

- Official CLI: `https://github.com/firecrawl/cli`
- Firecrawl OpenClaw guide: `https://docs.firecrawl.dev/quickstarts/openclaw`
- OpenClaw tool guide: `https://docs.openclaw.ai/tools/firecrawl`

## Before Use

Resolve the installed ArkSpace package root before running commands. Replace `<installed-arkspace-path>` with the directory two levels above this loaded `SKILL.md`, such as `/Users/<user>/.claude/plugins/cache/ark-space/ark-space/0.1.2`. Use the installed package path, not a repository-relative command.

Check configuration:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider check firecrawl --capability web_interact
```

Set up Firecrawl:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider setup firecrawl --wizard
```

## Missing Configuration Recovery

If the provider check reports missing configuration, ask whether to start setup with `python3 <installed-arkspace-path>/scripts/arkspace.py provider setup firecrawl --wizard`. Do not run browser interaction until the provider check succeeds.

## Helper Script

Run a browser action:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py browser run --provider firecrawl \
  "open https://example.com and snapshot" \
  --output json
```

## Routing Notes

- Use `registry/web-interact-providers.yaml` before execution.
- Use `firecrawl-interact` when the workflow is explicitly tied to a previous Firecrawl scrape ID.
- Prefer static `web_fetch` or `structured_extract` when interaction is not required.
