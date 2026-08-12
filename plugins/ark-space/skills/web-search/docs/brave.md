# Brave (web search)

`brave` is a keyed `web_search` provider backed by the Brave Search API. Unlike
the other new providers, it requires an API key.

## Configuration

Brave needs a `BRAVE_API_KEY`. Configure it through `provider-manager`:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider setup brave --wizard
python3 <installed-arkspace-path>/scripts/arkspace.py provider setup brave --save-secret BRAVE_API_KEY --secret-stdin
```

The key is resolved from the process environment or ArkSpace's private secret
store, and rotation/cooldown reuse the existing provider-manager key store.

## Usage

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py web search --provider brave "agent skills" --max-results 5 --output json
python3 <installed-arkspace-path>/scripts/arkspace.py web search --providers exa-mcp,brave "agent skills" --max-results 5
```

## Caveats

- It is a `_COMMON_ONLY_PROVIDERS` member: only the common chain arguments are
  accepted; provider-specific flags are rejected.
- `provider check brave` verifies that the API key resolves locally (no network
  call). If the key is missing, the check fails with a setup hint pointing to
  `provider setup brave --wizard`.
- Brave requests a live credential, so a live smoke run uses a dedicated test
  key; an unconfigured Brave must not invalidate deterministic checks.
