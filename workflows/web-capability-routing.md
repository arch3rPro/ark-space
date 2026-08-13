# Web Capability Routing

Resolve capability before selecting a provider. This is the authoritative routing matrix for ambiguous public-web intent:

```text
find sources/pages -> web-search
read supplied URL(s) -> web-fetch
extract requested fields/schema from supplied URL(s) -> web-extract
synthesize cited answer across sources -> web-research
discover/crawl a known site -> web-site
interact or manage monitors -> web-automation
```

## Boundaries

- A supplied URL is normally read with `web-fetch`. Use `web-extract` only when the requested result is structured fields or a schema; use `web-search` or `web-site` only when discovery is also required.
- For a known site, `map` discovers its URL structure; `crawl` collects content from a requested site section. Map before crawl when the target pages are unknown.
- Fetch, extract, map, and crawl are read-only. `web-automation` is stateful: use `interact` for live page actions and `monitor` for recurring checks.
- Monitor inspection is read-only; monitor mutation requires confirmation of the target, schedule, and goal.

## Provider Resolution

Resolve the capability first, then consult its provider registry. Skill-level provider omission is allowed after capability resolution: the owning skill may apply its registry preference. Raw CLI receives explicit `--provider` so the command is reproducible. Provider setup remains delegated to `provider-manager`; provider preference details stay in the owning skill.
