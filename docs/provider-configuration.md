# Provider Configuration

ArkSpace keeps personal provider configuration outside the public package. The normal setup path is command-driven or agent-guided, but the files are plain JSON when manual recovery or inspection is needed.

## Storage

Default paths:

| Purpose | Path |
|---|---|
| Provider config | `~/.config/ark-space/providers.json` |
| Private API key values | `~/.config/ark-space/secrets.json` |
| Runtime cooldown state | `~/.local/state/ark-space/provider-state.json` |

Override paths with environment variables:

```bash
export ARKSPACE_PROVIDER_CONFIG="/path/to/providers.json"
export ARKSPACE_PROVIDER_SECRETS="/path/to/secrets.json"
export ARKSPACE_PROVIDER_STATE="/path/to/provider-state.json"
```

Or use CLI flags where supported:

```bash
python3 scripts/arkspace.py provider show --config-path /path/to/providers.json
python3 scripts/arkspace.py provider resolve exa --state-path /path/to/provider-state.json
```

Provider config stores key references such as `env:EXA_API_KEY_1`. The raw key value is resolved from the process environment first, then from ArkSpace's private `secrets.json`.

## Option 1: Manual Files

Use manual editing for recovery, migration, or controlled automation. For normal user setup, prefer the command or agent-guided flows below.

Create private config files:

```bash
mkdir -p ~/.config/ark-space ~/.local/state/ark-space
umask 077
$EDITOR ~/.config/ark-space/providers.json
$EDITOR ~/.config/ark-space/secrets.json
```

Example `providers.json` with SearXNG, Exa, Firecrawl, and Tavily:

```json
{
  "providers": {
    "searxng": {
      "auth": {
        "type": "none"
      },
      "capability": "web_search",
      "enabled": true,
      "endpoints": [
        {
          "base_url": "https://searx.example.org",
          "id": "default",
          "weight": 100
        }
      ],
      "fallback": {},
      "rotation": {
        "cooldown_seconds": 300,
        "disable_on_status": [401, 403],
        "retry_on_status": [429, 500, 502, 503, 504],
        "strategy": "round_robin"
      }
    },
    "exa": {
      "auth": {
        "header": "x-api-key",
        "key_refs": ["env:EXA_API_KEY_1", "env:EXA_API_KEY_2"],
        "prefix": "",
        "type": "api_key"
      },
      "capabilities": ["web_search", "web_fetch", "deep_research", "code_context", "related_pages"],
      "enabled": true,
      "endpoints": [
        {
          "base_url": "https://api.exa.ai",
          "id": "default",
          "weight": 100
        }
      ],
      "fallback": {},
      "rotation": {
        "cooldown_seconds": 300,
        "disable_on_status": [401, 403],
        "retry_on_status": [429, 500, 502, 503, 504],
        "strategy": "round_robin"
      }
    },
    "firecrawl": {
      "auth": {
        "header": "Authorization",
        "key_refs": ["env:FIRECRAWL_API_KEY_1", "env:FIRECRAWL_API_KEY_2"],
        "prefix": "Bearer ",
        "type": "api_key"
      },
      "capabilities": [
        "web_search",
        "web_fetch",
        "web_map",
        "web_crawl",
        "structured_extract",
        "web_interact",
        "web_monitor"
      ],
      "enabled": true,
      "endpoints": [
        {
          "base_url": "https://api.firecrawl.dev",
          "id": "default",
          "weight": 100
        }
      ],
      "fallback": {},
      "rotation": {
        "cooldown_seconds": 300,
        "disable_on_status": [401, 403],
        "retry_on_status": [429, 500, 502, 503, 504],
        "strategy": "round_robin"
      }
    },
    "tavily": {
      "auth": {
        "header": "Authorization",
        "key_refs": ["env:TAVILY_API_KEY_1", "env:TAVILY_API_KEY_2"],
        "prefix": "Bearer ",
        "type": "api_key"
      },
      "capabilities": ["web_search", "web_fetch", "web_map", "web_crawl", "deep_research"],
      "enabled": true,
      "endpoints": [
        {
          "base_url": "https://api.tavily.com",
          "id": "default",
          "weight": 100
        }
      ],
      "fallback": {},
      "rotation": {
        "cooldown_seconds": 300,
        "disable_on_status": [401, 403],
        "retry_on_status": [429, 500, 502, 503, 504],
        "strategy": "round_robin"
      }
    }
  },
  "version": 1
}
```

If the key values are managed by the shell or host app, export them there:

```bash
export EXA_API_KEY_1="..."
export EXA_API_KEY_2="..."
export FIRECRAWL_API_KEY_1="..."
export FIRECRAWL_API_KEY_2="..."
export TAVILY_API_KEY_1="..."
export TAVILY_API_KEY_2="..."
```

If ArkSpace should store the raw values locally, use `secrets.json`:

```json
{
  "secrets": {
    "EXA_API_KEY_1": "exa-key-1",
    "EXA_API_KEY_2": "exa-key-2",
    "FIRECRAWL_API_KEY_1": "fc-key-1",
    "FIRECRAWL_API_KEY_2": "fc-key-2",
    "TAVILY_API_KEY_1": "tvly-key-1",
    "TAVILY_API_KEY_2": "tvly-key-2"
  },
  "version": 1
}
```

Keep `secrets.json` private. It is local user configuration, not repository content.

Verify after manual edits:

```bash
python3 scripts/arkspace.py provider show
python3 scripts/arkspace.py provider resolve exa --capability web_search --require-secret
python3 scripts/arkspace.py provider resolve firecrawl --capability web_search --require-secret
python3 scripts/arkspace.py provider resolve tavily --capability web_search --require-secret
python3 scripts/arkspace.py provider check searxng --capability web_search
```

## Option 2: Command Setup

Use commands when configuring from a terminal or automation. This is the preferred path for predictable setup.

Show the active paths:

```bash
python3 scripts/arkspace.py provider paths
```

Configure a self-hosted SearXNG endpoint:

```bash
python3 scripts/arkspace.py provider configure searxng --base-url "https://searx.example.org"
python3 scripts/arkspace.py provider check searxng --capability web_search
```

The SearXNG runtime command also accepts a one-off URL override:

```bash
python3 scripts/arkspace.py web search --provider searxng "query" --base-url "https://searx.example.org"
```

Set up Exa with two private keys saved by ArkSpace:

```bash
python3 scripts/arkspace.py provider setup exa --wizard --key-count 2
python3 scripts/arkspace.py provider check exa --capability web_search
```

Set up Firecrawl with two private keys saved by ArkSpace:

```bash
python3 scripts/arkspace.py provider setup firecrawl --wizard --key-count 2
python3 scripts/arkspace.py provider check firecrawl --capability web_search
python3 scripts/arkspace.py provider check firecrawl --capability structured_extract
python3 scripts/arkspace.py provider check firecrawl --capability web_interact
python3 scripts/arkspace.py provider check firecrawl --capability web_monitor
```

Set up Tavily with two private keys saved by ArkSpace:

```bash
python3 scripts/arkspace.py provider setup tavily --wizard --key-count 2
python3 scripts/arkspace.py provider check tavily --capability web_search
```

Choose explicit key reference names:

```bash
python3 scripts/arkspace.py provider setup exa \
  --save-secret EXA_API_KEY_1 \
  --save-secret EXA_API_KEY_2 \
  --prompt

python3 scripts/arkspace.py provider setup firecrawl \
  --save-secret FIRECRAWL_API_KEY_1 \
  --save-secret FIRECRAWL_API_KEY_2 \
  --prompt

python3 scripts/arkspace.py provider setup tavily \
  --save-secret TAVILY_API_KEY_1 \
  --save-secret TAVILY_API_KEY_2 \
  --prompt
```

Use environment-managed keys as an alternative to ArkSpace `secrets.json`:

```bash
export EXA_API_KEY_1="..."
export EXA_API_KEY_2="..."

python3 scripts/arkspace.py provider setup exa \
  --env EXA_API_KEY_1 \
  --env EXA_API_KEY_2
```

Firecrawl supports the same environment-managed setup:

```bash
export FIRECRAWL_API_KEY_1="..."
export FIRECRAWL_API_KEY_2="..."

python3 scripts/arkspace.py provider setup firecrawl \
  --env FIRECRAWL_API_KEY_1 \
  --env FIRECRAWL_API_KEY_2
```

For non-interactive automation, pass one secret value per `--save-secret` through stdin:

```bash
python3 scripts/arkspace.py provider setup exa \
  --save-secret EXA_API_KEY_1 \
  --save-secret EXA_API_KEY_2 \
  --secret-stdin < /path/to/private-exa-keys.txt
```

Only use `--secret-stdin` in an environment where stdin handling and shell history are controlled.

For providers without setup defaults, configure the endpoint and add key references explicitly:

```bash
python3 scripts/arkspace.py provider configure brave-search --base-url "https://api.search.brave.com"
python3 scripts/arkspace.py provider add-key brave-search --env BRAVE_API_KEY_1 --header X-Subscription-Token
python3 scripts/arkspace.py provider add-key brave-search --env BRAVE_API_KEY_2 --header X-Subscription-Token
```

`provider add-key` stores key references only. The raw values must come from the host environment unless that provider later gets a `provider setup` default.

## Option 3: Agent-Guided Setup

Use agent-guided setup when working inside Claude Code, Codex, or another host that has ArkSpace installed.

Direct provider-manager invocation:

```text
/ark-space:provider-manager configure Exa with two API keys
/ark-space:provider-manager configure Firecrawl with two API keys
/ark-space:provider-manager configure Tavily with key rotation
/ark-space:provider-manager configure SearXNG at https://searx.example.org
```

Orchestrator-routed setup:

```text
/ark-space:orchestrator configure Exa for web search and code context
/ark-space:orchestrator configure Firecrawl for web scraping
/ark-space:orchestrator set up Tavily before running research
/ark-space:orchestrator configure a self-hosted SearXNG provider
```

When a provider-backed skill detects missing configuration, the agent should:

1. Name the missing provider and capability.
2. Ask whether to start setup now with two choices: `Start setup wizard` or `Not now`.
3. Resolve the installed ArkSpace package path and present the matching command.
4. Run the setup command only if the host shell can safely collect interactive secret input.
5. If the host shell is non-interactive, ask the user to run the command in an interactive terminal or use a `--save-secret ... --secret-stdin` flow.
6. Re-run `provider check` after setup.
7. Return to the original skill invocation after the provider resolves.

Installed host sessions must use the installed package path, not the repository path. For example:

```bash
python3 /Users/<user>/.claude/plugins/cache/ark-space/ark-space/0.1.2/scripts/arkspace.py provider setup exa --wizard --key-count 2
python3 /Users/<user>/.codex/plugins/cache/ark-space/ark-space/0.1.2/scripts/arkspace.py provider setup exa --wizard --key-count 2
```

If a host cannot provide interactive secret input, the agent should report the limitation, provide the exact interactive command, and re-check after setup completes.

## Rotation Model

The shared runtime supports multiple endpoints and multiple API key references. It chooses the least recently used active item, records failures in state, and applies cooldown after retryable failures.

Default behavior:

| Setting | Value |
|---|---|
| Strategy | `round_robin` using least recently used state |
| Retry statuses | `429,500,502,503,504` |
| Disable statuses | `401,403` |
| Cooldown | `300` seconds |

Provider scripts should call `record_provider_result()` after API-backed requests so later calls can avoid recently failed keys.
