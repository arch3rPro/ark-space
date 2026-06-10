---
name: provider-manager
description: Use when configuring ArkSpace providers, fixing missing provider URLs or API keys, checking provider readiness, or setting up multiple API key rotation.
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

Provider secrets default to:

```bash
~/.config/ark-space/secrets.json
```

Override paths with `ARKSPACE_PROVIDER_CONFIG`, `ARKSPACE_PROVIDER_STATE`, `ARKSPACE_PROVIDER_SECRETS`, `--config-path`, or `--state-path`.

## Common Commands

Resolve the installed ArkSpace package root before running commands. Replace `<installed-arkspace-path>` with the directory two levels above the loaded ArkSpace `SKILL.md`, such as `/Users/<user>/.claude/plugins/cache/ark-space/ark-space/0.1.2`. Use the installed package path, not a repository-relative command, in installed host sessions.

Show paths:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider paths
```

Configure a self-hosted SearXNG endpoint:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider configure searxng --base-url "https://searx.example.org"
```

Configure Tavily API-backed skills:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider setup tavily --wizard --key-count 2
python3 <installed-arkspace-path>/scripts/arkspace.py provider check tavily --capability web_search
```

Inspect provider config without secret values:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider show
```

Resolve a provider before use:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider resolve searxng --capability web_search
```

Add API key references for future API-backed providers:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider add-key brave-search --env BRAVE_API_KEY_1 --header X-Subscription-Token
python3 <installed-arkspace-path>/scripts/arkspace.py provider add-key brave-search --env BRAVE_API_KEY_2 --header X-Subscription-Token
```

The provider config stores `env:BRAVE_API_KEY_1` or `env:TAVILY_API_KEY_1` references. When `--save-secret` is used, the actual key values are stored in the local private secrets file with `0600` permissions.

Use `provider setup` when a provider has ArkSpace defaults, such as Tavily. Use `provider configure` and `provider add-key` as advanced commands for self-hosted endpoints or new providers that do not have setup defaults yet.

## Key Rotation

ArkSpace provider runtime supports multiple API key references per provider. It resolves available `env:<NAME>` values from the process environment first, then ArkSpace's private secrets file, selects the least recently used key, and stores cooldown state locally after failures.

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
2. Ask whether to start setup now and present exactly two choices:
   - "Start setup wizard" - start interactive setup with the setup command.
   - "Not now" - leave the provider unconfigured; if the user still wants results, ask whether to continue with a clearly labeled non-ArkSpace fallback.
3. Give the one setup command that fixes it. For Tavily API keys, prefer `provider setup tavily --wizard`.
4. If the current host can execute shell commands and can provide interactive secret input, run the setup command for them.
5. If the host shell is non-interactive, do not run `--wizard` through that tool. Offer either interactive terminal setup or saving a pasted key through `provider setup tavily --save-secret TAVILY_API_KEY --secret-stdin`.
6. Re-run the provider check after setup.
7. If setup succeeds, rerun or tell the user to rerun the original skill invocation.

For secrets, never ask the user to paste a raw API key into committed files. Use the private ArkSpace secrets file through `--save-secret` or environment variables.
