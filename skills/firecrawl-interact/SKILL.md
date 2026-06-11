---
name: firecrawl-interact
description: Use when interacting with a Firecrawl scraped page session by scrape ID, including prompt-driven actions, Playwright code, or stopping an interact session.
---

# Firecrawl Interact

Use Firecrawl Interact as a scrape-bound `web_interact` helper when the user has already scraped a page with Firecrawl and wants to ask questions, click, inspect, or run code against that live page context.

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

## Helper Script

Prompt against a scraped page:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py interact run --provider firecrawl \
  --scrape-id <scrape-id> \
  --prompt "click the pricing tab and summarize the visible plans" \
  --output json
```

Run code against a scraped page:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py interact run --provider firecrawl \
  --scrape-id <scrape-id> \
  --code "await page.title()" \
  --language node \
  --output json
```

Stop an interact session:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py interact stop --provider firecrawl --scrape-id <scrape-id>
```

## Routing Notes

- Use `firecrawl-browser` for a new browser session or simple remote browser commands.
- Use this skill only when the interaction is tied to a Firecrawl scrape ID or the previous Firecrawl scrape session.
