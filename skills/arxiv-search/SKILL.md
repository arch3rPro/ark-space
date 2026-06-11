---
name: arxiv-search
description: Use when searching arXiv papers by keyword, title, author, abstract, category, or arXiv ID through ArkSpace web_search routing.
---

# arXiv Search

Use arXiv as a no-key `web_search` provider for academic paper discovery when the user asks for papers, preprints, arXiv IDs, authors, categories such as `cs.AI`, or literature candidates.

This skill queries the official arXiv public API and returns candidate paper metadata, abstracts, authors, categories, abstract URLs, and PDF URLs. Use a fetch or paper-reading workflow after search when the answer needs detailed synthesis from selected papers.

## Source References

- arXiv: `https://arxiv.org/`
- Official arXiv API: `https://info.arxiv.org/help/api/index.html`
- Official arXiv API user manual: `https://info.arxiv.org/help/api/user-manual.html`
- Hermes Agent reference: `https://hermes-agent.nousresearch.com/docs/user-guide/skills/bundled/research/research-arxiv`

## Before Use

Resolve the installed ArkSpace package root before running commands. Replace `<installed-arkspace-path>` with the directory two levels above this loaded `SKILL.md`, such as `/Users/<user>/.claude/plugins/cache/ark-space/ark-space/0.1.2`. Use the installed package path, not a repository-relative command.

Check readiness:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py provider check arxiv --capability web_search
```

arXiv search does not require provider setup or an API key.

## Helper Script

Basic paper search:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py web search --provider arxiv "diffusion transformers" --max-results 5 --output json
```

Search by author and category:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py web search --provider arxiv "language agents" \
  --author "Yoshua Bengio" \
  --category cs.AI \
  --max-results 5 \
  --output markdown
```

Search by title:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py web search --provider arxiv "" \
  --title "attention is all you need" \
  --max-results 3 \
  --output json
```

Fetch specific IDs:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py web search --provider arxiv "" \
  --id-list 1706.03762,2402.03268 \
  --output json
```

Use arXiv field syntax directly when needed:

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py web search --provider arxiv "ti:\"retrieval augmented generation\" AND cat:cs.CL" --max-results 10
```

## Routing Notes

- Prefer arXiv when the task is academic preprint discovery, literature scouting, paper metadata lookup, or arXiv category search.
- Prefer `exa-search` when the task mixes papers with broader web sources, repositories, technical docs, or semantic discovery outside arXiv.
- Prefer `tavily-research` or `exa-answer` when the user asks for a synthesized research report rather than a paper candidate list.
- Respect arXiv API pacing for repeated paged requests; keep at least three seconds between repeated API calls.
- Acknowledge arXiv data usage when publishing products or reports that materially depend on arXiv API output.
