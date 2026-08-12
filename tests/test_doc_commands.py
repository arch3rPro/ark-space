"""Documentation command-contract tests.

Every canonical ``python3 <installed-arkspace-path>/scripts/arkspace.py ...``
command shown in public skill docs must parse with the real ``build_parser``
argparse parser (no subprocesses are executed, so nothing runs). This keeps the
documented CLI surface in sync with the parser: a doc example that no longer
parses fails loudly, and a docs-only typo (e.g. ``--provider tavily`` on
``provider check`` or ``--limit`` instead of ``--max-results``) is caught.
"""

import importlib.util
import shlex
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DOC_SKILL_FILES = [
    ROOT / "skills" / "web-search" / "SKILL.md",
    ROOT / "skills" / "web-fetch" / "SKILL.md",
    ROOT / "skills" / "web-site" / "SKILL.md",
    ROOT / "skills" / "web-research" / "SKILL.md",
    ROOT / "skills" / "web-extract" / "SKILL.md",
    ROOT / "skills" / "web-automation" / "SKILL.md",
    ROOT / "skills" / "provider-manager" / "SKILL.md",
]


def load_arkspace():
    spec = importlib.util.spec_from_file_location(
        "arkspace_doc_contract_module", ROOT / "scripts" / "arkspace.py"
    )
    module = importlib.util.module_from_spec(spec)  # type: ignore[reportArgumentType]
    assert spec.loader is not None  # type: ignore[reportOptionalMemberAccess]
    spec.loader.exec_module(module)  # type: ignore[reportOptionalMemberAccess]
    return module


def _argv_without_prog(cmd):
    """Strip the leading ``python3 <scripts/arkspace.py>`` prefix from a command.

    argparse skips the program name only in the no-argument ``parse_args()``
    path; when an explicit argv is passed, the first token is treated as a
    positional. Every command here is documented as ``python3 .../arkspace.py
    <subcommand>``, so drop those two tokens so the parser sees the real CLI.
    """
    argv = shlex.split(cmd)
    if len(argv) >= 2 and argv[0] == "python3" and argv[1].endswith("arkspace.py"):
        return argv[2:]
    return argv


def extract_arkspace_commands(text):
    """Return canonical ``arkspace.py`` commands from bash fenced blocks."""
    commands = []
    in_block = False
    for line in text.splitlines():
        if line.strip() == "```bash":
            in_block = True
            continue
        if line.strip() == "```":
            in_block = False
            continue
        if not in_block:
            continue
        stripped = line.strip()
        if "scripts/arkspace.py" not in stripped:
            continue
        # Normalize the installed-path placeholder to the repo root and drop
        # any trailing shell output redirection so only the CLI stays.
        cmd = stripped.replace("<installed-arkspace-path>", str(ROOT))
        for marker in ("2>&1", "> /dev/null"):
            if marker in cmd:
                cmd = cmd.split(marker)[0].rstrip()
        commands.append(cmd)
    return commands


class DocCommandContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.arkspace = load_arkspace()
        cls.parser = cls.arkspace.build_parser()

    def _assert_parses(self, cmd):
        argv = _argv_without_prog(cmd)
        with self.subTest(command=cmd):
            try:
                self.parser.parse_args(argv)
            except SystemExit as exc:
                self.fail(f"documented command does not parse: {cmd} (exit {exc.code})")

    def test_all_documented_arkspace_commands_parse(self):
        any_extracted = False
        for path in DOC_SKILL_FILES:
            if not path.exists():
                continue
            for cmd in extract_arkspace_commands(path.read_text(encoding="utf-8")):
                any_extracted = True
                self._assert_parses(cmd)
        self.assertTrue(any_extracted, "no canonical arkspace.py commands were extracted")

    # -- regression: the two known-invalid SKILL commands must not parse ---------

    def test_provider_check_requires_positional_provider(self):
        with self.assertRaises(SystemExit):
            self.parser.parse_args(
                _argv_without_prog(
                    "python3 x/scripts/arkspace.py provider check --provider tavily --capability web_search"
                )
            )
        self._assert_parses("python3 x/scripts/arkspace.py provider check tavily --capability web_search")

    def test_web_search_uses_max_results_not_limit(self):
        with self.assertRaises(SystemExit):
            self.parser.parse_args(
                _argv_without_prog(
                    'python3 x/scripts/arkspace.py web search --provider searxng "q" --limit 5'
                )
            )
        self._assert_parses('python3 x/scripts/arkspace.py web search --provider searxng "q" --max-results 5')

    # -- canonical invocation forms ---------------------------------------------

    def test_provider_setup_wizard_parses_for_keyed_and_keyless(self):
        for provider in ("brave", "exa", "tavily", "firecrawl"):
            self._assert_parses(f"python3 x/scripts/arkspace.py provider setup {provider} --wizard")

    def test_web_search_single_provider_and_chain_parse(self):
        self._assert_parses(
            'python3 x/scripts/arkspace.py web search --provider exa-mcp "agent skills" --max-results 5 --output json'
        )
        self._assert_parses(
            'python3 x/scripts/arkspace.py web search --providers exa,brave,jina "agent frameworks" --max-results 5'
        )

    def test_web_search_default_provider_parses(self):
        self._assert_parses('python3 x/scripts/arkspace.py web search "agent frameworks"')


if __name__ == "__main__":
    unittest.main()
