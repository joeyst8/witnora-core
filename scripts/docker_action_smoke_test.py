import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ACTION_DIR = REPO_ROOT / "dist" / "witnora-verify-action-docker"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def write_fixtures(root: Path) -> tuple[Path, Path, Path, Path]:
    artifacts = root / "test-artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    source_zip = artifacts / "source.zip"
    diagnostic_zip = artifacts / "diagnostic.zip"
    manifest = artifacts / "MANIFEST.md"
    out_dir = artifacts / "out"

    with zipfile.ZipFile(source_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("README.md", "source fixture\n")
    with zipfile.ZipFile(diagnostic_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps({"suite": "docker-smoke"}) + "\n")

    manifest.write_text(
        "\n".join(
            [
                "# Docker Smoke Manifest",
                "",
                "| asset | SHA256 | status |",
                "| --- | --- | --- |",
                f"| `source.zip` | `{sha256(source_zip)}` | source archive |",
                f"| `diagnostic.zip` | `{sha256(diagnostic_zip)}` | diagnostic artifact |",
                "",
                "This fixture does not claim parity support, broad XOR extraction, or P vs NP progress.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return artifacts, source_zip, diagnostic_zip, manifest


def run_command(argv: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def docker_unavailable_summary() -> dict[str, object]:
    return {
        "docker_available": False,
        "status": "DOCKER_NOT_AVAILABLE",
        "message": "Docker build/run smoke test was not executed.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a Docker smoke test for the Witnora Verify Docker action.")
    parser.add_argument("--action-dir", default=str(DEFAULT_ACTION_DIR))
    parser.add_argument("--image-tag", default="witnora-verify-action:smoke")
    parser.add_argument("--keep-workdir", action="store_true")
    args = parser.parse_args(argv)

    if os.environ.get("WITNORA_FORCE_DOCKER_UNAVAILABLE") == "1" or shutil.which("docker") is None:
        print(json.dumps(docker_unavailable_summary(), indent=2, sort_keys=True))
        return 0

    action_dir = Path(args.action_dir).resolve()
    with tempfile.TemporaryDirectory() as temp_name:
        temp_root = Path(temp_name)
        artifacts, source_zip, diagnostic_zip, manifest = write_fixtures(temp_root)
        # Run the actual docker build / docker run smoke path when Docker is available.
        build = run_command(["docker", "build", "-t", args.image_tag, "."], cwd=action_dir)
        if build.returncode != 0:
            print(
                json.dumps(
                    {
                        "docker_available": True,
                        "build_status": "FAIL",
                        "run_status": "NOT_RUN",
                        "stdout": build.stdout[-2000:],
                        "stderr": build.stderr[-2000:],
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return build.returncode

        volume = f"{artifacts.resolve()}:/work/test-artifacts"
        run = run_command(
            [
                "docker",
                "run",
                "--rm",
                "-v",
                volume,
                "-e",
                "INPUT_SOURCE_ZIP=/work/test-artifacts/source.zip",
                "-e",
                "INPUT_DIAGNOSTIC_ZIP=/work/test-artifacts/diagnostic.zip",
                "-e",
                "INPUT_MANIFEST=/work/test-artifacts/MANIFEST.md",
                "-e",
                "INPUT_DEPTH=metadata",
                "-e",
                "INPUT_OUT_DIR=/work/test-artifacts/out",
                args.image_tag,
            ]
        )
        report_path = artifacts / "out" / "release_verification_report.json"
        verdict = None
        if report_path.is_file():
            verdict = json.loads(report_path.read_text(encoding="utf-8")).get("verdict")
        ok = run.returncode == 0 and verdict == "ARTIFACT_INTEGRITY_VERIFIED"
        summary = {
            "docker_available": True,
            "build_status": "PASS",
            "run_status": "PASS" if ok else "FAIL",
            "verdict": verdict,
            "report_path": str(report_path),
            "stdout_tail": run.stdout[-2000:],
            "stderr_tail": run.stderr[-2000:],
        }
        print(json.dumps(summary, indent=2, sort_keys=True))
        if args.keep_workdir:
            print(f"workdir={temp_root}")
        return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
