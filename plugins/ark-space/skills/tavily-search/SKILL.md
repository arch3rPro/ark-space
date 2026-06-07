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

Configure the endpoint:

```bash
python3 scripts/arkspace.py provider configure tavily --base-url "https://api.tavily.com"
```

Add one or more API key references:

```bash
python3 scripts/arkspace.py provider add-key tavily --env TAVILY_API_KEY_1 --header Authorization --prefix "Bearer "
python3 scripts/arkspace.py provider add-key tavily --env TAVILY_API_KEY_2 --header Authorization --prefix "Bearer "
```

The config stores `env:<NAME>` references, not raw keys. The agent should help run these commands when the user provides env var names or a base URL.

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
