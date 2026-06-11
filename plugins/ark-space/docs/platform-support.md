# Platform Support

Phase 1 supports Claude Code and Codex.

## Shared Source

Both supported hosts use:

- canonical skills from `skills/`
- callable agent sources from `agents/`
- workflow protocols from `workflows/`
- governance metadata from `registry/`

Host adapters consume the canonical skill bodies from `skills/`.

## Claude Code

Claude Code uses `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` for plugin metadata. The marketplace entry can point at the repository root because Claude Code supports relative plugin sources that resolve to the marketplace root.

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

Codex uses `.codex-plugin/plugin.json` for plugin metadata. Codex marketplace entries must point at a plugin subdirectory such as `./plugins/ark-space`; they cannot use the marketplace root as the local plugin source. The packaged plugin manifest points to:

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

The installable Codex package lives under `plugins/ark-space/` and mirrors the canonical root files. Rebuild it after canonical package edits:

```bash
python3 scripts/arkspace.py package-codex
```

Run validation after edits so stale package copies are caught before publishing.

## Validation

Run:

```bash
python3 scripts/arkspace.py doctor
```

The doctor command validates skills, agents, workflows, generated integrations, and local callability smoke checks.

After installing or refreshing a local host plugin, verify the installed cache:

```bash
python3 scripts/arkspace.py smoke-test --installed-host codex
python3 scripts/arkspace.py smoke-test --installed-host claude-code
```

Installed-host smoke tests compare critical cached skill, registry, and script files with the current package source. A stale cache must be refreshed before reporting host-level pass.

## Future Hosts

Future hosts add generated output under `integrations/<host>/` and adapter documentation here while reusing canonical skills and agents.
