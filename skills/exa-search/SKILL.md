---
name: exa-search
description: Use when querying Exa through ArkSpace web_search routing, especially semantic/neural search, coding documentation, repositories, technical research, domain/date filtered discovery, or Exa-specific search controls.
---

# Exa Search

Use Exa as an API-backed `web_search` provider when ArkSpace routes a semantic or technical discovery task to Exa, or when the user explicitly asks for Exa search.

Exa configuration is managed by `provider-manager`; do not ask the user to edit config files by hand.

## Source References

- Official Search API: `https://exa.ai/docs/reference/search`
- Official Contents API: `https://exa.ai/docs/reference/get-contents`
- Official Find Similar API: `https://exa.ai/docs/reference/find-similar-links`
- Official Answer API: `https://exa.ai/docs/reference/answer`
- OpenClaw guide: `https://docs.openclaw.ai/tools/exa-search`

## Before Use

Resolve the installed ArkSpace package root before running commands. Replace `<installed-arkspace-path>` with the directory two levels above this loaded `SKILL.md`, such as `/Users/<user>/.claude/plugins/cache/ark-space/ark-space/0.1.2`. Use the installed package path, not a repository-relative command.

Check configuration:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider check exa --capability web_search
```

Set up Exa once:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider setup exa --wizard
```

For multiple API keys:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider setup exa --wizard --key-count 2
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
6. If setup succeeds, rerun or tell the user to rerun the original invocation, such as `/ark-space:exa-search <query>`.
7. Do not return Exa search results until the provider check succeeds.

## Helper Script

Basic semantic search:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py web search --provider exa "agent skills frameworks" --output json
```

Search with domain filters and content extraction:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py web search --provider exa "Claude Code plugin docs" \
  --include-domains docs.anthropic.com,github.com \
  --search-type neural \
  --include-highlights \
  --max-results 5 \
  --output json
```

Deep search with structured output:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py web search --provider exa "top open-source agent skill systems" \
  --search-type deep-reasoning \
  --output-schema '{"type":"object","properties":{"projects":{"type":"array"}}}' \
  --output json
```

Deep search with related query expansion:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py web search --provider exa "open-source agent skill systems" \
  --search-type deep-reasoning \
  --additional-queries "Claude Code skills,Codex plugins,agent workflow repositories" \
  --include-summary \
  --output json
```

## Routing Notes

- Prefer Exa for semantic search, code/documentation discovery, repository research, conceptually related pages, strict domain/date filtered discovery, and search results with summaries/highlights/text.
- Use `exa-similar` instead when the user starts from a known URL and wants similar pages, comparable products, adjacent papers, or related repositories.
- Use `exa-context` instead when a code role needs ready-to-use examples, API syntax, or framework usage context rather than source URLs.
- Prefer SearXNG when privacy or self-hosted search is required.
- Prefer Tavily when the task needs broad current web search plus Tavily map/crawl/research workflows.
- Use `exa-contents` after Exa search when selected URLs need full text.
