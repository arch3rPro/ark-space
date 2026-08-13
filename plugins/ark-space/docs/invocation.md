# Invocation

ArkSpace supports direct skill invocation and Orchestrator-routed invocation. Public skills should expose both when the skill is user-visible and routable.

Invocation is part of the agent-loop contract. A public skill is not usable just because its files exist; the host must be able to discover the skill description, load the skill, and accept the documented slash path. See [Agent Loop Model](agent-loop-model.md).

## Direct Skill Path

Use a direct skill path when the caller knows the task capability. Provider selection is optional and only needed for an explicit provider request or provider-specific control:

```text
/ark-space:web-search search claude-code-everything
/ark-space:web-search find pages related to https://example.com/article
/ark-space:web-search search diffusion transformers
/ark-space:web-fetch extract https://example.com/article
/ark-space:web-site map https://docs.example.com
/ark-space:web-site crawl https://docs.example.com/docs
/ark-space:web-research research what changed in AI coding agents in 2025
/ark-space:web-extract extract product pricing from https://example.com
/ark-space:web-automation open https://example.com and snapshot
/ark-space:web-automation monitor https://example.com/blog
/ark-space:code-context find React hooks state management examples
```

Direct invocation is declared in `registry/skills.yaml` with `directInvocation` and must include `/ark-space:<skill-name>`. Slash invocation is the public contract for user-facing examples and host smoke tests. For ambiguous web intent, apply `workflows/web-capability-routing.md` before selecting a capability.

## Orchestrator Path

Use the Orchestrator path when ArkSpace should choose the role, workflow, or capability; specify a provider only when its outcome would materially differ:

```text
/ark-space:orchestrator search current AI coding agent news
/ark-space:orchestrator search arXiv papers about diffusion transformers
/ark-space:orchestrator extract and summarize https://example.com
/ark-space:orchestrator map https://docs.example.com
/ark-space:orchestrator crawl https://docs.example.com/docs
/ark-space:orchestrator extract product pricing from https://example.com
/ark-space:orchestrator inspect https://example.com in a browser
/ark-space:orchestrator monitor https://example.com/blog
/ark-space:orchestrator find pages similar to https://example.com/article
/ark-space:orchestrator research the AI coding agents market
/ark-space:orchestrator help me run my weekly planning board
/ark-space:orchestrator capture these personal tasks into my Obsidian Kanban
```

Routable public skills declare `orchestratorInvocation` in `registry/skills.yaml`. The Orchestrator selects the role, capability, then provider policy. It must not silently replace a user-requested provider.

## Capability Routing

`workflows/web-capability-routing.md` is the authoritative web capability matrix. Apply it to separate source/page discovery, reading supplied URLs, structured fields/schema extraction, cited synthesis, known-site map/crawl work, and interaction or monitors. Capability selection precedes provider selection. Resolve providers in the capability registries, including `registry/web-map-providers.yaml`, `registry/web-crawl-providers.yaml`, `registry/deep-research-providers.yaml`, and `registry/code-context-providers.yaml`.

## Configuration

Provider configuration lives outside committed package files. For Tavily:

```bash
python3 scripts/arkspace.py provider setup tavily --wizard
python3 scripts/arkspace.py provider check tavily
```

For Exa:

```bash
python3 scripts/arkspace.py provider setup exa --wizard --key-count 2
python3 scripts/arkspace.py provider check exa
```

For Firecrawl:

```bash
python3 scripts/arkspace.py provider setup firecrawl --wizard --key-count 2
python3 scripts/arkspace.py provider check firecrawl
```

Provider checks prove the local ArkSpace provider configuration resolves. Host discovery is verified separately with installed-host smoke tests.
