# Maintenance

This document is for ArkSpace maintainers. The README focuses on how an AI agent uses the package; operational commands live here.

## Regenerate Host Agents

Update `agents/` first, then regenerate host-native outputs:

```bash
python3 scripts/arkspace.py convert --host all
```

Generated files live under `integrations/` as derived outputs from `agents/`.

## Rebuild Codex Package

The Codex marketplace package under `plugins/ark-space/` is generated from canonical sources:

```bash
python3 scripts/arkspace.py package-codex
```

Run this after changing skills, agents, workflows, registries, docs, scripts, README, license, or notice files.

## Validate Source And Package

Use the normal doctor command for source, package, generated-agent, and local invocation checks:

```bash
python3 scripts/arkspace.py doctor
```

Use installed-host gates before calling a change usable in a local Claude Code or Codex session:

```bash
python3 scripts/arkspace.py doctor --installed-host all
```

Individual installed-host checks:

```bash
python3 scripts/arkspace.py smoke-test --installed-host codex
python3 scripts/arkspace.py smoke-test --installed-host claude-code
```

## Local Host Cache Refresh

For local development, refresh installed plugin caches only after package validation is clean.

Codex cache:

```bash
rsync -a --delete plugins/ark-space/ ~/.codex/plugins/cache/ark-space/ark-space/0.1.2/
```

Claude Code cache:

```bash
for item in .claude-plugin agents docs registry roles scripts skills workflows README.md README.zh-CN.md LICENSE NOTICE.md; do
  rsync -a --delete --exclude 'superpowers' "$item" ~/.claude/plugins/cache/ark-space/ark-space/0.1.2/
done
```

## Codex Marketplace Development

The Codex marketplace catalog lives at `.agents/plugins/marketplace.json`. The entry points at `plugins/ark-space/`, which must be a real packaged plugin directory.

After changing package content:

```bash
python3 scripts/arkspace.py package-codex
python3 scripts/arkspace.py doctor
```

Refresh an existing local marketplace snapshot:

```bash
codex plugin marketplace upgrade ark-space
codex plugin list --marketplace ark-space
codex plugin add ark-space@ark-space
```

## Provider Setup Checks

Provider setup details live in [provider-configuration.md](provider-configuration.md). For smoke checks, verify capability readiness through ArkSpace:

```bash
python3 scripts/arkspace.py provider check searxng --capability web_search
python3 scripts/arkspace.py provider check arxiv --capability web_search
python3 scripts/arkspace.py provider check exa --capability web_search
python3 scripts/arkspace.py provider check tavily --capability web_search
python3 scripts/arkspace.py provider check firecrawl --capability web_search
```

Provider checks prove local configuration resolution. Host discovery is verified separately with installed-host smoke tests.
