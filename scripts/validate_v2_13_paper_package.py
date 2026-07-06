"""Validate a generated v2.13 paper-hardening/reviewer-defense package."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from witnora_core.paper_hardening import validate_paper_hardening_package
from witnora_core.strictness_proof import stable_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the v2.13 paper hardening package")
    parser.add_argument("--package-root", default="outputs/v2.13-paper-hardening-reviewer-defense")
    args = parser.parse_args(argv)
    result = validate_paper_hardening_package(args.package_root)
    print(stable_json(result))
    return 0 if result["verification_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
