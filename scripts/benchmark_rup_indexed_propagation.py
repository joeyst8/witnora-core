"""Single-run A/B timing: indexed RUP witness generator vs reference scans.

Both versions consume identical Glucose DRUP text and are independently
replayed. Neither replay is a substitute for the separate Lean kernel gate.
"""
from __future__ import annotations

import json
from time import perf_counter

from pysat.solvers import Glucose3

from witnora_core.ood_sat_families import pigeonhole
from witnora_core.rup_witness_import import annotate_drup, verify_native_witness


def benchmark() -> list[dict]:
    rows = []
    for n, m in [(3, 2), (4, 3), (5, 4), (6, 5)]:
        source = pigeonhole(n, m).to_clause_lists()
        with Glucose3(bootstrap_with=source, with_proof=True) as solver:
            if solver.solve() is not False:
                raise AssertionError("PHP control unexpectedly SAT")
            proof = solver.get_proof()
        if not proof:
            raise AssertionError("missing independent CDCL proof")
        result = {"family": f"PHP({n},{m})", "variables": n*m,
                  "source_clauses": len(source), "proof_lines": len(proof),
                  "lean_checked_in_this_benchmark": False}
        traces = {}
        for indexed in (False, True):
            mode = "indexed" if indexed else "reference"
            started = perf_counter()
            report = annotate_drup(source, proof, indexed_propagation=indexed,
                                   max_additions=2500)
            result[mode + "_annotation_ms"] = round(
                (perf_counter() - started) * 1000, 3)
            result[mode + "_units"] = report["unit_witness_literals"]
            result[mode + "_native_replay"] = verify_native_witness(
                source, report["additions"])
            if not result[mode + "_native_replay"]:
                raise AssertionError("bad native RUP replay")
            traces[mode] = [item.clause for item in report["additions"]]
        if traces["indexed"] != traces["reference"]:
            raise AssertionError("reference and indexed additions differ")
        result["same_added_clauses"] = True
        result["indexed_speedup_single_run"] = round(
            result["reference_annotation_ms"] /
            max(result["indexed_annotation_ms"], 0.000001), 2)
        rows.append(result)
    return rows


def main() -> None:
    print("RUP_INDEXED_AB_SINGLE_RUN " + json.dumps(benchmark(), sort_keys=True))


if __name__ == "__main__":
    main()
