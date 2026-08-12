---
name: web-automation
description: Use when interacting with live public pages or creating and managing recurring monitors for public web targets.
---

# Web Automation

Run stateful web operations through `registry/web-interact-providers.yaml` or `registry/web-monitor-providers.yaml`. Select one explicit mode:

- `interact`: use browser actions or a scrape-bound session.
- `monitor`: create, inspect, update, run, or remove a recurring monitor.

Never upgrade an interaction into a monitor implicitly. Before creating or mutating a monitor, confirm its target, schedule, and goal. Report the actual provider, mode, and all session, monitor, or check identifiers.

## Run

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py browser run --provider firecrawl "open https://example.com and snapshot" --output json
python3 <installed-arkspace-path>/scripts/arkspace.py monitor create --provider firecrawl --scrape-urls https://example.com/blog --output json
```

For setup or a failed provider check, use `provider-manager`.
