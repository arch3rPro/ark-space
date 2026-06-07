import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_installed_host_module():
    spec = importlib.util.spec_from_file_location(
        "installed_host_smoke_test_module",
        ROOT / "scripts" / "smoke-test-installed-host.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class InstalledHostSmokeTests(unittest.TestCase):
    def setUp(self):
        self.module = load_installed_host_module()
        self.tmpdir = tempfile.TemporaryDirectory()
        self.cache_root = Path(self.tmpdir.name) / "ark-space" / "ark-space"

    def tearDown(self):
        self.tmpdir.cleanup()

    def copy_codex_package_to_cache(self):
        installed_root = self.cache_root / "0.1.2"
        shutil.copytree(ROOT / "plugins" / "ark-space", installed_root)
        return installed_root

    def test_installed_host_passes_when_cache_matches_package_source(self):
        self.copy_codex_package_to_cache()

        self.assertEqual(self.module.check_installed_host("codex", self.cache_root), 0)

    def test_installed_host_fails_when_cache_is_stale(self):
        installed_root = self.copy_codex_package_to_cache()
        skill_path = installed_root / "skills" / "provider-manager" / "SKILL.md"
        skill_path.write_text(skill_path.read_text(encoding="utf-8") + "\nstale cache\n", encoding="utf-8")

        self.assertEqual(self.module.check_installed_host("codex", self.cache_root), 1)

    def test_installed_host_fails_when_cache_is_missing(self):
        self.assertEqual(self.module.check_installed_host("codex", self.cache_root), 1)


if __name__ == "__main__":
    unittest.main()
