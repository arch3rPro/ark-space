import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "skills" / "prd-create" / "scripts" / "verify-prd-gates.js"
REQUIRED_GATES = [
    "Sources, meeting decisions, and conflict lists were read; conflicts were treated as questions until confirmed.",
    "Product access and evidence mode were recorded before drafting detailed behavior.",
    "Every module workflow record was completed before its detailed PRD section was written.",
    "Every detailed workflow uses explicit step headings with operation, page response, controls, R&D requirements, constraints, exceptions, and evidence status.",
    "Each workflow step has a browser screenshot captured from the accessible product or prototype; screenshots are not static design, desktop, meeting, or historical images.",
    "Observed UI, required behavior, unverified behavior, and decision-needed gaps are labeled instead of inferred.",
    "`node scripts/validate-prd-images.js <prd.md>` passed with no missing, duplicate, absolute, or empty links.",
    "`node scripts/verify-prd-gates.js <prd.md> <checklist.md>` passed.",
    "Review decisions were synchronized into the PRD, or no review decision was applicable.",
]
MODULE_GATES = [
    "Module workflow record is complete for the active module.",
    "Screenshots are captured for every active-module workflow step.",
    "The active module is written and checked before any next module begins.",
]



class PrdCreateGateTests(unittest.TestCase):
    def write_ready_fixture(self, root: Path, checked=True):
        assets = root / "assets"
        assets.mkdir()
        (assets / "screen.png").write_bytes(b"png")
        prd = root / "PRD.md"
        prd.write_text(
            """# PRD
## 7.2 User: Account


### Account Workflow Confirmation

| Item | Confirmed detail |
|---|---|
| Role | User |

### Account Main Workflow

#### Step 1: Open account

![account](assets/screen.png)

- Operation: Click Account.
- Page response: The account page opens.
- Controls: Account navigation item.
- R&D requirements: Load the current account.
- Constraints: Require an authenticated user.
- Exceptions: Show retry on failure.
- Evidence status: observed
""",
            encoding="utf-8",
        )
        marks = "x" if checked else " "
        checklist = root / "PRD_EXECUTION_CHECKLIST.md"
        checklist.write_text(
            "- Evidence mode: `demo-staging`\n"
            "- Active module: `none`\n"
            "- Decision checklist: `none`\n"
            "- Blocking decisions: `none`\n"
            "- Product access authorized: `yes`\n\n"
            + "| Module | Role | Included scope | Excluded scope | Entry points | Main workflow confirmed | Data result | Open questions status | Confirmation source |\n"
            + "|---|---|---|---|---|---|---|---|---|\n"
            + "| Account | User | Account | None | Navigation | Yes | Account view | confirmed | user |\n\n"
            + "\n".join(f"- [{marks}] {gate}" for gate in REQUIRED_GATES)
            + "\n",
            encoding="utf-8",
        )
        return prd, checklist

    def run_verifier(self, prd: Path, checklist: Path, module=None):
        command = ["node", str(VERIFIER), str(prd), str(checklist)]
        if module:
            command.extend(["--module", module])
        return subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_ready_prd_passes_all_gates(self):
        with tempfile.TemporaryDirectory() as directory:
            prd, checklist = self.write_ready_fixture(Path(directory))
            result = self.run_verifier(prd, checklist)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["ready"], True)

    def test_unchecked_gate_blocks_readiness(self):
        with tempfile.TemporaryDirectory() as directory:
            prd, checklist = self.write_ready_fixture(Path(directory), checked=False)
            result = self.run_verifier(prd, checklist)

        self.assertEqual(result.returncode, 1)
        self.assertIn("unchecked completion gate", result.stderr)
    def test_summary_only_step_blocks_readiness(self):
        with tempfile.TemporaryDirectory() as directory:
            prd, checklist = self.write_ready_fixture(Path(directory))
            prd.write_text(
                prd.read_text(encoding="utf-8").replace(
                    "- Controls: Account navigation item.\n", ""
                ),
                encoding="utf-8",
            )
            result = self.run_verifier(prd, checklist)

        self.assertEqual(result.returncode, 1)
        self.assertIn("missing 'Controls'", result.stderr)

    def test_active_module_must_pass_before_advancing(self):
        with tempfile.TemporaryDirectory() as directory:
            prd, checklist = self.write_ready_fixture(Path(directory))
            checklist.write_text(
                checklist.read_text(encoding="utf-8")
                .replace("- Active module: `none`", "- Active module: `Account`")
                .replace(
                    "\n".join(f"- [x] {gate}" for gate in REQUIRED_GATES),
                    "\n".join(f"- [x] {gate}" for gate in MODULE_GATES),
                ),
                encoding="utf-8",
            )
            result = self.run_verifier(prd, checklist, module="Account")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["moduleVerified"], "Account")

    def test_active_module_blocks_final_readiness(self):
        with tempfile.TemporaryDirectory() as directory:
            prd, checklist = self.write_ready_fixture(Path(directory))
            checklist.write_text(
                checklist.read_text(encoding="utf-8").replace(
                    "- Active module: `none`", "- Active module: `Account`"
                ),
                encoding="utf-8",
            )
            result = self.run_verifier(prd, checklist)

        self.assertEqual(result.returncode, 1)
        self.assertIn("final readiness requires", result.stderr)
    def test_blocking_decision_in_checklist_blocks_access(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prd, checklist = self.write_ready_fixture(root)
            (root / "decisions.md").write_text(
                """## Product Decisions

| ID | Decision | Recommended default | Options | Blocking module | Status | Confirmed by | Synced to PRD |
|---|---|---|---|---|---|---|---|
| D-01 | Registration policy | Defer | A / B | Account | blocking |  | No |
""",
                encoding="utf-8",
            )
            checklist.write_text(
                checklist.read_text(encoding="utf-8").replace(
                    "- Decision checklist: `none`",
                    "- Decision checklist: `decisions.md`",
                ),
                encoding="utf-8",
            )
            result = self.run_verifier(prd, checklist)

        self.assertEqual(result.returncode, 1)
        self.assertIn("decision checklist contains blocking decisions: D-01", result.stderr)

    def test_unconfirmed_active_module_workflow_blocks_module_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            prd, checklist = self.write_ready_fixture(Path(directory))
            checklist.write_text(
                checklist.read_text(encoding="utf-8")
                .replace("- Active module: `none`", "- Active module: `Account`")
                .replace("| Account | User | Account | None | Navigation | Yes |", "| Account | User | Account | None | Navigation | No |")
                .replace(
                    "\n".join(f"- [x] {gate}" for gate in REQUIRED_GATES),
                    "\n".join(f"- [x] {gate}" for gate in MODULE_GATES),
                ),
                encoding="utf-8",
            )
            result = self.run_verifier(prd, checklist, module="Account")

        self.assertEqual(result.returncode, 1)
        self.assertIn("workflow is not confirmed", result.stderr)


    def test_unapproved_product_access_blocks_readiness(self):
        with tempfile.TemporaryDirectory() as directory:
            prd, checklist = self.write_ready_fixture(Path(directory))
            checklist.write_text(
                checklist.read_text(encoding="utf-8").replace(
                    "- Product access authorized: `yes`",
                    "- Product access authorized: `no`",
                ),
                encoding="utf-8",
            )
            result = self.run_verifier(prd, checklist)

        self.assertEqual(result.returncode, 1)
        self.assertIn("product access is not authorized", result.stderr)

    def test_requirements_only_draft_cannot_pass_readiness(self):
        with tempfile.TemporaryDirectory() as directory:
            prd, checklist = self.write_ready_fixture(Path(directory))
            checklist.write_text(
                checklist.read_text(encoding="utf-8").replace(
                    "`demo-staging`", "`requirements-only`"
                ),
                encoding="utf-8",
            )
            result = self.run_verifier(prd, checklist)

        self.assertEqual(result.returncode, 1)
        self.assertIn("requirements-only evidence", result.stderr)
        self.assertIn("requirements-only PRD must not reference screenshots", result.stderr)



if __name__ == "__main__":
    unittest.main()
