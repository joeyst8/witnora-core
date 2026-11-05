"""Materialize Python-generated ASCII byte certificates as kernel-checkable Lean."""
from __future__ import annotations

import argparse
from pathlib import Path

from witnora_core.lean_ascii_certificate_export import emit_ascii_lean


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path,
        default=Path("formal/Witnora/GeneratedAsciiCertificates.lean"),
    )
    args = parser.parse_args()
    source = emit_ascii_lean()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(source, encoding="utf-8")
    print({"output": str(args.output), "source_bytes": len(source.encode("utf-8"))})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
