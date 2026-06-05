# Platform Support

Phase 1 supports Claude Code and Codex.

## Claude Code

Claude Code uses `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`.

The plugin ships one shared skills package. Roles are defined under `roles/`; they are not separate Claude plugins.

## Codex

Codex uses `.codex-plugin/plugin.json`.

The manifest points to:

```json
"skills": "./skills/"
```

Codex and Claude Code should consume the same `skills/` directory.

## Skill Content

Skill instructions should stay host-neutral when possible. Prefer wording such as "read the relevant files" over hard-coded tool names. Host-specific differences belong in platform documentation or references.

## Planned Later

OpenCode, Gemini, Cursor, and other hosts can be added later by adding platform manifests and documentation without changing the canonical skill bodies.
