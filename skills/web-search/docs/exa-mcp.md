# Exa MCP (web search)

`exa-mcp` is the zero-config default `web_search` provider. It queries the
Exa MCP endpoint over HTTP with no API key and no setup, so a plain query works
out of the box.

## Default behavior

- The default `web search` invocation uses `exa-mcp` when no provider is named:

  ```bash
  python3 <installed-arkspace-path>/scripts/arkspace.py web search "agent skills"
  ```

- It is keyless (`configRequired: false`, `authModes: none`). There is nothing
  to configure and no hidden fallback: if `exa-mcp` itself is unreachable, the
  command fails rather than silently switching providers.

- It is a `_COMMON_ONLY_PROVIDERS` member: it accepts only the common chain
  arguments (`query`, `--max-results`, `--timeout`, `--output`,
  `--config-path`, `--state-path`). Provider-specific flags such as
  `--search-type` or `--include-domains` are rejected with a clear error; use
  an explicit matching `--provider` (for example `--provider exa`) for those
  options.

## Explicit use and chains

Name it explicitly or include it in a `--providers` chain:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py web search --provider exa-mcp "agent skills" --max-results 5 --output json
python3 <installed-arkspace-path>/scripts/arkspace.py web search --providers exa-mcp,jina "agent skills" --max-results 5
```

In a chain, only common chain flags are forwarded to each candidate; the chain
reports which provider actually produced each result.

## Caveats

- Zero-config means no key management, but also no per-provider controls
  (depth, domains, dates, summaries). Reach for `exa` (semantic, keyed) when
  those controls matter.
- `provider check exa-mcp` verifies the provider is registered and keyless; it
  performs no network call.
