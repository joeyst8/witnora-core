"""Independent SAT cross-check and timing baseline for G5/G14 fixtures.

This is *testing*, not a universal correctness proof or a complexity result.
Install the external oracle with: python -m pip install python-sat
Run: PYTHONPATH=. python scripts/benchmark_affine_sat.py
"""
from __future__ import annotations

import json
from time import perf_counter

from pysat.solvers import Solver

from witnora_core.operator_genesis import (
    AFFINE_RESIDUE_SAT_WITNESS_VERIFIED,
    AFFINE_RESIDUE_UNSAT_NATIVE_CERTIFIED,
    build_affine_residue_certificate,
    make_affine_residue_instance,
)
from witnora_core.separator_affine_family_theorem import (
    SAT_CERTIFIED,
    UNSAT_CERTIFIED,
    build_separator_affine_certificate,
    make_separator_affine_instance,
)

G5_CASES = (
    "parity_arity_7_sat",
    "parity_arity_7_unsat",
    "parity_arity_8_sat",
    "parity_arity_8_unsat",
    "parity_arity_9_sat",
    "parity_arity_9_unsat",
)
G14_CASES = (
    "saf_sat_chain_2",
    "saf_unsat_cover_2",
    "saf_balanced_sat_2",
    "saf_sat_chain_4",
    "saf_unsat_cover_4",
    "saf_balanced_sat_8",
    "saf_unsat_cover_8",
    "saf_sat_chain_16",
    "saf_unsat_cover_16",
)


def oracle_satisfiable(clauses: list[list[int]]) -> bool:
    # CNF is passed verbatim to a solver developed independently of Witnora.
    with Solver(name="glucose3", bootstrap_with=clauses) as solver:
        return bool(solver.solve())


def benchmark_one(kind: str, name: str) -> dict:
    if kind == "G5":
        instance = make_affine_residue_instance(name)
        started = perf_counter()
        cert = build_affine_residue_certificate(instance)
        witnora_seconds = perf_counter() - started
        if cert.status == AFFINE_RESIDUE_SAT_WITNESS_VERIFIED:
            claimed_sat = True
        elif cert.status == AFFINE_RESIDUE_UNSAT_NATIVE_CERTIFIED:
            claimed_sat = False
        else:
            raise AssertionError(f"{name}: no certified G5 outcome ({cert.status})")
    elif kind == "G14":
        instance = make_separator_affine_instance(name)
        started = perf_counter()
        cert = build_separator_affine_certificate(instance)
        witnora_seconds = perf_counter() - started
        if cert.final_result == SAT_CERTIFIED:
            claimed_sat = True
        elif cert.final_result == UNSAT_CERTIFIED:
            claimed_sat = False
        else:
            raise AssertionError(f"{name}: no certified G14 outcome ({cert.final_result})")
    else:
        raise ValueError(kind)

    clauses = instance.formula.to_clause_lists()
    started = perf_counter()
    oracle_sat = oracle_satisfiable(clauses)
    oracle_seconds = perf_counter() - started
    if claimed_sat != oracle_sat:
        raise AssertionError(
            f"{kind}/{name}: Witnora SAT={claimed_sat}, Glucose3 SAT={oracle_sat}"
        )
    return {
        "family": kind,
        "instance": name,
        "num_variables": instance.formula.max_var,
        "num_clauses": len(clauses),
        "witnora_satisfiable": claimed_sat,
        "glucose3_satisfiable": oracle_sat,
        "witnora_seconds": round(witnora_seconds, 6),
        "glucose3_seconds": round(oracle_seconds, 6),
        "agreement": True,
    }


def main() -> None:
    results = [
        benchmark_one(kind, name)
        for kind, names in (("G5", G5_CASES), ("G14", G14_CASES))
        for name in names
    ]
    print(json.dumps({"schema": 1, "method": "single run, wall-clock seconds, "
                      "same input CNF, no performance claim", "cases": results},
                     indent=2))


if __name__ == "__main__":
    main()
