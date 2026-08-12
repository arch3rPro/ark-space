# Jina (web search)

`jina` is a keyless `web_search` provider backed by the Jina Reader endpoint
(`s.jina.ai`). It needs no API key and no setup. If a `JINA_API_KEY` happens to
be configured (process environment or the ArkSpace `jina` provider api_key), it
is sent only when present; otherwise the request is anonymous.

## Usage

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py web search --provider jina "agent skills" --max-results 5 --output json
python3 <installed-arkspace-path>/scripts/arkspace.py web search --providers exa-mcp,jina "agent skills" --max-results 5
```

Like the other zero-config providers, `jina` accepts only the common chain
arguments. Provider-specific flags are rejected; use an explicit matching
`--provider` for those.

## Caveats

- Results are parsed from the Reader's Markdown output, so snippet shape is
  heuristic and can drift if Jina changes its page format.
- It is a `_COMMON_ONLY_PROVIDERS` member: no provider-specific search controls.
- `provider check jina` verifies registration and keyless status; it performs
  no network call.
