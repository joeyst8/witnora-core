"""Reproduce the v2.12 paper/reproducibility package.

By default this script runs the full unit suite before regenerating the package.
Use --skip-tests only for fast local packaging checks.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from witnora_core.finite_edge_certificate import build_outputs as build_edge_delta_outputs
from witnora_core.finite_strictness_certificate import build_outputs as build_finite_strictness_outputs
from witnora_core.reproducibility_package import build_reproducibility_package, stable_json


def run_tests() -> dict[str, object]:
    command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
    proc = subprocess.run(command, capture_output=True, text=True, check=False)
    return {
        "command": " ".join(command),
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reproduce the v2.12 paper/reproducibility package")
    parser.add_argument("--out-root", default="outputs/v2.12-paper-reproducibility-package")
    parser.add_argument("--skip-tests", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--zip", default="witnora-core-v2.12-paper-reproducibility-package.zip")
    args = parser.parse_args(argv)

    test_result = {"skipped": True}
    if not args.skip_tests:
        test_result = run_tests()
        if test_result["returncode"] != 0:
            print(stable_json({"test_result": test_result}))
            return int(test_result["returncode"])

    build_finite_strictness_outputs(
        out_root="outputs/v2.10-finite-strictness-certificate",
        strict=args.strict,
        zip_path="witnora-core-v2.10-finite-strictness-certificate.zip",
    )
    build_edge_delta_outputs(
        out_root="outputs/v2.11-finite-edge-delta-g1-g2",
        strict=args.strict,
        zip_path="witnora-core-v2.11-finite-edge-delta-g1-g2.zip",
    )
    result = build_reproducibility_package(
        out_root=Path(args.out_root),
        strict=args.strict,
        zip_path=args.zip,
    )
    print(stable_json({"test_result": test_result, "package_result": result}))
    return 0 if result["validation"]["verification_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
