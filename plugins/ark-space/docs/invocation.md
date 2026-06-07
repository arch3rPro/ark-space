# Invocation

ArkSpace supports direct skill invocation and Orchestrator-routed invocation. Public skills should expose both when the skill is user-visible and routable.

## Direct Skill Path

Use a direct skill path when the caller already knows the skill or provider to use:

```text
$ark-space:tavily-search 搜索 claude-code-everything
$ark-space:searxng-search 搜索 claude-code-everything
$ark-space:tavily-extract 提取 https://example.com
```

Direct invocation is declared in `registry/skills.yaml` with `directInvocation` and must include `$ark-space:<skill-name>`.

## Orchestrator Path

Use the Orchestrator path when ArkSpace should choose the role, workflow, provider capability, or provider:

```text
$ark-space:orchestrator 使用 tavily 搜索 claude-code-everything
$ark-space:orchestrator 搜索 claude-code-everything 项目
$ark-space:orchestrator 抓取并总结 https://example.com
```

Routable public skills declare `orchestratorInvocation` in `registry/skills.yaml`. The Orchestrator selects the role first, then the capability and provider registry.

## Capability Split

| Capability | Input | Output | Registry |
|---|---|---|---|
| `web_search` | Query | Candidate URLs, snippets, source metadata | `registry/search-providers.yaml` |
| `web_fetch` | URL | Extracted page content, Markdown/text, metadata | `registry/web-fetch-providers.yaml` |

Use `web_search` to discover sources. Use `web_fetch` to read a known URL or a URL selected from search results.

## Configuration

Provider configuration lives outside committed package files. For Tavily:

```bash
python3 scripts/arkspace.py provider setup tavily --env TAVILY_API_KEY_1
python3 scripts/arkspace.py provider check tavily
```

Provider checks prove the local ArkSpace provider configuration resolves. They do not prove a host session discovered the installed plugin.
