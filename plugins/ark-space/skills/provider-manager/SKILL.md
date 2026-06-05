---
name: provider-manager
description: Use when configuring ArkSpace providers, fixing missing provider URLs or API keys, checking search/fetch provider readiness, or setting up multiple API key rotation.
---

# Provider Manager

Manage provider configuration as a guided runtime setup, not as manual file editing.

Use this when a skill reports missing provider configuration, the user wants to set a self-hosted service URL, or a provider needs one or more API keys. Public package files only declare provider capabilities. Personal endpoints and key references live in user config.

## Configuration Rule

Do not ask the user to find and edit config files by hand. Help them run the setup command.

Provider config defaults to:

```bash
~/.config/ark-space/providers.json
```

Provider state defaults to:

```bash
~/.local/state/ark-space/provider-state.json
```

Override paths with `ARKSPACE_PROVIDER_CONFIG`, `ARKSPACE_PROVIDER_STATE`, `--config-path`, or `--state-path`.

## Common Commands

Show paths:

```bash
python3 scripts/arkspace_provider.py paths
```

Configure a self-hosted SearXNG endpoint:

```bash
python3 scripts/arkspace_provider.py configure searxng --base-url "https://searx.example.org"
```

Inspect provider config without secret values:

```bash
python3 scripts/arkspace_provider.py show
```

Resolve a provider before use:

```bash
python3 scripts/arkspace_provider.py resolve searxng --capability web_search
```

Add API key references for future API-backed providers:

```bash
python3 scripts/arkspace_provider.py add-key brave-search --env BRAVE_API_KEY_1 --header X-Subscription-Token
python3 scripts/arkspace_provider.py add-key brave-search --env BRAVE_API_KEY_2 --header X-Subscription-Token
```

The config stores `env:BRAVE_API_KEY_1` references, not the actual key values.

## Key Rotation

ArkSpace provider runtime supports multiple API key references per provider. It resolves available `env:<NAME>` values, selects the least recently used key, and stores cooldown state locally after failures.

Default rotation behavior:

| Setting | Default |
|---|---|
| Strategy | `round_robin` using least recently used state |
| Retry statuses | `429,500,502,503,504` |
| Disable statuses | `401,403` |
| Cooldown | `300` seconds |

Provider scripts should record request results through `arkspace_runtime.provider_config.record_provider_result()` when they add API-backed calls.

## Agent Behavior

When a provider is missing:

1. Explain the exact capability that is missing, such as `web_search`.
2. Give the one setup command that fixes it.
3. If the user provided the needed URL or env var name, run the command for them.
4. Re-run the provider check.

For secrets, never ask the user to paste a raw API key into committed files. Prefer environment variables or host-managed secret storage.
