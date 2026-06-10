---
name: exa-contents
description: Use when extracting clean content, summaries, highlights, subpages, link extras, or metadata for known URLs or Exa result ids through Exa Contents.
---

# Exa Contents

Use Exa Contents as an API-backed `web_fetch` provider when ArkSpace needs full text, summaries, highlights, subpages, link extras, or metadata for known URLs or Exa result ids.

Exa configuration is shared with `exa-search` through `provider-manager`.

## Source References

- Official Contents API: `https://exa.ai/docs/reference/get-contents`
- Official Search API: `https://exa.ai/docs/reference/search`

## Before Use

Resolve the installed ArkSpace package root before running commands. Replace `<installed-arkspace-path>` with the directory two levels above this loaded `SKILL.md`, such as `/Users/<user>/.claude/plugins/cache/ark-space/ark-space/0.1.2`. Use the installed package path, not a repository-relative command.

Check configuration:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider check exa --capability web_fetch
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
4. In Claude Code non-interactive tool sessions, offer:
   - run `! python3 <installed-arkspace-path>/scripts/arkspace.py provider setup exa --wizard` in the Claude prompt or terminal, or
   - paste the API key in chat and let the agent save it with `python3 <installed-arkspace-path>/scripts/arkspace.py provider setup exa --save-secret EXA_API_KEY --secret-stdin`.
5. Re-run the provider check after setup.
6. If setup succeeds, rerun or tell the user to rerun the original invocation, such as `/ark-space:exa-contents <url>`.
7. Do not return Exa content results until the provider check succeeds.

## Helper Script

Single URL:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py web fetch --provider exa "https://example.com/article" --output json
```

With summaries and highlights:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py web fetch --provider exa "https://example.com/article" \
  --include-summary \
  --include-highlights \
  --output json
```

With freshness, subpages, and link extras:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py web fetch --provider exa "https://example.com/article" \
  --max-age-hours 24 \
  --subpages 5 \
  --include-links \
  --output json
```

## Routing Notes

- Prefer Exa Contents after Exa search when you need source text, highlights, summaries, or metadata.
- Prefer `exa-similar` when the user wants pages similar to the provided URL rather than the provided URL's own content.
- Prefer local `defuddle` for normal pages when local extraction is enough and no API call is needed.
- Prefer Tavily Extract when JavaScript rendering or query-focused extraction is the main need.
