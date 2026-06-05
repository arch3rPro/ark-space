# Support

ArkSpace is a local Agent Skills package. Support requests should include enough context to reproduce the problem.

## Good Support Requests

Include:

- Host environment: Claude Code, Codex, or another compatible agent host.
- Operating system and shell.
- The skill, role, or manifest involved.
- Exact command output or validation failure.
- Whether the issue affects public package files or private overlays.

## Common Checks

Run:

```bash
python3 scripts/validate-skills.py
```

For plugin metadata problems, run:

```bash
python3 -m json.tool .claude-plugin/plugin.json >/dev/null
python3 -m json.tool .claude-plugin/marketplace.json >/dev/null
python3 -m json.tool .codex-plugin/plugin.json >/dev/null
```

## Boundaries

This project does not provide support for private overlay contents, unrelated host configuration, or upstream tools outside the ArkSpace package unless the issue is caused by this repository.
