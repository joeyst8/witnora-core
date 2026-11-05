"""Validate a generated v2.12 paper/reproducibility package."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from witnora_core.reproducibility_package import stable_json, validate_package


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the v2.12 reproducibility package")
    parser.add_argument("--package-root", default="outputs/v2.12-paper-reproducibility-package")
    args = parser.parse_args(argv)
    result = validate_package(args.package_root)
    print(stable_json(result))
    return 0 if result["verification_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
