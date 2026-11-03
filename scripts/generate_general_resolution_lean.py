"""Build checkable ordinary-resolution traces from arbitrary small signed CNFs.

This is a deliberately simple saturation *producer*, not a solver speed claim.
It is complete for finite CNFs if allowed unlimited memory/time, but can
expand exponentially. The Lean checker is the proof authority; Python may
propose invalid traces without compromising soundness.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product

from witnora_core.ood_sat_families import pigeonhole


@dataclass(frozen=True)
class Step:
    left: tuple[int, ...]
    right: tuple[int, ...]
    pivot: int
    output: tuple[int, ...]


def resolution_trace(
    raw: list[list[int]], *, max_clauses: int = 2000
) -> list[Step]:
    if max_clauses <= 0:
        raise ValueError("positive proof-size limit required")
    if any(type(lit) is not int or lit == 0 for row in raw for lit in row):
        raise ValueError("resolution source must contain nonzero integer literals")
    database: list[tuple[int, ...]] = [tuple(row) for row in raw]
    known = {frozenset(row) for row in database}
    if any(not row for row in database):
        return []
    steps: list[Step] = []
    i = 0
    while i < len(database):
        new = database[i]
        for j in range(i):
            old = database[j]
            pivots = sorted({abs(lit) for lit in new + old})
            for pivot in pivots:
                if pivot in new and -pivot in old:
                    left, right = new, old
                elif pivot in old and -pivot in new:
                    left, right = old, new
                else:
                    continue
                output = tuple(lit for lit in left if lit != pivot) + tuple(
                    lit for lit in right if lit != -pivot
                )
                if any(-lit in output for lit in output):
                    continue  # Tautological resolvents cannot help refute
                key = frozenset(output)
                if key in known:
                    continue
                known.add(key)
                database.append(output)
                steps.append(Step(left, right, pivot, output))
                if not output:
                    return steps
                if len(database) >= max_clauses:
                    raise RuntimeError("resolution search hit the proof-size cap")
        i += 1
    raise ValueError("no refutation: source is satisfiable or proof generation incomplete")


def indexed_trace(raw: list[list[int]], steps: list[Step]) -> list[tuple[int, int, int]]:
    """Serialize source/derived-row references, with no trusted index guesses."""
    rows = [tuple(row) for row in raw]
    result = []
    for step in steps:
        left = rows.index(step.left)
        right = rows.index(step.right)
        result.append((left, right, step.pivot))
        rows.append(step.output)
    return result


def verify_steps(raw: list[list[int]], steps: list[Step]) -> bool:
    """Independent native format check, never treated as the proof authority."""
    database = {tuple(row) for row in raw}
    for step in steps:
        if (step.left not in database or step.right not in database
                or step.pivot <= 0 or step.pivot not in step.left
                or -step.pivot not in step.right):
            return False
        expected = tuple(lit for lit in step.left if lit != step.pivot) + tuple(
            lit for lit in step.right if lit != -step.pivot
        )
        if step.output != expected:
            return False
        database.add(step.output)
    return () in database


def small_truth(raw: list[list[int]]) -> bool:
    """Independent exhaustive truth oracle ONLY for tiny tests."""
    variables = sorted({abs(lit) for row in raw for lit in row})
    if len(variables) > 16:
        raise ValueError("bounded tiny-oracle only")
    for values in product((False, True), repeat=len(variables)):
        a = dict(zip(variables, values))
        if all(any(a[abs(lit)] == (lit > 0) for lit in row) for row in raw):
            return True
    return False


def lean_lit(lit: int) -> str:
    return f"({abs(lit)}, {'true' if lit > 0 else 'false'})"


def lean_clause(row: tuple[int, ...] | list[int]) -> str:
    return "[" + ", ".join(lean_lit(lit) for lit in row) + "]"


def lean_signed(row: list[int]) -> str:
    return "[" + ", ".join(str(lit) for lit in row) + "]"


def lean_step(step: Step) -> str:
    return ("{ left := " + lean_clause(step.left) +
            ", right := " + lean_clause(step.right) +
            ", pivot := " + str(step.pivot) +
            ", output := " + lean_clause(step.output) + " }")


def main() -> None:
    # Non-affine pigeonhole contradiction, not a bounded-affine TC-063 example.
    raw = pigeonhole(3, 2).to_clause_lists()
    if small_truth(raw):
        raise AssertionError("pigeonhole 3->2 must be UNSAT")
    steps = resolution_trace(raw)
    if not verify_steps(raw, steps):
        raise AssertionError("Python resolution trace is internally inconsistent")
    print("import Witnora.GeneralResolutionStream")
    print("open Witnora.GeneralResolution")
    print("open Witnora.GeneralResolutionIndexed")
    print("open Witnora.GeneralResolutionStream")
    print("set_option maxRecDepth 65536")
    print("set_option maxHeartbeats 4000000")
    print("-- The Lean evaluator checks all resolution steps from signed CNF clauses.")
    print("-- No small separators, affine extraction, or SAT oracle are assumed.")
    raw_lean = "[" + ", ".join(lean_signed(row) for row in raw) + "]"
    trace_lean = "[\n  " + ",\n  ".join(lean_step(step) for step in steps) + "\n]"
    print("example : checkResolution (Witnora.SignedSerialization.decodeCNF")
    print(f"    ({raw_lean} : List (List Int)))")
    print(f"    ({trace_lean} : List Step) = true := by decide")
    idx = indexed_trace(raw, steps)
    compact_lean = "[\n  " + ",\n  ".join(
        "{leftID := " + str(a) + ", rightID := " + str(b) +
        ", pivot := " + str(v) + "}" for a, b, v in idx
    ) + "\n]"
    print("example : checkIndexed (Witnora.SignedSerialization.decodeCNF")
    print(f"    ({raw_lean} : List (List Int)))")
    print(f"    ({compact_lean} : List Instruction) = true := by decide")
    print("example : checkStream (Witnora.SignedSerialization.decodeCNF")
    print(f"    ({raw_lean} : List (List Int)))")
    print(f"    ({compact_lean} : List Instruction) = true := by decide")
    print(f"-- PHP(3,2): {len(raw)} source clauses; {len(steps)} derived resolutions.")
    print(f"-- Indexed trace payload: {len(compact_lean)} characters; full by-value trace: {len(trace_lean)} characters.")
    print("#print axioms Witnora.GeneralResolutionStream.signedStream_unsat")
    print("#print axioms Witnora.GeneralResolutionIndexed.signedIndexed_unsat")
    print("#print axioms Witnora.GeneralResolution.signedResolution_unsat")


if __name__ == "__main__":
    main()
