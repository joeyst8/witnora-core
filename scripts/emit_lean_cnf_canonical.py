"""Kernel-check actual Python CNF canonicalization against Lean normalization.

This emits concrete, closed proof obligations for deterministic adversarial and
seeded randomized valid signed-integer inputs. It does not prove Python source
correct for every execution.
"""
from __future__ import annotations

import random
from pathlib import Path

from witnora_core.cnf import CNFFormula

SEED = 63063
RANDOM_CASES = 32
OUTPUT = Path("formal/Witnora/CNFCanonicalGenerated.lean")


def lean_signed_cnf(rows: list[list[int]]) -> str:
    return "[" + ", ".join(
        "[" + ", ".join(str(int(x)) for x in row) + "]"
        for row in rows
    ) + "]"


def examples() -> list[list[list[int]]]:
    cases = [
        [],
        [[]],
        [[1, 1, 1]],
        [[1, -1]],
        [[1, -1, 2]],
        [[-1, 1, 0 + 2], [3]],
        [[1, 1, -2], [1, 1, -2], []],
        [[-3, 2, 1], [1, 2, -3]],
        [[5, -5, 3], [3, 3], [3, -3]],
        [[-2, -2, 1], [1, -2], [6, 6, -6]],
        [[1, 2, 3], [-1, -2, -3], [1, 2, 3]],
    ]
    rng = random.Random(SEED)
    values = [-6, -5, -4, -3, -2, -1, 1, 2, 3, 4, 5, 6]
    for _ in range(RANDOM_CASES):
        clauses = [
            [rng.choice(values) for _ in range(rng.randrange(7))]
            for _ in range(rng.randrange(8))
        ]
        cases.append(clauses)
    return cases


def main() -> None:
    lines = [
        "import Witnora.CNFCanonical",
        "import Witnora.SignedSerialization",
        "",
        "/- Concrete Python output / Lean normalization correspondence,",
        "   modulo order of literals and clauses. -/",
        "namespace Witnora.GeneratedCanonical",
        "",
        "def sameLiterals (left right : List Witnora.Concrete.Literal) : Bool :=",
        "  left.all (fun lit => decide (lit ∈ right)) &&",
        "    right.all (fun lit => decide (lit ∈ left))",
        "",
        "def sameClauses (left right : Witnora.Concrete.CNF) : Bool :=",
        "  left.all (fun clause => right.any (sameLiterals clause)) &&",
        "    right.all (fun clause => left.any (sameLiterals clause))",
        "",
    ]
    for i, raw in enumerate(examples()):
        actual = CNFFormula.from_raw_clauses(raw).to_clause_lists()
        lines += [
            f"-- Case {i}: actual Python CNFFormula.from_raw_clauses output.",
            "example : sameClauses",
            "  (Witnora.CNFCanonical.normalize",
            f"    (Witnora.SignedSerialization.decodeCNF {lean_signed_cnf(raw)}))",
            f"  (Witnora.SignedSerialization.decodeCNF {lean_signed_cnf(actual)})",
            "    = true := by decide",
            "",
        ]
    lines += ["end Witnora.GeneratedCanonical", ""]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated {len(examples())} Python/Lean CNF normalization claims in {OUTPUT}")


if __name__ == "__main__":
    main()
