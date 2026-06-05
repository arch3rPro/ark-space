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

Override them with:

```bash
export ARKSPACE_PROVIDER_CONFIG="/path/to/providers.json"
export ARKSPACE_PROVIDER_STATE="/path/to/provider-state.json"
```

## Configure SearXNG

Run:

```bash
python3 scripts/arkspace_provider.py configure searxng --base-url "https://searx.example.org"
python3 scripts/arkspace_provider.py resolve searxng --capability web_search
python3 skills/searxng-search/scripts/searxng_search.py --check
```

The SearXNG helper also accepts one-off overrides:

```bash
python3 skills/searxng-search/scripts/searxng_search.py "query" --base-url "https://searx.example.org"
```

Host-managed environment variables still work:

```bash
export SEARXNG_URL="https://searx.example.org"
```

## API Key References

For API-backed providers, store only key references in ArkSpace config. Store actual keys in the host environment or secret manager.

```bash
export BRAVE_API_KEY_1="..."
export BRAVE_API_KEY_2="..."

python3 scripts/arkspace_provider.py add-key brave-search --env BRAVE_API_KEY_1 --header X-Subscription-Token
python3 scripts/arkspace_provider.py add-key brave-search --env BRAVE_API_KEY_2 --header X-Subscription-Token
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

## Public Fallback Policy

ArkSpace does not use public SearXNG instance fallback. In practice, public instances often disable JSON output, rate limit automated requests, or block them entirely. Missing SearXNG configuration should trigger guided setup or selection of another configured `web_search` provider.
