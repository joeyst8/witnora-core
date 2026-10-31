"""Generate deterministic Lean source from actual Python coloring outputs."""
from __future__ import annotations

import argparse
from pathlib import Path

from witnora_core.lean_color_certificate_export import emit_lean, generate_default_cases


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path,
                        default=Path("formal/Witnora/GeneratedColorCertificates.lean"))
    args = parser.parse_args()
    source = emit_lean()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(source, encoding="utf-8")
    print({"generated_file": str(args.output),
           "certificates": [case[0] for case in generate_default_cases()],
           "bytes": len(source.encode("utf-8")),
           "python_to_lean_refinement_verified": False})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
