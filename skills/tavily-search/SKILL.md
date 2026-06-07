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

Check configuration:

```bash
python3 scripts/arkspace.py provider check tavily --capability web_search
```

Set up Tavily once:

```bash
python3 scripts/arkspace.py provider setup tavily --wizard
```

For multiple API keys:

```bash
python3 scripts/arkspace.py provider setup tavily --wizard --key-count 2
```

The provider config stores `env:<NAME>` references. Raw keys saved through setup live in ArkSpace's local private secrets file, not in committed package files. The agent should help run these commands when the user asks to configure Tavily.

## Missing Configuration Recovery

If the provider check reports a missing Tavily API key:

1. Tell the user: "Tavily is not configured. I can start the ArkSpace setup wizard now."
2. Present one clear setup action. In Claude Code, use `! python3 <installed-arkspace-path>/scripts/arkspace.py provider setup tavily --wizard`. In other hosts, run the same command through the host's shell execution mechanism.
3. When the host supports shell execution and the user approves setup, run the setup command for them instead of asking them to edit config files.
4. Re-run the provider check after setup.
5. If setup succeeds, rerun or tell the user to rerun the original invocation, such as `/ark-space:tavily-search <query>`.
6. Do not return Tavily search results until the provider check succeeds.
7. If the user declines, defers, or cannot complete setup and still wants results, ask whether to continue with a clearly labeled non-ArkSpace fallback.

## Helper Script

Basic search:

```bash
python3 scripts/arkspace.py web search --provider tavily "agent skills" --output json
```

Search with Tavily controls:

```bash
python3 scripts/arkspace.py web search --provider tavily "AI coding assistants" \
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
