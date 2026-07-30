---
name: code-context
description: Use when implementation work needs externally grounded code examples, API syntax, framework setup, or library usage context.
---

# Code Context

Retrieve implementation-oriented context through the configured provider selected by `registry/code-context-providers.yaml`. Accept a technical query, token budget, timeout, and output controls. Report the actual provider and citations or source URLs when supplied.

Use local repository evidence first. This skill supplements, never replaces, inspection of the code being changed.

## Run

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py code context --provider exa "React hooks state management examples" --output json
```

For setup or a failed provider check, use `provider-manager`.
