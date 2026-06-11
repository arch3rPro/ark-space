import argparse
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_arxiv_module():
    spec = importlib.util.spec_from_file_location(
        "arxiv_search_test_module",
        ROOT / "skills" / "arxiv-search" / "scripts" / "arxiv_search.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ArxivHelperTests(unittest.TestCase):
    def setUp(self):
        self.arxiv = load_arxiv_module()

    def test_check_config_requires_no_secret(self):
        result = self.arxiv.check_config()

        self.assertTrue(result["ok"])
        self.assertEqual(result["provider"], "arxiv")
        self.assertEqual(result["capability"], "web_search")
        self.assertFalse(result["configRequired"])

    def test_build_url_supports_field_filters(self):
        args = argparse.Namespace(
            query="diffusion transformers",
            title=None,
            author="William Peebles",
            abstract=None,
            category="cs.CV",
            id_list=None,
            start=0,
            max_results=3,
            sort_by="submittedDate",
            sort_order="descending",
        )

        url = self.arxiv.build_url(args)

        self.assertIn("search_query=all%3A%22diffusion+transformers%22+AND+au%3A%22William+Peebles%22+AND+cat%3Acs.CV", url)
        self.assertIn("max_results=3", url)
        self.assertIn("sortBy=submittedDate", url)

    def test_parse_feed_extracts_paper_metadata(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <opensearch:totalResults>1</opensearch:totalResults>
  <entry>
    <id>http://arxiv.org/abs/1706.03762v7</id>
    <updated>2023-08-02T00:00:00Z</updated>
    <published>2017-06-12T17:57:34Z</published>
    <title>Attention Is All You Need</title>
    <summary>Transformer architecture.</summary>
    <author><name>Ashish Vaswani</name></author>
    <arxiv:primary_category term="cs.CL" />
    <category term="cs.CL" />
    <link href="http://arxiv.org/abs/1706.03762v7" rel="alternate" type="text/html" />
    <link title="pdf" href="http://arxiv.org/pdf/1706.03762v7" rel="related" type="application/pdf" />
  </entry>
</feed>
"""

        parsed = self.arxiv.parse_feed(xml)

        self.assertEqual(parsed["totalResults"], "1")
        self.assertEqual(parsed["results"][0]["id"], "1706.03762v7")
        self.assertEqual(parsed["results"][0]["title"], "Attention Is All You Need")
        self.assertEqual(parsed["results"][0]["authors"], ["Ashish Vaswani"])
        self.assertEqual(parsed["results"][0]["primary_category"], "cs.CL")
        self.assertEqual(parsed["results"][0]["pdf_url"], "http://arxiv.org/pdf/1706.03762v7")

    def test_markdown_output_contains_paper_links(self):
        markdown = self.arxiv.format_markdown(
            {
                "query": "all:transformers",
                "id_list": None,
                "results": [
                    {
                        "id": "1706.03762v7",
                        "title": "Attention Is All You Need",
                        "authors": ["Ashish Vaswani"],
                        "published": "2017-06-12T17:57:34Z",
                        "primary_category": "cs.CL",
                        "abs_url": "http://arxiv.org/abs/1706.03762v7",
                        "pdf_url": "http://arxiv.org/pdf/1706.03762v7",
                        "summary": "Transformer architecture.",
                    }
                ],
            }
        )

        self.assertIn("# arXiv Search: all:transformers", markdown)
        self.assertIn("Attention Is All You Need", markdown)
        self.assertIn("http://arxiv.org/pdf/1706.03762v7", markdown)


if __name__ == "__main__":
    unittest.main()
