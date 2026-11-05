"""Gauge/permutation metamorphic checks for bounded mixed-arity XOR proofs.

Changing variables by x_v -> x_v XOR g_v induces a parity change in each
equation's RHS. This bijective assignment transformation preserves all
inconsistent source-row index subsets, independently of variable labels.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import random

from scripts.benchmark_xor_frontier import _external_check, exhaustive_sat
from scripts.benchmark_xor_syndrome_frontier import (
    exhaustive_inconsistent_subset, parity_hypergraph,
    shortest_inconsistent_subset, validate_witness_against_original,
)
from witnora_core.cnf import CNFFormula
from witnora_core.drat_check import check_drat_text
from witnora_core.drat_trim import find_drat_trim
from witnora_core.xor import XorEquation, canonical_xor_cnf_clauses
from witnora_core.xor_drat import _row_trace_refutation, _sparse_xor_elimination_schedule


def transform_equations(equations: list[XorEquation], *,
                        renaming: dict[int, int] | None = None,
                        gauge: dict[int, bool] | None = None):
    source_variables = {v for row in equations for v in row.variables}
    renaming = dict(renaming or {v: v for v in source_variables})
    gauge = dict(gauge or {})
    if set(renaming) != source_variables or len(set(renaming.values())) != len(renaming):
        raise ValueError("renaming must be a total injective variable map")
    if any(type(v) is not int or v <= 0 for v in renaming.values()):
        raise ValueError("renaming target variables must be positive integers")
    if not set(gauge) <= source_variables:
        raise ValueError("gauge contains a variable outside the original source")
    transformed=[]
    for eq in equations:
        rhs = eq.rhs ^ (sum(bool(gauge.get(v, False)) for v in eq.variables) & 1)
        support = [renaming[v] for v in eq.variables]
        transformed.append(XorEquation(support, rhs,
            source_clauses=canonical_xor_cnf_clauses(support, rhs)))
    formula = CNFFormula(c for row in transformed for c in row.source_clauses)
    return formula, transformed


def _candidate(formula, rows, indices, *, compare_rust=False,
               external_checker=None):
    if indices is None:
        return None, 0
    validate_witness_against_original(formula, rows, indices)
    selected = [rows[i] for i in indices]
    trace = _sparse_xor_elimination_schedule(selected)["row_operation_trace"]
    opts = dict(max_proof_clauses=10000,max_proof_bytes=200000,timeout_seconds=15)
    result = _row_trace_refutation(formula,selected,trace,backend="python",**opts)
    if compare_rust:
        native = _row_trace_refutation(formula,selected,trace,backend="rust",**opts)
        if native != result:
            raise AssertionError("native/Python metamorphic proof disagreement")
    proof,error,stats = result
    if error is not None or not proof or not check_drat_text(formula,proof)["verified"]:
        raise AssertionError(f"transformed proof not original-CNF RUP accepted: {error}")
    if external_checker is not None and not _external_check(formula,proof,external_checker):
        raise AssertionError("external checker rejected gauge-transformed proof")
    return sha256(proof.encode()).hexdigest(),stats["proof_clause_count_actual"]


def evaluate_gauge(seed: int, *, contradictory: bool = True,
                   compare_rust: bool = False, external_checker: str | None = None):
    original, equations = parity_hypergraph(seed, contradictory=contradictory)
    variables = sorted({v for row in equations for v in row.variables})
    rng = random.Random(seed + 3610000)
    mapped = rng.sample(list(range(100,100+len(variables))), len(variables))
    renaming = dict(zip(variables,mapped))
    gauge = {v: bool(rng.randrange(2)) for v in variables}
    changed, transformed = transform_equations(equations,renaming=renaming,gauge=gauge)
    before, before_stats = shortest_inconsistent_subset(equations)
    after, after_stats = shortest_inconsistent_subset(transformed)
    if before != after or before != exhaustive_inconsistent_subset(equations):
        raise AssertionError("GF2 inconsistent-subsystem witness changed under gauge")
    if after != exhaustive_inconsistent_subset(transformed):
        raise AssertionError("metamorphic exhaustive subsystem oracle disagreement")
    if before_stats["reachable_states"] != after_stats["reachable_states"]:
        raise AssertionError("gauge unexpectedly changed syndrome state count")
    if exhaustive_sat(original) != exhaustive_sat(changed):
        raise AssertionError("independent original-CNF SAT oracle changed under gauge")
    first_hash, first_count = _candidate(original,equations,before,
        compare_rust=compare_rust,external_checker=external_checker)
    other_hash, other_count = _candidate(changed,transformed,after,
        compare_rust=compare_rust,external_checker=external_checker)
    if contradictory and (first_hash is None or other_hash is None):
        raise AssertionError("gauge changed contradictory proof candidate existence")
    if not contradictory and (first_hash is not None or other_hash is not None):
        raise AssertionError("SAT gauge control emitted candidate proof")
    return {"seed":seed,"contradictory":contradictory,
            "minimal_witness_rows":len(before) if before else None,
            "syndrome_reachable_states":before_stats["reachable_states"],
            "original_source_sha256":sha256(original.canonical_dimacs().encode()).hexdigest(),
            "transformed_source_sha256":sha256(changed.canonical_dimacs().encode()).hexdigest(),
            "original_proof_sha256":first_hash,"transformed_proof_sha256":other_hash,
            "proof_clauses":first_count,"transformed_proof_clauses":other_count,
            "external_drat_verified":bool(first_hash and external_checker is not None),
            "native_differential":compare_rust}


def run_gauge(*, samples: int = 64, compare_rust: bool = False,
              external_checker: str | None = None):
    if not 1 <= samples <= 200:
        raise ValueError("gauge sample count outside bounded domain")
    if external_checker is not None:
        external_checker=find_drat_trim(external_checker)
        if external_checker is None:
            raise ValueError("requested external checker unavailable")
    records=[]
    for seed in range(361000,361000+samples):
        for contradictory in (False,True):
            records.append(evaluate_gauge(seed,contradictory=contradictory,
                compare_rust=compare_rust,external_checker=external_checker))
    return {"status":"GAUGE_METAMORPHIC_CHECKS_NOT_GENERAL_SAT_THEOREM",
            "cases":len(records),"external_drat_verification_performed":external_checker is not None,
            "native_differential_performed":compare_rust,"records":records}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples",type=int,default=64)
    parser.add_argument("--compare-rust",action="store_true")
    parser.add_argument("--drat-trim")
    args=parser.parse_args()
    result=run_gauge(samples=args.samples,compare_rust=args.compare_rust,
        external_checker=args.drat_trim)
    print(json.dumps({k:v for k,v in result.items() if k!="records"},sort_keys=True))


if __name__=="__main__":
    main()
