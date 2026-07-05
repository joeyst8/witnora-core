import unittest
from pathlib import Path


class MarketplaceActionPackageTest(unittest.TestCase):
    def test_marketplace_action_root_metadata(self):
        action = Path("marketplace-action/action.yml")
        self.assertTrue(action.is_file())
        text = action.read_text(encoding="utf-8")
        for required in [
            "name: Witnora Verify",
            "description: Scoped artifact verification",
            "author:",
            "branding:",
            "source-zip:",
            "diagnostic-zip:",
            "manifest:",
            "fail-on-risk-flags:",
            "fail-on-verdict:",
            "report_path:",
            "trust_card_path:",
            "python -m witnora_core.ci",
        ]:
            self.assertIn(required, text)
        print("MARKETPLACE_ACTION_ROOT_METADATA_PASS")

    def test_marketplace_readme_scope(self):
        text = Path("marketplace-action/README.md").read_text(encoding="utf-8")
        self.assertIn("does not rerun the solver", text)
        self.assertIn("does not regenerate CNFgen instances", text)
        self.assertIn("does not regenerate DRAT proofs", text)
        self.assertIn("does not rerun the full benchmark diagnostic", text)
        print("MARKETPLACE_README_SCOPE_PASS")

    def test_marketplace_risk_flag_table(self):
        text = Path("marketplace-action/README.md").read_text(encoding="utf-8")
        for flag in [
            "METADATA_ONLY",
            "DRAT_TRIM_NOT_RERUN",
            "INDEPENDENT_CHECKER_NOT_RERUN",
            "CLAIM_SCAN_HEURISTIC_ONLY",
            "PROOF_SELECTION_LIMITED",
            "PROOF_SELECTION_NONE",
            "PROOF_FILE_MISSING",
            "DRAT_TRIM_TIMEOUT",
            "ACTION_INPUT_MISMATCH",
            "CHECKER_VERSION_NOT_RECORDED",
            "UNVERIFIED_CLAIM",
            "HASH_MISMATCH",
            "MISSING_FILE",
            "REPORT_ARTIFACT_NOT_UPLOADED",
            "GITHUB_CLI_NOT_AVAILABLE",
        ]:
            self.assertIn(flag, text)
        print("MARKETPLACE_RISK_FLAG_TABLE_PASS")

    def test_selection_policy_doc(self):
        combined = (
            Path("docs/GITHUB_ACTION_INTEGRATION.md").read_text(encoding="utf-8")
            + Path("marketplace-action/README.md").read_text(encoding="utf-8")
        )
        for policy in ["largest", "first", "all", "instance"]:
            self.assertIn(policy, combined)
        self.assertIn("proof size", combined)
        self.assertIn("PROOF_SELECTION_LIMITED", combined)
        print("SELECTION_POLICY_DOC_PASS")

    def test_fail_policy_doc(self):
        combined = (
            Path("docs/GITHUB_ACTION_INTEGRATION.md").read_text(encoding="utf-8")
            + Path("marketplace-action/README.md").read_text(encoding="utf-8")
        )
        for phrase in [
            "Strict artifact integrity",
            "Require partial replay",
            "Require drat-trim rerun",
            "Require no limited proof selection",
            "HASH_MISMATCH,MISSING_FILE,ACTION_INPUT_MISMATCH,UNVERIFIED_CLAIM",
            "DRAT_TRIM_NOT_RERUN,DRAT_TRIM_TIMEOUT",
            "PROOF_SELECTION_LIMITED,PROOF_SELECTION_NONE",
        ]:
            self.assertIn(phrase, combined)
        print("FAIL_POLICY_DOC_PASS")

    def test_marketplace_package_no_solver_logic_change(self):
        marketplace_files = [
            "marketplace-action/action.yml",
            "marketplace-action/README.md",
            "scripts/attach_release_trust_card.py",
        ]
        combined = "\n".join(Path(path).read_text(encoding="utf-8") for path in marketplace_files)
        self.assertNotIn("from witnora_core.runner", combined)
        self.assertNotIn("import witnora_core.runner", combined)
        self.assertNotIn("solve_formula", combined)
        print("MARKETPLACE_PACKAGE_NO_SOLVER_LOGIC_CHANGE_PASS")


if __name__ == "__main__":
    unittest.main()
