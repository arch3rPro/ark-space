# Changelog

All notable changes to ArkSpace are documented here.

This project uses human-readable release notes. Dates use `YYYY-MM-DD`.

## Unreleased

- Codex marketplace packaging now uses a real `plugins/ark-space/` package directory instead of an invalid repository-root source or symlink wrapper.
- Validation now checks the Codex package directory for required files, symlinks, and stale copies against canonical root sources.
- `python3 scripts/arkspace.py package-codex` now rebuilds the Codex marketplace package from canonical root files.
- Claude marketplace metadata now includes a marketplace description and explicit strict-mode intent.
- Callable ArkSpace agent runtime files, generated host integrations, and callability checks added.
- Local `reference/` checkouts and local process planning files are ignored.
- Provider Manager skill and `scripts/arkspace_provider.py` added for guided provider setup, readiness checks, and future API key rotation.
- Shared provider runtime added under `scripts/arkspace_runtime/` for user config, endpoint resolution, key references, and cooldown state.
- SearXNG helper now reads ArkSpace provider config and requires a configured endpoint.
- SearXNG helper can persist a self-hosted URL in ArkSpace provider config via `--save-base-url`.
- Codex marketplace catalog added under `.agents/plugins/marketplace.json` for GitHub marketplace installation.
- SearXNG search skill added with self-hosted instance support.
- Web provider registries split `web_search` discovery from `web_fetch` URL extraction for future provider expansion.
- Search providers now declare configuration metadata and runtime check behavior for host-provided settings.
- Project name and package identity updated to ArkSpace / `ark-space`.
- Root agent guidance added for Claude Code and other agents.
- Project governance files added for contribution, support, security, notices, and conduct.

## 0.1.0 - 2026-06-05

Initial ArkSpace package foundation.

### Added

- Shared Agent Skills tree under `skills/`.
- Lightweight Orchestrator skill for routing tasks to the smallest useful role and workflow.
- Skill Manager skill for source governance, registry updates, and validation.
- Role definitions for code, docs, product, project, skills, and knowledge-management work.
- Registries for skills, roles, and upstream sources.
- Claude Code plugin metadata under `.claude-plugin/`.
- Codex plugin metadata under `.codex-plugin/`.
- Public/private overlay documentation.
- Validation script for skill frontmatter, registries, roles, and plugin manifests.

### Changed

- Repositioned the package from an Obsidian-focused skills collection into a general multi-role agent skills workspace.
- Reclassified existing Obsidian skills as knowledge-management and documentation tooling.

### Notes

- No release, tag, or publishing workflow has been run for this version.
