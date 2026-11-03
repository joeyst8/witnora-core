"""Single-run CDCL-to-RUP scaling probe on frozen non-affine PHP cases.

Measurements are local to the CI runner; no statistical speed claims.
Do NOT label native witness replay as Lean verification. The 3/2, 4/3, 5/4
Lean examples are checked in a separate CI step.
"""
from __future__ import annotations

import json
from time import perf_counter

from witnora_core.ood_sat_families import pigeonhole
from witnora_core.rup_witness_import import annotate_drup, verify_native_witness


def study(sizes=((3, 2), (4, 3), (5, 4), (6, 5))) -> list[dict]:
    from pysat.solvers import Glucose3

    rows = []
    for pigeons, holes in sizes:
        raw = pigeonhole(pigeons, holes).to_clause_lists()
        solver_start = perf_counter()
        with Glucose3(bootstrap_with=raw, with_proof=True) as solver:
            verdict = solver.solve()
            proof_lines = solver.get_proof() or []
        solve_ms = (perf_counter() - solver_start) * 1000
        row = {
            "family": f"PHP({pigeons},{holes})",
            "variables": pigeons * holes,
            "clauses": len(raw),
            "glucose_unsat": verdict is False,
            "glucose_proof_lines": len(proof_lines),
            "solver_and_proof_ms": round(solve_ms, 3),
            "lean_checked_in_this_benchmark": False,
            "status": "NOT_RUN",
        }
        if verdict is not False or not proof_lines:
            row["status"] = "EXTERNAL_SOLVER_NO_PROOF"
            rows.append(row)
            continue
        started = perf_counter()
        try:
            report = annotate_drup(raw, proof_lines, max_additions=2500)
        except (RuntimeError, ValueError) as exc:
            row["status"] = "CAPPED_OR_UNCHECKABLE"
            row["reason"] = str(exc)
            row["annotation_ms"] = round((perf_counter() - started) * 1000, 3)
            rows.append(row)
            continue
        row["annotation_ms"] = round((perf_counter() - started) * 1000, 3)
        verify_start = perf_counter()
        ok = verify_native_witness(raw, report["additions"])
        row["native_replay_ms"] = round((perf_counter() - verify_start) * 1000, 3)
        row["rup_additions"] = len(report["additions"])
        row["propagated_units"] = report["unit_witness_literals"]
        row["deletions_ignored"] = report["deletions_ignored"]
        row["status"] = "NATIVE_WITNESS_CONSISTENT" if ok else "NATIVE_WITNESS_REJECTED"
        rows.append(row)
    return rows


def main() -> None:
    print("CDCL_RUP_SCALING_SINGLE_RUN " + json.dumps(study(), sort_keys=True))


if __name__ == "__main__":
    main()
