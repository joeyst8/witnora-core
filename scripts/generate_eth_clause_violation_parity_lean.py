"""Emit kernel-checked finite controls for source-bound clause-violation parity.

Reuses the exact deterministic dense 8-variable source CNFs from the Glucose
gate. All 256 assignments are checked by Lean reduction in each example.
This is an exponential finite verification, not fast model counting.
"""
from __future__ import annotations

from scripts.generate_glucose_dense_3sat_lean import find_case
from witnora_core.eth_clause_violation_parity import (
    build_finite_sketch, verify_finite_sketch
)


def signed(source: list[list[int]]) -> str:
    return "[" + ", ".join("[" + ", ".join(map(str, clause)) + "]"
                          for clause in source) + "]"


def masks(rows: tuple[tuple[int, ...], ...], nclauses: int) -> str:
    return "[" + ", ".join(
        "[" + ", ".join("true" if j in row else "false"
                        for j in range(nclauses)) + "]"
        for row in rows
    ) + "]"


def main() -> None:
    print("import Witnora.ClauseViolationParity")
    print("open Witnora.ClauseViolationParity")
    print("set_option maxRecDepth 65536")
    print("set_option maxHeartbeats 8000000")
    for planted in (False, True):
        source, info = find_case(8, 54, planted=planted)
        sketch = build_finite_sketch(source, 8)
        assert verify_finite_sketch(source, sketch)
        assert sketch.survivors[-1] == 0
        print(f"-- Frozen seed {info['seed']}; planted={planted}; "
              f"{len(sketch.rows)} sparse rows, {sketch.satisfying_count} models.")
        print("example : boundedExact")
        print(f"    ({signed(source)} : List (List Int))")
        print(f"    ({masks(sketch.rows, len(source))} : List (List Bool))")
        print("    8 = true := by decide")


if __name__ == "__main__":
    main()
