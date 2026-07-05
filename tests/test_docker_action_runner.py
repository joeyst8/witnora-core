from pathlib import Path
import re
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
        self.assertIn("ARG WITNORA_CORE_REF=v1.6-marketplace-action-repo-package", text)
        self.assertIn("git+https://github.com/joeyst8/witnora-core.git@${WITNORA_CORE_REF}", text)
        self.assertIn("ENTRYPOINT", text)
        self.assertNotIn("pip install witnora-core", text)
        print("DOCKERFILE_PRESENT_PASS")

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
