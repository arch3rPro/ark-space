---
name: exa-answer
description: Use when answering a focused research question through Exa Answer with sources, especially concise cited synthesis, technical questions, or domain-constrained web answers.
---

# Exa Answer

Use Exa Answer as an API-backed `deep_research` provider for concise cited synthesis. This is not the same as a long research report; use Tavily Research when the user asks for a comprehensive report or extended market analysis.

Exa configuration is shared with all Exa skills through `provider-manager`.

## Source References

- Official Answer API: `https://exa.ai/docs/reference/answer`
- Official Search API: `https://exa.ai/docs/reference/search`

## Before Use

Resolve the installed ArkSpace package root before running commands. Replace `<installed-arkspace-path>` with the directory two levels above this loaded `SKILL.md`, such as `/Users/<user>/.claude/plugins/cache/ark-space/ark-space/0.1.2`. Use the installed package path, not a repository-relative command.

Check configuration:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider check exa --capability deep_research
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
6. If setup succeeds, rerun or tell the user to rerun the original invocation, such as `/ark-space:exa-answer <question>`.
7. Do not return Exa answer results until the provider check succeeds.

## Helper Script

Focused answer:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py research run --provider exa "What changed in AI coding assistants in 2025?" --output markdown
```

## Routing Notes

- Use Exa Answer for concise cited answers and semantic research questions.
- Use Exa Search first when the user wants source discovery rather than synthesis.
- Use Tavily Research when the user asks for a long-form report, broad market analysis, or comprehensive multi-source comparison.
