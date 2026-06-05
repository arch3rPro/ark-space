# Architecture

This repository is a general Agent Skills package.

The canonical skill source is `skills/<skill-name>/SKILL.md`. Claude Code, Codex, and future hosts should consume the same skill files instead of maintaining platform-specific copies.

## Layers

- `skills/`: executable skill instructions.
- `roles/`: role definitions that compose skills for common work types.
- `registry/`: governance metadata for skills, roles, and upstream sources.
- `.claude-plugin/`: Claude Code plugin metadata.
- `.codex-plugin/`: Codex plugin metadata.
- `overlays/`: examples and documentation for private local customization.
- `reference/`: optional local or tracked area for upstream projects used as design reference.

## Default Entry

The default role is `orchestrator`. It uses lightweight routing to choose the smallest useful role and workflow for a task.

## Existing Obsidian Skills

The Obsidian skills remain active. They are now classified as documentation and knowledge-management tooling rather than the identity of the whole repository.
