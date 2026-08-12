# arXiv provider reference

arXiv is a no-key `web_search` provider for academic paper discovery: papers, preprints, arXiv IDs, authors, categories such as `cs.AI`, or literature candidates. It queries the official arXiv public API and returns candidate paper metadata, abstracts, authors, categories, abstract URLs, and PDF URLs.

## Source references

- arXiv: `https://arxiv.org/`
- Official arXiv API: `https://info.arxiv.org/help/api/index.html`
- Official arXiv API user manual: `https://info.arxiv.org/help/api/user-manual.html`

## Search by author and category

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py web search --provider arxiv "language agents" \
  --author "Yoshua Bengio" \
  --category cs.AI \
  --max-results 5 \
  --output markdown
```

## Search by title

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py web search --provider arxiv "" \
  --title "attention is all you need" \
  --max-results 3 \
  --output json
```

## Fetch specific IDs

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py web search --provider arxiv "" \
  --id-list 1706.03762,2402.03268 \
  --output json
```

## Raw arXiv field syntax

```bash
python3 <installed-arkspace-path>/scripts/arkspace.py web search --provider arxiv "ti:\"retrieval augmented generation\" AND cat:cs.CL" --max-results 10
```

## Routing notes

- Prefer arXiv when the task is academic preprint discovery, literature scouting, paper metadata lookup, or arXiv category search.
- Prefer Exa when the task mixes papers with broader web sources, repositories, technical docs, or semantic discovery outside arXiv.
- Prefer `web-research` when the user asks for a synthesized research report rather than a paper candidate list.
- Respect arXiv API pacing for repeated paged requests; keep at least three seconds between repeated API calls.
- Acknowledge arXiv data usage when publishing products or reports that materially depend on arXiv API output.
