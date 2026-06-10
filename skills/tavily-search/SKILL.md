---
name: tavily-search
description: Use when querying Tavily through ArkSpace web_search routing, configuring Tavily API-backed search, or using Tavily-specific search controls such as depth, topic, time range, domain filters, or answer summaries.
---

# Tavily Search

Use Tavily as an API-backed `web_search` provider when ArkSpace routes a search task to Tavily or when the user explicitly asks for Tavily search.

Tavily configuration is managed by `provider-manager`; do not ask the user to edit config files by hand.

## Source References

- Official docs: `https://docs.tavily.com/documentation/agent-skills`
- API reference: `https://docs.tavily.com/api-reference/endpoint/search`
- Official skills: `https://github.com/tavily-ai/skills`
- OpenClaw guide: `https://docs.openclaw.ai/tools/tavily`
- OpenClaw plugin: `https://github.com/openclaw/openclaw/tree/main/extensions/tavily`

## Before Use

Resolve the installed ArkSpace package root before running commands. Replace `<installed-arkspace-path>` with the directory two levels above this loaded `SKILL.md`, such as `/Users/<user>/.claude/plugins/cache/ark-space/ark-space/0.1.2`. Use the installed package path, not a repository-relative command.

Check configuration:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider check tavily --capability web_search
```

Set up Tavily once:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider setup tavily --wizard
```

For multiple API keys:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider setup tavily --wizard --key-count 2
```

The provider config stores `env:<NAME>` references. Raw keys saved through setup live in ArkSpace's local private secrets file, not in committed package files. The agent should help run these commands when the user asks to configure Tavily.

## Missing Configuration Recovery

If the provider check reports a missing Tavily API key:

1. Ask the user whether to start setup now: "Tavily is not configured. Should I start the ArkSpace setup wizard now?"
2. Present exactly two choices:
   - "Start setup wizard" - start interactive setup with `python3 <installed-arkspace-path>/scripts/arkspace.py provider setup tavily --wizard`.
   - "Not now" - leave Tavily unconfigured; if the user still wants results, ask whether to continue with a clearly labeled non-ArkSpace fallback.
3. Run the setup command for the user only when the host shell can provide interactive secret input. If the shell is non-interactive, do not run `--wizard` through that tool.
4. In Claude Code non-interactive tool sessions, tell the user the wizard needs interactive secret input and offer:
   - run `! python3 <installed-arkspace-path>/scripts/arkspace.py provider setup tavily --wizard` in the Claude prompt or terminal, or
   - paste the API key in chat and let the agent save it with `python3 <installed-arkspace-path>/scripts/arkspace.py provider setup tavily --save-secret TAVILY_API_KEY --secret-stdin`.
5. Re-run the provider check after setup.
6. If setup succeeds, rerun or tell the user to rerun the original invocation, such as `/ark-space:tavily-search <query>`.
7. Do not return Tavily search results until the provider check succeeds.
8. If the user declines, defers, or cannot complete setup and still wants results, ask whether to continue with a clearly labeled non-ArkSpace fallback.

## Helper Script

Basic search:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py web search --provider tavily "agent skills" --output json
```

Search with Tavily controls:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py web search --provider tavily "AI coding assistants" \
  --search-depth basic \
  --max-results 5 \
  --topic general \
  --time-range month \
  --include-domains github.com,docs.tavily.com \
  --output json
```

## Routing Notes

- Use `registry/search-providers.yaml` before execution.
- Use `tavily-extract` or another `web_fetch` provider when the user provides a URL to read.
- Use Tavily search results as discovery snippets unless `include_answer` or raw content is explicitly requested.
- Record provider failures through the helper so key rotation can cool down failing keys.
