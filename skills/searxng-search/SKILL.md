---
name: searxng-search
description: Use when querying a configured self-hosted SearXNG instance, the SearXNG Search API, or privacy-oriented metasearch through ArkSpace web_search routing.
---

# SearXNG Search

Use SearXNG for privacy-oriented metasearch when the user provides a SearXNG instance, asks to use a self-hosted search service, or explicitly wants SearXNG instead of a general web search tool. This is a `web_search` provider: it discovers URLs and snippets from a query, but it does not fetch full page content.

In ArkSpace, SearXNG is exposed through this skill and its bundled helper script.

## Source References

- Official documentation: `https://docs.searxng.org/`
- Search API: `https://docs.searxng.org/dev/search_api.html`
- Reference skill: `https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/research/searxng-search/SKILL.md`
- Provider reference: `https://docs.openclaw.ai/tools/searxng-search`

## Instance Selection

1. Prefer the user's explicit instance URL.
2. If not provided, use `SEARXNG_URL`.
3. If not set, use `SEARXNG_BASE_URL`.
4. If not set, use ArkSpace provider config, defaulting to `~/.config/ark-space/providers.json`.
5. If none exists, help the user configure SearXNG through `provider-manager`.
6. When multiple search skills exist, let Orchestrator choose the role first, then select this provider from `registry/search-providers.yaml`.
7. If the user provides an exact URL to read, route to a `web_fetch` provider instead of this skill.

## Before Use

Check configuration before searching when privacy, reproducibility, or reliability matters:

```bash
python3 scripts/arkspace.py provider check searxng
```

Persist a self-hosted URL once:

```bash
python3 scripts/arkspace.py provider configure searxng --base-url "https://searx.example.org"
```

Inspect the resolved configuration:

```bash
python3 scripts/arkspace.py provider resolve searxng --capability web_search
```

If the check fails because no instance is configured:

- If the user already gave a SearXNG URL, run `python3 scripts/arkspace.py provider configure searxng --base-url "<url>"` for them.
- If the user has not provided a URL, ask for the self-hosted SearXNG base URL.
- For one-off searches, use `--base-url`.

Configuration belongs in the host environment or ArkSpace user config, not in committed skill files. Use `--base-url` for one-off overrides, `SEARXNG_URL` / `SEARXNG_BASE_URL` for host-managed config, and `python3 scripts/arkspace.py provider configure searxng --base-url <url>` for durable user-level config. Set `ARKSPACE_PROVIDER_CONFIG` or pass `--config-path` to use a custom provider config file.

## API Pattern

SearXNG supports `GET /`, `GET /search`, `POST /`, and `POST /search`. For agent use, prefer:

```bash
curl -G "$SEARXNG_URL/search" \
  --data-urlencode "q=site:github.com searxng" \
  --data-urlencode "format=json"
```

Common parameters:

| Parameter | Use |
|---|---|
| `q` | Required query string |
| `format` | `json`, `csv`, or `rss`; must be enabled by the instance |
| `categories` | Comma-separated categories |
| `engines` | Comma-separated engine names |
| `language` | Search language code |
| `pageno` | Page number, default `1` |
| `time_range` | `day`, `month`, or `year` when supported |
| `safesearch` | `0`, `1`, or `2` |

If `format=json` returns `403`, `406`, or HTML, the instance probably has JSON disabled; try another instance or use HTML only when a readable page is acceptable.

## Helper Script

Use the bundled helper for repeatable searches:

```bash
python3 skills/searxng-search/scripts/searxng_search.py "query text"
```

Check configured availability:

```bash
python3 scripts/arkspace.py provider check searxng
```

Self-hosted instance:

```bash
SEARXNG_URL="https://searx.example.org" \
python3 skills/searxng-search/scripts/searxng_search.py "query text" --limit 5
```

Persisted self-hosted instance:

```bash
python3 scripts/arkspace.py provider configure searxng --base-url "https://searx.example.org"
python3 skills/searxng-search/scripts/searxng_search.py "query text" --limit 5
```

`SEARXNG_BASE_URL` is also accepted for hosts that use that convention.

Explicit instance and filters:

```bash
python3 skills/searxng-search/scripts/searxng_search.py "query text" \
  --base-url "https://searx.example.org" \
  --categories general \
  --language en \
  --time-range month \
  --safesearch 1
```

Output modes:

```bash
python3 skills/searxng-search/scripts/searxng_search.py "query text" --output markdown
python3 skills/searxng-search/scripts/searxng_search.py "query text" --output json
```

If a non-`general` category returns zero results, the helper retries once with `categories=general` unless `--no-category-fallback` is set.

## Result Handling

- Cite result URLs when using SearXNG output in an answer.
- Treat results as discovery snippets: SearXNG returns titles, URLs, snippets, engines, and optional media/date fields, not full article content.
- Prefer opening primary sources from the result list before making factual claims.
- Mention the instance used when result quality or reproducibility matters.
- For current, legal, medical, financial, or other high-stakes facts, verify with primary sources after discovery.

## Troubleshooting

| Symptom | Response |
|---|---|
| `403 Forbidden` | JSON format is disabled or request is blocked; try another instance |
| `429 Too Many Requests` | Instance rate limited the request; use a better self-hosted endpoint or another configured `web_search` provider |
| Empty results | Retry with broader terms, different engines, or another instance |
| Timeout | Use self-hosted instance or reduce candidate count |
| Captcha/block page | Do not bypass; switch to a configured endpoint |
| Missing self-hosted URL | Use `provider-manager` to configure SearXNG before searching |
