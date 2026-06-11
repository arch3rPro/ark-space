#!/usr/bin/env python3
"""arXiv web_search provider helper for ArkSpace."""

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


API_URL = "https://export.arxiv.org/api/query"
USER_AGENT = "ArkSpace-arxiv-search/0.1"
ATOM_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
    "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
}
FIELD_PREFIX_RE = re.compile(r"\b(all|ti|au|abs|cat|co|jr|id):", re.IGNORECASE)


def check_config():
    return {
        "ok": True,
        "provider": "arxiv",
        "capability": "web_search",
        "base_url": API_URL,
        "configRequired": False,
        "auth": "none",
    }


def field_query(prefix, value):
    if value is None:
        return None
    value = " ".join(str(value).strip().split())
    if not value:
        return None
    if " " in value and not (value.startswith('"') and value.endswith('"')):
        value = f'"{value}"'
    return f"{prefix}:{value}"


def build_search_query(args):
    parts = []
    query = " ".join((args.query or "").strip().split())
    if query:
        parts.append(query if FIELD_PREFIX_RE.search(query) else field_query("all", query))
    for prefix, value in [
        ("ti", args.title),
        ("au", args.author),
        ("abs", args.abstract),
        ("cat", args.category),
    ]:
        built = field_query(prefix, value)
        if built:
            parts.append(built)
    return " AND ".join(parts)


def build_url(args):
    params = {
        "start": str(args.start),
        "max_results": str(args.max_results),
        "sortBy": args.sort_by,
        "sortOrder": args.sort_order,
    }
    search_query = build_search_query(args)
    if search_query:
        params["search_query"] = search_query
    if args.id_list:
        params["id_list"] = args.id_list
    if not params.get("search_query") and not params.get("id_list"):
        raise ValueError("arxiv search requires a query, field filter, or --id-list")
    return f"{API_URL}?{urllib.parse.urlencode(params)}"


def text_or_none(node, path):
    found = node.find(path, ATOM_NS)
    if found is None or found.text is None:
        return None
    return " ".join(found.text.split())


def parse_entry(entry):
    entry_id = text_or_none(entry, "atom:id") or ""
    arxiv_id = entry_id.rstrip("/").split("/")[-1] if entry_id else ""
    links = {}
    for link in entry.findall("atom:link", ATOM_NS):
        href = link.attrib.get("href")
        if not href:
            continue
        rel = link.attrib.get("rel") or "alternate"
        title = link.attrib.get("title")
        link_type = link.attrib.get("type")
        if title == "pdf" or link_type == "application/pdf":
            links["pdf_url"] = href
        elif rel == "alternate":
            links["abs_url"] = href

    categories = [cat.attrib.get("term") for cat in entry.findall("atom:category", ATOM_NS) if cat.attrib.get("term")]
    primary = entry.find("arxiv:primary_category", ATOM_NS)

    return {
        "id": arxiv_id,
        "title": text_or_none(entry, "atom:title"),
        "authors": [text_or_none(author, "atom:name") for author in entry.findall("atom:author", ATOM_NS) if text_or_none(author, "atom:name")],
        "published": text_or_none(entry, "atom:published"),
        "updated": text_or_none(entry, "atom:updated"),
        "summary": text_or_none(entry, "atom:summary"),
        "primary_category": primary.attrib.get("term") if primary is not None else (categories[0] if categories else None),
        "categories": categories,
        "abs_url": links.get("abs_url") or entry_id or None,
        "pdf_url": links.get("pdf_url"),
        "doi": text_or_none(entry, "arxiv:doi"),
        "journal_ref": text_or_none(entry, "arxiv:journal_ref"),
        "comment": text_or_none(entry, "arxiv:comment"),
    }


def parse_feed(xml_text):
    root = ET.fromstring(xml_text)
    total = text_or_none(root, "opensearch:totalResults")
    entries = [parse_entry(entry) for entry in root.findall("atom:entry", ATOM_NS)]
    return {"results": entries, "totalResults": total}


def fetch(args):
    url = build_url(args)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=args.timeout) as response:
        body = response.read().decode("utf-8")
    parsed = parse_feed(body)
    parsed.update(
        {
            "provider": "arxiv",
            "capability": "web_search",
            "query": build_search_query(args),
            "id_list": args.id_list,
            "start": args.start,
            "max_results": args.max_results,
            "sort_by": args.sort_by,
            "sort_order": args.sort_order,
            "request_url": url if args.raw else None,
        }
    )
    if not args.raw:
        parsed.pop("request_url", None)
    return parsed


def format_markdown(data):
    lines = [f"# arXiv Search: {data.get('query') or data.get('id_list')}", ""]
    if not data["results"]:
        return "\n".join([*lines, "No arXiv results found."])
    for index, item in enumerate(data["results"], start=1):
        lines.append(f"## {index}. {item.get('title') or item.get('id')}")
        if item.get("authors"):
            lines.append(f"- Authors: {', '.join(item['authors'])}")
        if item.get("published"):
            lines.append(f"- Published: {item['published']}")
        if item.get("primary_category"):
            lines.append(f"- Category: {item['primary_category']}")
        if item.get("abs_url"):
            lines.append(f"- Abstract: {item['abs_url']}")
        if item.get("pdf_url"):
            lines.append(f"- PDF: {item['pdf_url']}")
        if item.get("summary"):
            lines.append("")
            lines.append(item["summary"])
        lines.append("")
    return "\n".join(lines).rstrip()


def build_parser():
    parser = argparse.ArgumentParser(description="Search arXiv through the official public API.")
    parser.add_argument("query", nargs="?", help="Search query. Plain text defaults to all:<query>.")
    parser.add_argument("--id-list", help="Comma-separated arXiv IDs, with or without versions.")
    parser.add_argument("--title", help="Title field filter.")
    parser.add_argument("--author", help="Author field filter.")
    parser.add_argument("--abstract", help="Abstract field filter.")
    parser.add_argument("--category", help="arXiv category filter, such as cs.AI or stat.ML.")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--sort-by", choices=["relevance", "lastUpdatedDate", "submittedDate"], default="relevance")
    parser.add_argument("--sort-order", choices=["ascending", "descending"], default="descending")
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--output", choices=["json", "markdown"], default="json")
    parser.add_argument("--raw", action="store_true", help="Include request URL in JSON output.")
    parser.add_argument("--check", action="store_true")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.check:
        print(json.dumps(check_config(), ensure_ascii=False))
        return 0
    try:
        data = fetch(args)
    except Exception as exc:
        print(f"arxiv search failed: {exc}", file=sys.stderr)
        return 1
    if args.output == "markdown":
        print(format_markdown(data))
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
