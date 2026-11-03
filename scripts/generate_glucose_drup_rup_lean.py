"""Import an actual Glucose DRUP proof and emit Lean RUP witness checks.

The external solver proposes a proof. Its UNSAT flag is insufficient;
the claimed result is validated by Lean's GeneralRUP checker.
"""
from __future__ import annotations

from scripts.generate_general_resolution_lean import lean_clause, lean_signed
from witnora_core.ood_sat_families import pigeonhole
from witnora_core.rup_witness_import import annotate_drup, verify_native_witness


def glucose_drup_witness(pigeons: int, holes: int) -> tuple[list[list[int]], dict]:
    from pysat.solvers import Glucose3

    source = pigeonhole(pigeons, holes).to_clause_lists()
    with Glucose3(bootstrap_with=source, with_proof=True) as solver:
        result = solver.solve()
        raw_proof = solver.get_proof()
    if result is not False or not raw_proof:
        raise AssertionError("independent Glucose did not emit a UNSAT proof")
    elaborated = annotate_drup(source, raw_proof)
    if not verify_native_witness(source, elaborated["additions"]):
        raise AssertionError("emitted unit witness does not replay")
    return source, elaborated


def lean_witness(item) -> str:
    return ("{clause := " + lean_clause(item.clause) +
            ", units := " + lean_clause(item.units) + "}")


def lean_example(source: list[list[int]], report: dict) -> None:
    clauses = "[" + ", ".join(lean_signed(row) for row in source) + "]"
    witness = "[\n  " + ",\n  ".join(
        lean_witness(step) for step in report["additions"]) + "\n]"
    print("example : checkRup (Witnora.SignedSerialization.decodeCNF")
    print(f"    ({clauses} : List (List Int)))")
    print(f"    ({witness} : List RupStep) = true := by decide")


def lean_ascii_example(source: list[list[int]], report: dict) -> None:
    nvars = max(abs(lit) for row in source for lit in row)
    source_text = ("p cnf " + str(nvars) + " " + str(len(source)) + "\n"
                   + "".join(" ".join(map(str, row)) + " 0\n" for row in source))
    source_bytes = "[" + ", ".join(str(ord(ch)) for ch in source_text) + "]"
    tokens = [lit for row in source for lit in (*row, 0)]
    signed_tokens = "[" + ", ".join(str(lit) for lit in tokens) + "]"
    signed_source = "[" + ", ".join(lean_signed(row) for row in source) + "]"
    witness = "[\n  " + ",\n  ".join(
        lean_witness(step) for step in report["additions"]) + "\n]"
    print("example : checkAsciiRup")
    print(f"    ({source_bytes} : List Nat)")
    print(f"    ({signed_tokens} : List Int)")
    print(f"    ({signed_source} : List (List Int))")
    print(f"    ({witness} : List RupStep) = true := by decide")
    tampered = source_text.replace(
        "p cnf " + str(nvars) + " " + str(len(source)),
        "p cnf " + str(nvars) + " " + str(len(source) - 1), 1)
    bad_bytes = "[" + ", ".join(str(ord(ch)) for ch in tampered) + "]"
    print("example : checkAsciiRup")
    print(f"    ({bad_bytes} : List Nat)")
    print(f"    ({signed_tokens} : List Int)")
    print(f"    ({signed_source} : List (List Int))")
    print(f"    ({witness} : List RupStep) = false := by decide")


def main() -> None:
    print("import Witnora.GeneralRUPAscii")
    print("open Witnora.GeneralRUP")
    print("open Witnora.GeneralRUPAscii")
    print("set_option maxRecDepth 65536")
    print("set_option maxHeartbeats 8000000")
    for pigeons, holes in [(3, 2), (4, 3), (5, 4)]:
        source, report = glucose_drup_witness(pigeons, holes)
        if len(report["additions"]) > 300:
            raise AssertionError("proof size exceeded the frozen Lean smoke cap")
        print(f"-- Actual Glucose DRUP: PHP({pigeons},{holes}); " +
              f"{len(source)} source clauses, " +
              f"{len(report['additions'])} additions, " +
              f"{report['unit_witness_literals']} propagated units, " +
              f"{report['deletions_ignored']} deletions safely retained.")
        print(f"-- Untrusted solver proof SHA-256: {report['proof_sha256']}")
        lean_example(source, report)
        if pigeons == 3:
            lean_ascii_example(source, report)
    print("#print axioms Witnora.GeneralRUP.signedRup_unsat")
    print("#print axioms Witnora.GeneralRUPAscii.checkAsciiRup_sound")


if __name__ == "__main__":
    main()
