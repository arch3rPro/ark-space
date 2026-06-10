---
name: exa-context
description: Use when a coding task needs Exa Code context, practical library examples, API syntax, framework setup, or repository-grounded snippets beyond local code.
---

# Exa Context

Use Exa Context as an API-backed `code_context` provider when a code role needs token-efficient examples from GitHub repositories, docs pages, Stack Overflow posts, and related technical sources.

Exa configuration is shared with all Exa skills through `provider-manager`.

## Source References

- Official Context API: `https://exa.ai/docs/reference/context`
- Official Search API: `https://exa.ai/docs/reference/search`
- Hermes Exa provider reference: `https://raw.githubusercontent.com/NousResearch/hermes-agent/main/plugins/web/exa/provider.py`

## Before Use

Resolve the installed ArkSpace package root before running commands. Replace `<installed-arkspace-path>` with the directory two levels above this loaded `SKILL.md`, such as `/Users/<user>/.claude/plugins/cache/ark-space/ark-space/0.1.2`. Use the installed package path, not a repository-relative command.

Check configuration:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider check exa --capability code_context
```

Configure Exa once:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider setup exa --wizard
```

## Missing Configuration Recovery

If the provider check reports a missing Exa API key:

1. Ask the user whether to start setup now: "Exa is not configured. Should I start the ArkSpace setup wizard now?"
2. Present exactly two choices:
   - "Start setup wizard" - start interactive setup with `python3 <installed-arkspace-path>/scripts/arkspace.py provider setup exa --wizard`.
   - "Not now" - leave Exa unconfigured; if the user still wants results, ask whether to continue with another registered provider or a clearly labeled non-ArkSpace fallback.
3. Run the setup command only when the host shell can provide interactive secret input. If the shell is non-interactive, do not run `--wizard` through that tool.
4. In Claude Code non-interactive tool sessions, offer:
   - run `! python3 <installed-arkspace-path>/scripts/arkspace.py provider setup exa --wizard` in the Claude prompt or terminal, or
   - paste the API key in chat and let the agent save it with `python3 <installed-arkspace-path>/scripts/arkspace.py provider setup exa --save-secret EXA_API_KEY --secret-stdin`.
5. Re-run the provider check after setup.
6. If setup succeeds, rerun or tell the user to rerun the original invocation, such as `/ark-space:exa-context <query>`.
7. Do not return Exa Context results until the provider check succeeds.

## Helper Script

Get code context:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py code context --provider exa "React hooks state management examples" --output markdown
```

Control token budget:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py code context --provider exa "Next.js app router auth middleware" --tokens 10000 --output json
```

## Routing Notes

- Prefer Exa Context for implementation questions, API syntax, library examples, framework setup, and repository-grounded coding patterns.
- Prefer local repository inspection when the answer is already in the current codebase.
- Prefer `exa-search` when the user wants candidate source URLs rather than ready-to-use code context.
