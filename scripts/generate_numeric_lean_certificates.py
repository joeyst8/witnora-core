"""Materialize generated raw Nat certificates for Lean kernel verification."""
from __future__ import annotations

import argparse
from pathlib import Path

from witnora_core.lean_numeric_certificate_export import emit_numeric_lean


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path,
                        default=Path("formal/Witnora/GeneratedNumericCertificates.lean"))
    args = parser.parse_args()
    source = emit_numeric_lean()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(source, encoding="utf-8")
    print({"output": str(args.output), "bytes": len(source.encode("utf-8")),
           "lean_kernel_verification_required": True})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
