# SearXNG provider reference

SearXNG is a privacy-oriented `web_search` provider: it discovers URLs and snippets from a query via a self-hosted SearXNG instance, but it does not fetch full page content.

## Source references

- Official documentation: `https://docs.searxng.org/`
- Search API: `https://docs.searxng.org/dev/search_api.html`

## Instance selection

1. Prefer the user's explicit instance URL.
2. If not provided, use `SEARXNG_URL`.
3. If not set, use `SEARXNG_BASE_URL`.
4. If not set, use ArkSpace provider config, defaulting to `~/.config/ark-space/providers.json`.
5. If none exists, help the user configure SearXNG through `provider-manager`.

Persist a self-hosted URL once:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider configure searxng --base-url "https://searx.example.org"
```

Inspect the resolved configuration:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider resolve searxng --capability web_search
```

Use `--base-url` for one-off overrides; `SEARXNG_URL` / `SEARXNG_BASE_URL` for host-managed config; `provider configure searxng --base-url <url>` for durable user-level config. Set `ARKSPACE_PROVIDER_CONFIG` or pass `--config-path` to use a custom provider config file.

## API pattern

SearXNG supports `GET /`, `GET /search`, `POST /`, and `POST /search`. For agent use, prefer:

```bash
curl -G "$SEARXNG_URL/search" \
  --data-urlencode "q=site:github.com searxng" \
  --data-urlencode "format=json"
```

Common parameters:

| Parameter | Use |
| --- | --- |
| `q` | Required query string |
| `format` | `json`, `csv`, or `rss`; must be enabled by the instance |
| `categories` | Comma-separated categories |
| `engines` | Comma-separated engine names |
| `language` | Search language code |
| `pageno` | Page number, default `1` |
| `time_range` | `day`, `month`, or `year` when supported |
| `safesearch` | `0`, `1`, or `2` |

If `format=json` returns `403`, `406`, or HTML, the instance probably has JSON disabled; try another instance or use HTML only when a readable page is acceptable.

## Helper script

Use the bundled helper for repeatable searches:

```bash
python3 <installed-arkspace-path>/skills/web-search/scripts/searxng_search.py "query text"
python3 <installed-arkspace-path>/skills/web-search/scripts/searxng_search.py "query text" --limit 5
python3 <installed-arkspace-path>/skills/web-search/scripts/searxng_search.py "query text" \
  --base-url "https://searx.example.org" \
  --categories general \
  --language en \
  --time-range month \
  --safesearch 1
python3 <installed-arkspace-path>/skills/web-search/scripts/searxng_search.py "query text" --output markdown
python3 <installed-arkspace-path>/skills/web-search/scripts/searxng_search.py "query text" --output json
```

If a non-`general` category returns zero results, the helper retries once with `categories=general` unless `--no-category-fallback` is set.

## Troubleshooting

| Symptom | Response |
| --- | --- |
| `403 Forbidden` | JSON format is disabled or request is blocked; try another instance |
| `429 Too Many Requests` | Instance rate limited; use a better self-hosted endpoint or another configured `web_search` provider |
| Empty results | Retry with broader terms, different engines, or another instance |
| Timeout | Use self-hosted instance or reduce candidate count |
| Captcha/block page | Do not bypass; switch to a configured endpoint |
| Missing self-hosted URL | Use `provider-manager` to configure SearXNG before searching |
