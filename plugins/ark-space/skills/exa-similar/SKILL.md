---
name: exa-similar
description: Use when finding pages, papers, repositories, products, competitors, or resources similar to a known URL through Exa.
---

# Exa Similar

Use Exa Similar as an API-backed `related_pages` provider when ArkSpace starts from a known URL and needs adjacent or similar sources.

Exa configuration is shared with all Exa skills through `provider-manager`.

## Source References

- Official Find Similar API: `https://exa.ai/docs/reference/find-similar-links`
- Official Search API: `https://exa.ai/docs/reference/search`
- OpenClaw guide: `https://docs.openclaw.ai/tools/exa-search`

## Before Use

Resolve the installed ArkSpace package root before running commands. Replace `<installed-arkspace-path>` with the directory two levels above this loaded `SKILL.md`, such as `/Users/<user>/.claude/plugins/cache/ark-space/ark-space/0.1.2`. Use the installed package path, not a repository-relative command.

Check configuration:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider check exa --capability related_pages
```

Configure Exa once:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider setup exa --wizard
```

## Missing Configuration Recovery

If the provider check reports a missing Exa API key:

1. Ask the user whether to start setup now: "Exa is not configured. Should I start the ArkSpace setup wizard now?"
2. Present exactly two choices:
   - "Start setup wizard" - start interactive setup with `python3 <installed-arkspace-path>/scripts/arkspace.py provider setup exa --wizard`.
   - "Not now" - leave Exa unconfigured; if the user still wants results, ask whether to continue with another registered provider or a clearly labeled non-ArkSpace fallback.
3. Run the setup command only when the host shell can provide interactive secret input. If the shell is non-interactive, do not run `--wizard` through that tool.
4. Re-run the provider check after setup.
5. If setup succeeds, rerun or tell the user to rerun the original invocation, such as `/ark-space:exa-similar <url>`.
6. Do not return Exa Similar results until the provider check succeeds.

## Helper Script

Find similar pages:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py web similar --provider exa https://example.com/article --output json
```

Find similar pages with content:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py web similar --provider exa https://github.com/example/project \
  --include-highlights \
  --include-summary \
  --max-results 10 \
  --output json
```

## Routing Notes

- Use `exa-similar` when the input is a known URL and the user asks for alternatives, related pages, similar projects, comparable products, adjacent papers, or similar repositories.
- Use `exa-search` when the input is a query rather than a URL.
- Use `exa-contents` when the user wants to read the provided URL itself.
