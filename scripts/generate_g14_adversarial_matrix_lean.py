"""Deterministic adversarial Python G14 -> Lean partition-refinement matrix.

The real production conditioner constructs each candidate; the Lean kernel
independently checks the signed-literal residual partition. The matrix is
bounded testing, not a universal correctness proof of CPython.
"""
from __future__ import annotations

from random import Random
from pathlib import Path

from witnora_core.cnf import CNFFormula
from witnora_core.python_g14_lean_artifact import lean_cnf, lean_branch
from witnora_core.separator_affine_family_theorem import (
    _all_assignments, _component_dicts, _condition_by_separator,
)


CASES = (
    ("contradictory_units", [[1], [-1], [3]], (1,)),
    ("duplicate_clause", [[1, 3], [1, 3], [-1, 4]], (1,)),
    ("separator_only_empty", [[1], [2, -3]], (1,)),
    ("explicit_empty_clause", [[], [1, 2]], (1,)),
    ("two_separator_variables", [[1, 3], [-2, 4], [1, 2]], (1, 2)),
    ("two_separator_contradiction", [[1], [-1], [2], [-2]], (1, 2)),
    ("zero_residual_components", [[1], [-1]], (1,)),
)


def _random_case(seed: int) -> tuple[str, list[list[int]], tuple[int, ...]]:
    rng = Random(63_000 + seed)
    raw = []
    for _ in range(3 + seed % 5):
        width = rng.randrange(0, 4)
        raw.append([
            v if rng.getrandbits(1) else -v
            for v in rng.sample(range(1, 6), width)
        ])
    # Force a nonempty one- or two-variable separator in the formula.
    separator = (1,) if seed % 2 == 0 else (1, 2)
    raw.append([1, 3])
    if len(separator) == 2:
        raw.append([-2, 4])
    return f"random_{seed:02d}", raw, separator


def _list_of_cnfs(parts: list[CNFFormula]) -> str:
    return "[" + ", ".join(lean_cnf(part) for part in parts) + "]"


def emit_adversarial_matrix(random_cases: int = 16) -> tuple[str, dict[str, int]]:
    if random_cases < 0 or random_cases > 64:
        raise ValueError("random_cases must be in [0, 64]")
    cases = list(CASES) + [_random_case(i) for i in range(random_cases)]
    lines = [
        "import Witnora.G14NormalizedPartition",
        "namespace Witnora.GeneratedG14AdversarialMatrix",
        "open Witnora.Concrete",
        "open Witnora.FiniteXor",
        "open Witnora.Extraction",
        "open Witnora.G5Extraction",
        "open Witnora.Conditioning",
        "open Witnora.ComponentPartition",
        "open Witnora.G14NormalizedPartition",
        "open Witnora.SeparatorAssignments",
        "set_option maxRecDepth 8192",
        "set_option maxHeartbeats 0",
    ]
    stats = {"cases": 0, "branches": 0, "rejected_mutations": 0,
             "empty_residuals": 0, "normalized_duplicate_cases": 0}
    for case_id, (name, raw, separator) in enumerate(cases):
        formula = CNFFormula.from_raw_clauses(raw)
        if len(raw) != formula.num_clauses:
            stats["normalized_duplicate_cases"] += 1
        components = _component_dicts(formula, list(separator))
        prefix = f"case{case_id}"
        lines.append(f"-- {name}, separator={separator}")
        lines.append(f"def {prefix} : CNF := {lean_cnf(formula)}")
        patterns = []
        for assignment in _all_assignments(separator):
            branch = lean_branch(assignment)
            patterns.append(branch)
            residual, partition, errors = _condition_by_separator(
                formula, assignment, components)
            if errors:
                raise ValueError(f"{name} {branch}: {errors}")
            actual = list(partition.values())
            expected_clauses = sorted(tuple(c) for c in residual.to_clause_lists())
            actual_clauses = sorted(
                tuple(c) for part in actual for c in part.to_clause_lists())
            if expected_clauses != actual_clauses:
                raise ValueError(f"{name} {branch}: Python clause partition failed")
            fixed = f"(fixedOf {branch})"
            residual_lean = f"(conditionCNF {fixed} {prefix})"
            parts_lean = _list_of_cnfs(actual)
            lines.append(
                f"example : checkNormalizedPartition {residual_lean} "
                f"{parts_lean} = true := by decide"
            )
            # Verify that Python's own residual clauses are exactly Lean's
            # conditioned clauses, up to normalized order.
            lines.append(
                f"example : checkPartition {residual_lean} "
                f"[{lean_cnf(residual)}] = true := by decide"
            )
            if not residual.num_clauses:
                stats["empty_residuals"] += 1
            else:
                # Drop one actual clause; Lean must reject the mutated proof.
                dropped = []
                removed = False
                for part in actual:
                    cls = part.to_clause_lists()
                    if cls and not removed:
                        cls = cls[1:]
                        removed = True
                    dropped.append(CNFFormula.from_raw_clauses(cls))
                if not removed:
                    raise ValueError("nonempty residual had no components")
                lines.append(
                    f"example : checkPartition {residual_lean} "
                    f"{_list_of_cnfs(dropped)} = false := by decide"
                )
                stats["rejected_mutations"] += 1
            stats["branches"] += 1
        lines.append(
            f"example : enumerate {list(separator)} = "
            f"[{', '.join(patterns)}] := by decide"
        )
        stats["cases"] += 1
    lines.extend([
        "-- Every accepted instance inherits model preservation from",
        "-- Witnora.ComponentPartition.conditioned_partition_correct.",
        "#print axioms Witnora.ComponentPartition.conditioned_partition_correct",
        "end Witnora.GeneratedG14AdversarialMatrix",
        "",
    ])
    return "\n".join(lines), stats


def main() -> None:
    target = Path("formal/Witnora/GeneratedG14AdversarialMatrix.lean")
    source, stats = emit_adversarial_matrix()
    target.write_text(source, encoding="utf-8")
    print({"path": str(target), **stats})


if __name__ == "__main__":
    main()
