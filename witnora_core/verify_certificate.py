"""Standalone verifier CLI for Witnora certificate bundles."""

from __future__ import annotations

import argparse
import json

from .proof import verify_certificate_bundle


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify a Witnora .wcert certificate")
    parser.add_argument("certificate", help=".wcert directory or .wcert.json file")
    args = parser.parse_args(argv)

    result = verify_certificate_bundle(args.certificate)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("verified") else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
