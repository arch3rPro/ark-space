# Changelog

All notable changes to ArkSpace are documented here.

This project uses human-readable release notes. Dates use `YYYY-MM-DD`.

## Unreleased

- SearXNG search skill added with self-hosted instance support and searx.space public fallback discovery.
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
