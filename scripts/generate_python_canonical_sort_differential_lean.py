"""Finite Python-to-Lean adversarial study of sorting accepted affine rows.

A real Python canonical XOR-CNF generator supplies the source clauses.
The rows are deliberately unsorted, may overlap, and have mixed syndromes.
Lean independently checks exact semantic-affine extraction before and
after row sorting. This is finite evidence, not a universal lemma.
"""

from __future__ import annotations

import random

from witnora_core.cnf import CNFFormula
from witnora_core.xor import canonical_xor_cnf_clauses


def _list(items):
    return "[" + ", ".join(str(item) for item in items) + "]"


def _clauses(clauses):
    return "[" + ", ".join(_list(clause) for clause in clauses) + "]"


def _rows(rows):
    return "[" + ", ".join(
        "{coefficients := " + _list(coeff) + ", rhs := " +
        ("true" if rhs else "false") + "}"
        for coeff, rhs in rows
    ) + "]"


def emit():
    rng = random.Random(630643)
    lines = [
        "import Witnora.TC063CanonicalAffineBridge",
        "namespace Witnora.GeneratedPythonCanonicalSortDifferential",
        "open Witnora.TC063CanonicalAffineBridge",
        "open Witnora.ExactAffineMembership",
        "set_option maxRecDepth 8192",
        "set_option maxHeartbeats 8000000",
    ]
    n = 0
    unsorted = 0
    for arity in (1, 2, 3):
        for repetition in range(16):
            ids = sorted(rng.sample(range(1, 45), max(arity, 3)))
            rows = []
            for j in range(1 + repetition % 2):
                variables = rng.sample(ids, arity)
                rhs = (j + repetition) % 2
                rows.append((variables, rhs))
            signed = []
            for variables, rhs in rows:
                signed.extend(canonical_xor_cnf_clauses(variables, rhs))
            formula = CNFFormula.from_raw_clauses(signed)
            cnf = "Witnora.SignedSerialization.decodeCNF " + _clauses(
                formula.to_clause_lists()
            )
            row_text = _rows(rows)
            lines.extend([
                f"-- Python case {n}: {arity}-variable equations, {len(rows)} rows",
                f"example : checkSemanticExactAffine 3 ({cnf}) "
                f"{row_text} = true := by decide",
                f"example : checkSemanticExactAffine 3 ({cnf}) "
                f"(sortAffineRows {row_text}) = true := by decide",
            ])
            if any(vars != sorted(vars) for vars, _ in rows):
                unsorted += 1
            n += 1
    lines.extend([
        f"-- {n} accepted Python-derived exact-affine systems, "
        f"{unsorted} deliberately noncanonical coefficient-order systems.",
        "end Witnora.GeneratedPythonCanonicalSortDifferential",
        "",
    ])
    return "\n".join(lines)


if __name__ == "__main__":
    print(emit(), end="")
