# Provider Configuration

ArkSpace provider setup is guided by commands. Users should not need to find and edit config files manually.

## Paths

Provider config defaults to:

```bash
~/.config/ark-space/providers.json
```

Provider runtime state defaults to:

```bash
~/.local/state/ark-space/provider-state.json
```

Provider secrets default to:

```bash
~/.config/ark-space/secrets.json
```

Override them with:

```bash
export ARKSPACE_PROVIDER_CONFIG="/path/to/providers.json"
export ARKSPACE_PROVIDER_STATE="/path/to/provider-state.json"
export ARKSPACE_PROVIDER_SECRETS="/path/to/secrets.json"
```

## Configure SearXNG

Run:

```bash
python3 scripts/arkspace.py provider configure searxng --base-url "https://searx.example.org"
python3 scripts/arkspace.py provider resolve searxng --capability web_search
python3 scripts/arkspace.py provider check searxng
```

The SearXNG helper also accepts one-off overrides:

```bash
python3 scripts/arkspace.py web search --provider searxng "query" --base-url "https://searx.example.org"
```

Host-managed environment variables still work:

```bash
export SEARXNG_URL="https://searx.example.org"
```

## API Key References

For API-backed providers, ArkSpace provider config stores key references. Raw key values can stay in the host environment or be stored in ArkSpace's local private secrets file.

For Tavily or Exa, use the setup command. It writes provider config and prompts for the key values:

```bash
python3 scripts/arkspace.py provider setup tavily --wizard --key-count 2
python3 scripts/arkspace.py provider check tavily
python3 scripts/arkspace.py provider setup exa --wizard --key-count 2
python3 scripts/arkspace.py provider check exa
```

If you want to choose the stored key reference names explicitly:

```bash
python3 scripts/arkspace.py provider setup tavily --save-secret TAVILY_API_KEY_1 --save-secret TAVILY_API_KEY_2 --prompt
python3 scripts/arkspace.py provider check tavily
```

The setup command writes the Tavily endpoint, Tavily capabilities (`web_search`, `web_fetch`, `web_map`, `web_crawl`, `deep_research`), key references, and private secret values in one flow. Provider config stores references such as `env:TAVILY_API_KEY_1`; raw keys are stored in `~/.config/ark-space/secrets.json` with `0600` permissions.

Exa setup writes the Exa endpoint, Exa capabilities (`web_search`, `web_fetch`, `deep_research`, `code_context`, `related_pages`), key references such as `env:EXA_API_KEY_1`, and private secret values with the same rotation model.

For non-interactive setup, provide one secret value per `--save-secret` through stdin:

```bash
python3 scripts/arkspace.py provider setup tavily \
  --save-secret TAVILY_API_KEY_1 \
  --save-secret TAVILY_API_KEY_2 \
  --secret-stdin

python3 scripts/arkspace.py provider setup exa \
  --save-secret EXA_API_KEY_1 \
  --save-secret EXA_API_KEY_2 \
  --secret-stdin
```

For providers without setup defaults, use the lower-level key reference command:

```bash
export BRAVE_API_KEY_1="..."
export BRAVE_API_KEY_2="..."

python3 scripts/arkspace.py provider add-key brave-search --env BRAVE_API_KEY_1 --header X-Subscription-Token
python3 scripts/arkspace.py provider add-key brave-search --env BRAVE_API_KEY_2 --header X-Subscription-Token
```

The config stores `env:BRAVE_API_KEY_1`, not the secret value.

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
