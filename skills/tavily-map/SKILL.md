---
name: tavily-map
description: Use when discovering URLs on a site through Tavily Map, especially when the user knows a domain but not the exact page, asks for site structure, or needs URL discovery before extraction or crawling.
---

# Tavily Map

Use Tavily Map as an API-backed site-discovery provider when ArkSpace needs URLs from a known site without extracting page content.

Tavily configuration is shared with all Tavily skills through `provider-manager`.

## Source References

- Official docs: `https://docs.tavily.com/documentation/agent-skills`
- API reference: `https://docs.tavily.com/documentation/api-reference/endpoint/map`
- Official skills: `https://github.com/tavily-ai/skills/tree/main/skills/tavily-map`

## Before Use

Resolve the installed ArkSpace package root before running commands. Replace `<installed-arkspace-path>` with the directory two levels above this loaded `SKILL.md`, such as `/Users/<user>/.claude/plugins/cache/ark-space/ark-space/0.1.2`. Use the installed package path, not a repository-relative command.

Check configuration:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider check tavily --capability web_map
```

Configure Tavily once:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider setup tavily --wizard
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
6. If setup succeeds, rerun or tell the user to rerun the original invocation, such as `/ark-space:tavily-map <url>`.
7. Do not return Tavily Map results until the provider check succeeds.
8. If the user declines, defers, or cannot complete setup and still wants results, ask whether to continue with a clearly labeled non-ArkSpace fallback.

## Helper Script

Basic map:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py site map --provider tavily "https://docs.example.com" --output json
```

Focused URL discovery:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py site map --provider tavily "https://docs.example.com" \
  --instructions "Find API authentication pages" \
  --max-depth 2 \
  --limit 100 \
  --output json
```

Path-filtered map:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py site map --provider tavily "https://example.com" \
  --select-paths "/docs/.*,/api/.*" \
  --exclude-paths "/blog/.*" \
  --output json
```

## Routing Notes

- Use `tavily-map` when URL discovery is the task.
- Use `tavily-extract` after mapping when only a few discovered URLs need content.
- Use `tavily-crawl` when the user needs content from many pages in a site section.
