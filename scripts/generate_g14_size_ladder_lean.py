"""Emit deterministic native G14/G5 source proofs for 2, 3, and 4 components."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from witnora_core.python_g14_lean_artifact import (
    actual_python_g14_artifacts, emit_python_g14_lean,
)


SIZES = (2, 3, 4)


def main():
    formal = Path("formal/Witnora")
    formal.mkdir(parents=True, exist_ok=True)
    for n in SIZES:
        instance_id = f"saf_unsat_cover_{n}"
        formula, branches = actual_python_g14_artifacts(instance_id)
        source = emit_python_g14_lean(instance_id)
        path = formal / f"GeneratedG14Size{n}.lean"
        path.write_text(source, encoding="utf-8")
        print({
            "instance": instance_id,
            "source_dimacs_sha256": sha256(formula.canonical_dimacs().encode("ascii")).hexdigest(),
            "source_clauses": formula.num_clauses,
            "branches": len(branches),
            "components_per_branch": [len(parts) for _, _, parts, _, _ in branches],
            "emitted_lean_bytes": len(source.encode("utf-8")),
            "path": str(path),
        })


if __name__ == "__main__":
    main()
