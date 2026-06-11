---
name: firecrawl-monitor
description: Use when creating, listing, updating, running, or inspecting Firecrawl monitors through ArkSpace web_monitor routing.
---

# Firecrawl Monitor

Use Firecrawl Monitor as a CLI-backed `web_monitor` provider when the user wants recurring scrapes or crawls with change checks.

## Source References

- Official CLI: `https://github.com/firecrawl/cli`
- Firecrawl OpenClaw guide: `https://docs.firecrawl.dev/quickstarts/openclaw`
- OpenClaw tool guide: `https://docs.openclaw.ai/tools/firecrawl`

## Before Use

Resolve the installed ArkSpace package root before running commands. Replace `<installed-arkspace-path>` with the directory two levels above this loaded `SKILL.md`, such as `/Users/<user>/.claude/plugins/cache/ark-space/ark-space/0.1.2`. Use the installed package path, not a repository-relative command.

Check configuration:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider check firecrawl --capability web_monitor
```

Set up Firecrawl:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider setup firecrawl --wizard
```

## Helper Script

Create a monitor:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py monitor create --provider firecrawl \
  --name "Blog" \
  --schedule "every 30 minutes" \
  --page "https://example.com/blog" \
  --goal "Alert when a new blog post is published." \
  --output json
```

List monitors:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py monitor list --provider firecrawl --limit 20 --output json
```

Run a monitor immediately:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py monitor run --provider firecrawl <monitor-id> --output json
```

## Routing Notes

- Use `registry/web-monitor-providers.yaml` before execution.
- Start with explicit user confirmation before creating, updating, deleting, or triggering monitors.
- Firecrawl monitors are recurring external jobs; summarize the schedule and target before executing mutations.
