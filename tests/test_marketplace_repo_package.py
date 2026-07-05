import json
from pathlib import Path
import unittest


DIST = Path("dist/witnora-verify-action")


class MarketplaceRepoPackageTest(unittest.TestCase):
    def test_marketplace_dist_root_action_yml(self):
        action = DIST / "action.yml"
        self.assertTrue(action.is_file())
        text = action.read_text(encoding="utf-8")
        self.assertIn("name: Witnora Verify", text)
        self.assertIn("branding:", text)
        self.assertIn("inputs:", text)
        self.assertIn("outputs:", text)
        self.assertIn("python -m witnora_core.ci", text)
        print("MARKETPLACE_DIST_ROOT_ACTION_YML_PASS")

    def test_marketplace_dist_readme_scope(self):
        readme = (DIST / "README.md").read_text(encoding="utf-8")
        self.assertIn("What This Action Verifies", readme)
        self.assertIn("What This Action Does Not Verify", readme)
        self.assertIn("does not rerun the solver", readme)
        self.assertIn("does not regenerate benchmark instances", readme)
        self.assertIn("does not regenerate DRAT proofs", readme)
        self.assertIn("does not replace human review", readme)
        print("MARKETPLACE_DIST_README_SCOPE_PASS")

    def test_marketplace_dist_install_instructions(self):
        readme = (DIST / "README.md").read_text(encoding="utf-8")
        self.assertIn("pip install git+https://github.com/joeyst8/witnora-core.git@v1.5.1-release-trust-polish", readme)
        self.assertIn("WITNORA_CORE_NOT_INSTALLED", readme)
        self.assertIn("does not claim a PyPI package exists", readme)
        self.assertNotIn("pip install witnora-core", readme)
        print("MARKETPLACE_DIST_INSTALL_INSTRUCTIONS_PASS")

    def test_marketplace_dist_self_test_workflow(self):
        workflow = DIST / ".github" / "workflows" / "self-test.yml"
        self.assertTrue(workflow.is_file())
        text = workflow.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch", text)
        self.assertIn("actions/checkout", text)
        self.assertIn("actions/setup-python", text)
        self.assertIn("git+https://github.com/joeyst8/witnora-core.git@v1.5.1-release-trust-polish", text)
        self.assertNotIn("secrets.", text)
        print("MARKETPLACE_DIST_SELF_TEST_WORKFLOW_PASS")

    def test_marketplace_release_checklist(self):
        checklist = (DIST / "MARKETPLACE_RELEASE_CHECKLIST.md").read_text(encoding="utf-8")
        for phrase in [
            "public repo",
            "action.yml",
            "repository root",
            "Push tag `v1`",
            "Create a GitHub Release",
            "Marketplace publish prompt",
            "uses: joeyst8/witnora-verify-action@v1",
        ]:
            self.assertIn(phrase, checklist)
        print("MARKETPLACE_RELEASE_CHECKLIST_PASS")

    def test_marketplace_package_manifest(self):
        manifest_path = DIST / "ACTION_PACKAGE_MANIFEST.json"
        self.assertTrue(manifest_path.is_file())
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["package"], "witnora-verify-action")
        self.assertEqual(manifest["intended_repository"], "joeyst8/witnora-verify-action")
        files = {entry["path"]: entry for entry in manifest["files"]}
        self.assertIn("action.yml", files)
        self.assertIn("README.md", files)
        self.assertRegex(files["action.yml"]["sha256"], r"^[A-F0-9]{64}$")
        print("MARKETPLACE_PACKAGE_MANIFEST_PASS")

    def test_marketplace_dist_no_solver_logic_change(self):
        package_text = "\n".join(
            path.read_text(encoding="utf-8", errors="replace")
            for path in DIST.rglob("*")
            if path.is_file()
        )
        self.assertNotIn("from witnora_core.runner", package_text)
        self.assertNotIn("import witnora_core.runner", package_text)
        self.assertNotIn("solve_formula", package_text)
        print("MARKETPLACE_DIST_NO_SOLVER_LOGIC_CHANGE_PASS")


if __name__ == "__main__":
    unittest.main()
