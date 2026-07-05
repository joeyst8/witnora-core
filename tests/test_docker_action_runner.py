from pathlib import Path
import json
import os
import re
import subprocess
import sys
import unittest


COMPOSITE_DIST = Path("dist/witnora-verify-action")
DOCKER_DIST = Path("dist/witnora-verify-action-docker")


def _action_input_names(path: Path) -> set[str]:
    names: set[str] = set()
    in_inputs = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line == "inputs:":
            in_inputs = True
            continue
        if line == "outputs:":
            break
        if in_inputs:
            match = re.match(r"^  ([A-Za-z0-9_-]+):$", line)
            if match:
                names.add(match.group(1))
    return names


class DockerActionRunnerTest(unittest.TestCase):
    def test_docker_action_metadata(self):
        action = DOCKER_DIST / "action.yml"
        self.assertTrue(action.is_file())
        text = action.read_text(encoding="utf-8")
        self.assertIn("name: Witnora Verify Docker", text)
        self.assertIn("branding:", text)
        self.assertIn("inputs:", text)
        self.assertIn("outputs:", text)
        self.assertIn("using: docker", text)
        self.assertIn("image: Dockerfile", text)
        print("DOCKER_ACTION_METADATA_PASS")

    def test_dockerfile_present(self):
        dockerfile = DOCKER_DIST / "Dockerfile"
        self.assertTrue(dockerfile.is_file())
        text = dockerfile.read_text(encoding="utf-8")
        self.assertIn("FROM python:3.11-slim", text)
        self.assertIn("ARG WITNORA_CORE_REF=v1.7-docker-action-runner", text)
        self.assertIn("git+https://github.com/joeyst8/witnora-core.git@${WITNORA_CORE_REF}", text)
        self.assertIn("ENTRYPOINT", text)
        self.assertNotIn("pip install witnora-core", text)
        print("DOCKERFILE_PRESENT_PASS")

    def test_dockerfile_version_pin_aligned(self):
        dockerfile = (DOCKER_DIST / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("ARG WITNORA_CORE_REF=v1.7-docker-action-runner", dockerfile)
        readme = (DOCKER_DIST / "README.md").read_text(encoding="utf-8")
        self.assertIn("default ref is `v1.7-docker-action-runner`", readme)
        self.assertIn("--build-arg WITNORA_CORE_REF=<tag>", readme)
        print("DOCKERFILE_VERSION_PIN_ALIGNED_PASS")

    def test_docker_self_test_workflow_build_run(self):
        workflow = (DOCKER_DIST / ".github" / "workflows" / "self-test.yml").read_text(encoding="utf-8")
        self.assertIn("docker-build-run-test", workflow)
        self.assertIn("docker build -t witnora-verify-action:test .", workflow)
        self.assertIn("docker run --rm", workflow)
        self.assertIn("test-artifacts/source.zip", workflow)
        self.assertIn("test-artifacts/diagnostic.zip", workflow)
        self.assertIn("ARTIFACT_INTEGRITY_VERIFIED", workflow)
        print("DOCKER_SELF_TEST_WORKFLOW_BUILD_RUN_PASS")

    def test_docker_smoke_script_present(self):
        script = Path("scripts/docker_action_smoke_test.py")
        self.assertTrue(script.is_file())
        text = script.read_text(encoding="utf-8")
        self.assertIn("DOCKER_NOT_AVAILABLE", text)
        self.assertIn("docker build", text)
        self.assertIn("ARTIFACT_INTEGRITY_VERIFIED", text)
        print("DOCKER_SMOKE_SCRIPT_PRESENT_PASS")

    def test_docker_smoke_unavailable_report(self):
        env = dict(os.environ)
        env["WITNORA_FORCE_DOCKER_UNAVAILABLE"] = "1"
        result = subprocess.run(
            [sys.executable, "scripts/docker_action_smoke_test.py"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads(result.stdout)
        self.assertFalse(summary["docker_available"])
        self.assertEqual(summary["status"], "DOCKER_NOT_AVAILABLE")
        self.assertIn("not executed", summary["message"])
        print("DOCKER_SMOKE_UNAVAILABLE_REPORT_PASS")

    def test_docker_action_readme_scope(self):
        readme = (DOCKER_DIST / "README.md").read_text(encoding="utf-8")
        for phrase in [
            "does not rerun the solver",
            "does not regenerate benchmark instances",
            "does not regenerate DRAT proofs",
            "does not replace human review",
            "Composite vs Docker",
            "does not claim a PyPI package exists",
        ]:
            self.assertIn(phrase, readme)
        print("DOCKER_ACTION_README_SCOPE_PASS")

    def test_docker_action_composite_tradeoff_doc(self):
        docs = "\n".join(
            [
                (DOCKER_DIST / "README.md").read_text(encoding="utf-8"),
                Path("docs/GITHUB_ACTION_INTEGRATION.md").read_text(encoding="utf-8"),
                Path("docs/PRODUCT_WEDGE.md").read_text(encoding="utf-8"),
            ]
        )
        self.assertIn("Composite action", docs)
        self.assertIn("Docker action", docs)
        self.assertIn("requires Python and Witnora-Core", docs)
        self.assertIn("requires a Docker-capable runner", docs)
        print("DOCKER_ACTION_COMPOSITE_TRADEOFF_DOC_PASS")

    def test_docker_action_external_release_warning(self):
        docs = "\n".join(
            [
                (DOCKER_DIST / "README.md").read_text(encoding="utf-8"),
                Path("docs/GITHUB_ACTION_INTEGRATION.md").read_text(encoding="utf-8"),
                Path("docs/PRODUCT_WEDGE.md").read_text(encoding="utf-8"),
            ]
        )
        self.assertIn("should not be treated as externally validated", docs)
        self.assertIn("Docker build/run self-test passes", docs)
        print("DOCKER_ACTION_EXTERNAL_RELEASE_WARNING_PASS")

    def test_docker_action_input_parity(self):
        composite_inputs = _action_input_names(COMPOSITE_DIST / "action.yml")
        docker_inputs = _action_input_names(DOCKER_DIST / "action.yml")
        self.assertEqual(composite_inputs, docker_inputs)
        print("DOCKER_ACTION_INPUT_PARITY_PASS")

    def test_docker_action_no_solver_logic_change(self):
        package_text = "\n".join(
            path.read_text(encoding="utf-8", errors="replace")
            for path in DOCKER_DIST.rglob("*")
            if path.is_file()
        )
        self.assertNotIn("from witnora_core.runner", package_text)
        self.assertNotIn("import witnora_core.runner", package_text)
        self.assertNotIn("solve_formula", package_text)
        print("DOCKER_ACTION_NO_SOLVER_LOGIC_CHANGE_PASS")


if __name__ == "__main__":
    unittest.main()
