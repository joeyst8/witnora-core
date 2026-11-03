"""Emit real Glucose DRUP proofs with exact indexed unit/conflict reasons.

The external solver and Python reason annotation are not trusted: Lean checks
each named row and the exact source clauses, including actual DIMACS bytes
for a small source-bound case.
"""
from __future__ import annotations

from dataclasses import replace

from scripts.generate_general_resolution_lean import lean_clause, lean_lit, lean_signed
from scripts.generate_glucose_drup_rup_lean import glucose_drup_witness
from scripts.generate_glucose_dense_3sat_lean import find_case
from witnora_core.rup_witness_import import (
    IndexedRUPWitness,
    attach_reason_indices,
    verify_native_indexed_witness,
)


def lean_indexed_step(step: IndexedRUPWitness) -> str:
    units = "[" + ", ".join(
        "{forced := " + lean_lit(lit) + ", rowID := " + str(row_id) + "}"
        for lit, row_id in step.units
    ) + "]"
    return ("{clause := " + lean_clause(step.clause) +
            ", units := " + units +
            ", conflictID := " + str(step.conflict_id) + "}")


def lean_trace(proof: list[IndexedRUPWitness]) -> str:
    return "[\n  " + ",\n  ".join(lean_indexed_step(step) for step in proof) + "\n]"


def lean_acceptance(source: list[list[int]], proof: list[IndexedRUPWitness],
                    *, expect: bool = True) -> None:
    raw = "[" + ", ".join(lean_signed(row) for row in source) + "]"
    steps = lean_trace(proof)
    print("example : checkIndexedRup (Witnora.SignedSerialization.decodeCNF")
    print(f"    ({raw} : List (List Int)))")
    print(f"    ({steps} : List IndexedRupStep) = {'true' if expect else 'false'} := by decide")


def lean_ascii(source: list[list[int]], proof: list[IndexedRUPWitness]) -> None:
    nvars = max(abs(lit) for row in source for lit in row)
    source_text = (f"p cnf {nvars} {len(source)}\n" +
                   "".join(" ".join(map(str, row)) + " 0\n" for row in source))
    tokens = [lit for row in source for lit in (*row, 0)]
    raw = "[" + ", ".join(lean_signed(row) for row in source) + "]"
    signed_tokens = "[" + ", ".join(map(str, tokens)) + "]"
    steps = lean_trace(proof)
    for text, expect in (
        (source_text, True),
        (source_text.replace(f"p cnf {nvars} {len(source)}",
                             f"p cnf {nvars} {len(source) - 1}", 1), False),
    ):
        ascii_bytes = "[" + ", ".join(str(ord(ch)) for ch in text) + "]"
        print("example : checkAsciiIndexedRup")
        print(f"    ({ascii_bytes} : List Nat)")
        print(f"    ({signed_tokens} : List Int)")
        print(f"    ({raw} : List (List Int))")
        print(f"    ({steps} : List IndexedRupStep) = " +
              f"{'true' if expect else 'false'} := by decide")


def main() -> None:
    print("import Witnora.GeneralRUPIndexedAscii")
    print("open Witnora.GeneralRUPIndexed")
    print("open Witnora.GeneralRUPIndexedAscii")
    print("set_option maxRecDepth 65536")
    print("set_option maxHeartbeats 8000000")
    for pigeons, holes in [(3, 2), (4, 3), (5, 4)]:
        source, report = glucose_drup_witness(pigeons, holes, indexed=True)
        proof = attach_reason_indices(source, report["additions"])
        assert verify_native_indexed_witness(source, proof)
        print(f"-- Glucose PHP({pigeons},{holes}): " +
              f"{len(proof)} additions, " +
              f"{sum(len(x.units) for x in proof)} indexed units.")
        lean_acceptance(source, proof)
        if pigeons == 3:
            lean_ascii(source, proof)
            first = proof[0]
            if not first.units:
                raise AssertionError("expected a non-empty first unit witness")
            forged = [replace(first, units=((first.units[0][0], 9999),) +
                              first.units[1:])] + proof[1:]
            assert not verify_native_indexed_witness(source, forged)
            lean_acceptance(source, forged, expect=False)
    dense_source, dense = find_case(8, 54, planted=False)
    dense_proof = attach_reason_indices(dense_source, dense["proof"]["additions"])
    assert verify_native_indexed_witness(dense_source, dense_proof)
    print(f"-- Complete-primal random 3-CNF: 8 vars, {len(dense_source)} clauses, " +
          f"{len(dense_proof)} indexed additions.")
    lean_acceptance(dense_source, dense_proof)
    print("#print axioms Witnora.GeneralRUPIndexed.signedIndexedRup_unsat")
    print("#print axioms Witnora.GeneralRUPIndexedAscii.checkAsciiIndexedRup_sound")


if __name__ == "__main__":
    main()
