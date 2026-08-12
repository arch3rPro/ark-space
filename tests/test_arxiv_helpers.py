import argparse
import contextlib
import email.message
import importlib.util
import io
import json
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


VALID_FEED = """<?xml version="1.0" encoding="UTF-8"?>
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
    <link href="http://arxiv.org/abs/1706.03762v7" rel="alternate" type="text/html" />
  </entry>
</feed>
"""


class _FakeResponse:
    def __init__(self, body: bytes):
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return self._body


def load_arxiv_module():
    spec = importlib.util.spec_from_file_location(
        "arxiv_search_test_module",
        ROOT / "skills" / "web-search" / "scripts" / "arxiv_search.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load arxiv_search module")
    module = importlib.util.module_from_spec(spec)
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

    def _run_main(self, argv, urlopen):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.object(self.arxiv.urllib.request, "urlopen", urlopen):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                rc = self.arxiv.main(argv)
        return rc, stdout.getvalue(), stderr.getvalue()

    def test_main_success_json_shape_unchanged(self):
        os.environ["ARKSPACE_ERROR_FILE"] = str(Path(tempfile.mkdtemp()) / "err.json")
        self.addCleanup(os.environ.pop, "ARKSPACE_ERROR_FILE", None)

        rc, out, err = self._run_main(
            ["transformers", "--output", "json"],
            lambda *a, **k: _FakeResponse(VALID_FEED.encode("utf-8")),
        )

        self.assertEqual(rc, 0)
        self.assertEqual(err, "")
        data = json.loads(out)
        self.assertIn("results", data)
        self.assertIn("totalResults", data)
        self.assertEqual(data["results"][0]["title"], "Attention Is All You Need")
        self.assertNotIn("ok", data)  # results are not wrapped in an envelope

    def test_main_success_markdown_shape_unchanged(self):
        rc, out, err = self._run_main(
            ["transformers", "--output", "markdown"],
            lambda *a, **k: _FakeResponse(VALID_FEED.encode("utf-8")),
        )

        self.assertEqual(rc, 0)
        self.assertIn("# arXiv Search:", out)
        self.assertIn("Attention Is All You Need", out)
        self.assertNotIn("ok", out)

    def test_main_http_429_writes_quota_error_record(self):
        errfile = str(Path(tempfile.mkdtemp()) / "err.json")
        os.environ["ARKSPACE_ERROR_FILE"] = errfile
        self.addCleanup(os.environ.pop, "ARKSPACE_ERROR_FILE", None)

        def raise_429(*a, **k):
            raise urllib.error.HTTPError(
                "http://x", 429, "Too Many Requests", email.message.Message(), None
            )

        rc, _out, err = self._run_main(["transformers"], raise_429)

        self.assertEqual(rc, 1)
        self.assertIn("arxiv search failed", err)
        record = json.loads(Path(errfile).read_text(encoding="utf-8"))
        self.assertEqual(record["version"], 1)
        self.assertEqual(record["provider"], "arxiv")
        self.assertEqual(record["capability"], "web_search")
        self.assertEqual(record["kind"], "quota")
        self.assertEqual(record["status"], 429)

    def test_main_connection_failure_writes_network_error_record(self):
        errfile = str(Path(tempfile.mkdtemp()) / "err.json")
        os.environ["ARKSPACE_ERROR_FILE"] = errfile
        self.addCleanup(os.environ.pop, "ARKSPACE_ERROR_FILE", None)

        def raise_conn(*a, **k):
            raise urllib.error.URLError("connection refused")

        rc, _out, err = self._run_main(["transformers"], raise_conn)

        self.assertEqual(rc, 1)
        self.assertIn("arxiv search failed", err)
        record = json.loads(Path(errfile).read_text(encoding="utf-8"))
        self.assertEqual(record["kind"], "network")
        self.assertNotIn("status", record)

    def test_main_malformed_xml_writes_invalid_response_error_record(self):
        errfile = str(Path(tempfile.mkdtemp()) / "err.json")
        os.environ["ARKSPACE_ERROR_FILE"] = errfile
        self.addCleanup(os.environ.pop, "ARKSPACE_ERROR_FILE", None)

        rc, _out, err = self._run_main(
            ["transformers"], lambda *a, **k: _FakeResponse(b"<not xml")
        )

        self.assertEqual(rc, 1)
        self.assertIn("arxiv search failed", err)
        record = json.loads(Path(errfile).read_text(encoding="utf-8"))
        self.assertEqual(record["kind"], "invalid-response")

    def test_main_without_error_file_preserves_stderr_and_exit(self):
        os.environ.pop("ARKSPACE_ERROR_FILE", None)

        def raise_conn(*a, **k):
            raise urllib.error.URLError("connection refused")

        rc, _out, err = self._run_main(["transformers"], raise_conn)

        self.assertEqual(rc, 1)
        self.assertIn("arxiv search failed", err)


if __name__ == "__main__":
    unittest.main()
