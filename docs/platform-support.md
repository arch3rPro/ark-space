# Platform Support

Phase 1 supports Claude Code and Codex.

## Shared Source

Both supported hosts use:

- canonical skills from `skills/`
- callable agent sources from `agents/`
- workflow protocols from `workflows/`
- governance metadata from `registry/`

Host adapters must not create separate skill bodies.

## Claude Code

Claude Code uses `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` for plugin metadata.

Generate Claude Code agent files with:

```bash
python3 scripts/arkspace.py convert --host claude-code
```

Dry-run install:

```bash
python3 scripts/arkspace.py install --host claude-code --dry-run
```

Generated files live under `integrations/claude-code/agents/`.

## Codex

Codex uses `.codex-plugin/plugin.json` for plugin metadata. The manifest points to:

```json
"skills": "./skills/"
```

Generate Codex custom agent TOML files with:

```bash
python3 scripts/arkspace.py convert --host codex
```

Dry-run install:

```bash
python3 scripts/arkspace.py install --host codex --dry-run
```

Generated files live under `integrations/codex/agents/`.

## Validation

Run:

```bash
python3 scripts/arkspace.py doctor
```

The doctor command validates skills, agents, workflows, generated integrations, and local callability smoke checks.

## Future Hosts

Future hosts should add generated output under `integrations/<host>/` and adapter documentation here. They should not require rewriting canonical skills or agents.
