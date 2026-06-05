---
name: searxng-search
description: Use when querying SearXNG search, a self-hosted SearXNG instance, the SearXNG Search API, or public SearXNG fallback instances from searx.space.
---

# SearXNG Search

Use SearXNG for privacy-oriented metasearch when the user provides a SearXNG instance, asks to use a self-hosted search service, or explicitly wants SearXNG instead of a general web search tool. This is a `web_search` provider: it discovers URLs and snippets from a query, but it does not fetch full page content.

## Source References

- Official documentation: `https://docs.searxng.org/`
- Search API: `https://docs.searxng.org/dev/search_api.html`
- Public instance list: `https://searx.space/`
- Machine-readable instance list: `https://searx.space/data/instances.json`
- Reference skill: `https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/research/searxng-search/SKILL.md`
- Provider reference: `https://docs.openclaw.ai/tools/searxng-search`

## Instance Selection

1. Prefer the user's explicit instance URL.
2. If not provided, use `SEARXNG_URL`.
3. If not set, use `SEARXNG_BASE_URL`.
4. If neither exists and the query is not sensitive, use `searx.space` public instances as fallback.
5. Do not send private, internal, credential-bearing, personal, or embargoed queries to public instances without explicit user approval.
6. Treat public instances as best-effort: many disable JSON output, rate limit, block automation, or return weaker results under high traffic.
7. When multiple search skills exist, let Orchestrator choose the role first, then select this provider from `registry/search-providers.yaml`.
8. If the user provides an exact URL to read, route to a `web_fetch` provider instead of this skill.

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

Use the bundled helper for repeatable searches and fallback handling:

```bash
python3 skills/searxng-search/scripts/searxng_search.py "query text"
```

Check configured availability:

```bash
python3 skills/searxng-search/scripts/searxng_search.py --check
```

Self-hosted instance:

```bash
SEARXNG_URL="https://searx.example.org" \
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

Disable public fallback:

```bash
python3 skills/searxng-search/scripts/searxng_search.py "query text" --no-public-fallback
```

Output modes:

```bash
python3 skills/searxng-search/scripts/searxng_search.py "query text" --output markdown
python3 skills/searxng-search/scripts/searxng_search.py "query text" --output json
```

When JSON API access fails on every public instance, the helper emits HTML search URLs for the best candidate instances. Open those URLs only for non-sensitive queries, or ask the user for a self-hosted instance URL.

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
| `429 Too Many Requests` | Public limiter rejected the request; use self-hosted SearXNG or HTML fallback links |
| Empty results | Retry with broader terms, different engines, or another instance |
| Timeout | Use self-hosted instance or reduce candidate count |
| Captcha/block page | Do not bypass; switch instance or ask for self-hosted URL |
| Sensitive query without self-host | Ask before using public fallback |
