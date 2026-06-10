---
name: tavily-research
description: Use when running Tavily Research for comprehensive multi-source research, cited reports, market analysis, comparisons, literature reviews, or deep investigation that needs synthesis instead of quick search snippets.
---

# Tavily Research

Use Tavily Research when ArkSpace needs Tavily to run a deeper research task and return a cited synthesized report.

Tavily configuration is shared with all Tavily skills through `provider-manager`.

## Source References

- Official docs: `https://docs.tavily.com/documentation/agent-skills`
- Create task API reference: `https://docs.tavily.com/documentation/api-reference/endpoint/research`
- Status API reference: `https://docs.tavily.com/documentation/api-reference/endpoint/research-get`
- Official skills: `https://github.com/tavily-ai/skills/tree/main/skills/tavily-research`

## Before Use

Resolve the installed ArkSpace package root before running commands. Replace `<installed-arkspace-path>` with the directory two levels above this loaded `SKILL.md`, such as `/Users/<user>/.claude/plugins/cache/ark-space/ark-space/0.1.2`. Use the installed package path, not a repository-relative command.

Check configuration:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider check tavily --capability deep_research
```

Configure Tavily once:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider setup tavily --wizard
```

## Missing Configuration Recovery

If the provider check reports a missing Tavily API key or missing Tavily capability:

1. Ask the user whether to start setup now: "Tavily is not configured. Should I start the ArkSpace setup wizard now?"
2. Present exactly two choices:
   - "Start setup wizard" - start interactive setup with `python3 <installed-arkspace-path>/scripts/arkspace.py provider setup tavily --wizard`.
   - "Not now" - leave Tavily unconfigured; if the user still wants results, ask whether to continue with a clearly labeled non-ArkSpace fallback.
3. Run the setup command for the user only when the host shell can provide interactive secret input. If the shell is non-interactive, do not run `--wizard` through that tool.
4. In Claude Code non-interactive tool sessions, tell the user the wizard needs interactive secret input and offer:
   - run `! python3 <installed-arkspace-path>/scripts/arkspace.py provider setup tavily --wizard` in the Claude prompt or terminal, or
   - paste the API key in chat and let the agent save it with `python3 <installed-arkspace-path>/scripts/arkspace.py provider setup tavily --save-secret TAVILY_API_KEY --secret-stdin`.
5. Re-run the provider check after setup.
6. If setup succeeds, rerun or tell the user to rerun the original invocation, such as `/ark-space:tavily-research <query>`.
7. Do not return Tavily Research results until the provider check succeeds.
8. If the user declines, defers, or cannot complete setup and still wants results, ask whether to continue with a clearly labeled non-ArkSpace fallback.

## Helper Script

Create a research task:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py research run --provider tavily "Compare Claude Code and Codex plugin ecosystems" --output json
```

Create and poll until complete:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py research run --provider tavily "AI coding agent market analysis" \
  --model pro \
  --wait \
  --timeout 600 \
  --output markdown
```

Check an async task:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py research status --provider tavily <request_id> --output json
```

## Routing Notes

- Use `tavily-search` for quick fact-finding and source discovery.
- Use `tavily-research` when the user asks for a detailed report, comparison, market analysis, or cited synthesis.
- Tell the user when a task is asynchronous and include the `request_id` for follow-up status checks.
