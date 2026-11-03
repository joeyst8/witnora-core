"""Turn ordinary resolution into explicit, independently Lean-checked RUP.

Each resolvent is a RUP addition with a single forced pivot witness:
negating its non-pivot literals forces the positive pivot from the left
parent, then falsifies the right parent. This proves a format bridge but
is *not yet* ingestion of an independent CDCL proof stream.
"""
from __future__ import annotations

from dataclasses import dataclass

from scripts.generate_general_resolution_lean import (
    lean_clause, lean_signed, resolution_trace, small_truth,
)
from witnora_core.ood_sat_families import pigeonhole


@dataclass(frozen=True)
class RupAddition:
    clause: tuple[int, ...]
    units: tuple[int, ...]


def from_resolution(raw: list[list[int]]) -> list[RupAddition]:
    steps = resolution_trace(raw)
    return [RupAddition(step.output, (step.pivot,)) for step in steps]


def witness_accepts(raw: list[list[int]], trace: list[RupAddition]) -> bool:
    """Independent native trace replay, not a substitute for Lean acceptance."""
    active = [tuple(row) for row in raw]
    for addition in trace:
        assumptions = {-lit for lit in addition.clause}
        for forced in addition.units:
            justified = any(
                forced in clause and
                all(lit == forced or -lit in assumptions for lit in clause)
                for clause in active
            )
            if not justified:
                return False
            assumptions.add(forced)
        conflict = any(
            all(-lit in assumptions for lit in clause) for clause in active
        )
        if not conflict:
            return False
        active.append(addition.clause)
    return () in active


def lean_rup_addition(addition: RupAddition) -> str:
    return ("{clause := " + lean_clause(addition.clause) +
            ", units := " + lean_clause(addition.units) + "}")


def main() -> None:
    raw = pigeonhole(3, 2).to_clause_lists()
    if small_truth(raw):
        raise AssertionError("PHP(3,2) is UNSAT")
    trace = from_resolution(raw)
    if not witness_accepts(raw, trace):
        raise AssertionError("RUP witness is not complete")
    rows = "[" + ", ".join(lean_signed(row) for row in raw) + "]"
    witness = "[\n  " + ",\n  ".join(
        lean_rup_addition(step) for step in trace) + "\n]"
    tampered = list(trace)
    tampered[-1] = RupAddition(tampered[-1].clause, ())
    wrong = "[\n  " + ",\n  ".join(
        lean_rup_addition(step) for step in tampered) + "\n]"
    print("import Witnora.GeneralRUP")
    print("open Witnora.GeneralRUP")
    print("set_option maxRecDepth 65536")
    print("set_option maxHeartbeats 4000000")
    print("example : checkRup (Witnora.SignedSerialization.decodeCNF")
    print(f"    ({rows} : List (List Int)))")
    print(f"    ({witness} : List RupStep) = true := by decide")
    print("example : checkRup (Witnora.SignedSerialization.decodeCNF")
    print(f"    ({rows} : List (List Int)))")
    print(f"    ({wrong} : List RupStep) = false := by decide")
    print(f"-- Non-affine PHP(3,2) source: {len(raw)} clauses, {len(trace)} RUP additions.")
    print("#print axioms Witnora.GeneralRUP.signedRup_unsat")


if __name__ == "__main__":
    main()
