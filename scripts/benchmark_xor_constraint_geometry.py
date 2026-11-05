"""Matched-size, matched-degree XOR interaction-geometry experiment.

Compare one n-cycle against n/2 disjoint duplicated edges. Both have n
variables, n binary-XOR constraints, and per-variable degree two; their
GF(2) ranks and bounded syndrome state counts differ. These measurements
describe an algorithm-specific state space, not general SAT complexity.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json

from scripts.benchmark_xor_frontier import _external_check
from scripts.benchmark_xor_syndrome_frontier import (
    shortest_inconsistent_subset, validate_witness_against_original,
)
from witnora_core.cnf import CNFFormula
from witnora_core.drat_check import check_drat_text
from witnora_core.drat_trim import find_drat_trim
from witnora_core.xor import XorEquation, canonical_xor_cnf_clauses
from witnora_core.xor_drat import _row_trace_refutation, _sparse_xor_elimination_schedule


def geometry(n: int, family: str, *, contradictory: bool = True):
    if n % 2 or not 4 <= n <= 16:
        raise ValueError("matched graph needs even n from 4 to 16")
    if family == "cycle":
        pairs = [(i, i + 1) for i in range(1, n)] + [(1, n)]
    elif family == "parallel_pairs":
        pairs = [(i, i + 1) for i in range(1, n, 2) for _ in range(2)]
    else:
        raise ValueError("unknown matched graph family")
    rows = []
    for index, (u, v) in enumerate(pairs):
        if family == "cycle":
            rhs = int(contradictory and index == len(pairs) - 1)
        else:
            # Each duplicated pair carries opposite RHS constraints when
            # UNSAT, ensuring *unique* source-CNF clause counts also match.
            rhs = int(contradictory and index % 2 == 1)
        rows.append(XorEquation([u, v], rhs,
            source_clauses=canonical_xor_cnf_clauses([u, v], rhs)))
    formula = CNFFormula(c for eq in rows for c in eq.source_clauses)
    return formula, rows


def support_rank(equations: list[XorEquation]) -> int:
    positions = {v: i for i, v in enumerate(sorted({v for e in equations for v in e.variables}))}
    pivots = {}
    for eq in equations:
        mask = sum(1 << positions[v] for v in eq.variables)
        while mask:
            p = mask.bit_length() - 1
            if p not in pivots:
                pivots[p] = mask
                break
            mask ^= pivots[p]
    return len(pivots)


def measure_geometry(n: int, family: str, *, contradictory: bool = True,
                     compare_rust: bool = False, external_checker: str | None = None,
                     max_states: int = 100000):
    formula, equations = geometry(n, family, contradictory=contradictory)
    witness, stats = shortest_inconsistent_subset(equations, max_states=max_states)
    degrees = {}
    for eq in equations:
        for v in eq.variables:
            degrees[v] = degrees.get(v, 0) + 1
    if set(degrees) != set(range(1, n + 1)) or any(degree != 2 for degree in degrees.values()):
        raise AssertionError("matched geometry degree profile was not preserved")
    proof = None
    proof_stats = {"proof_clause_count_actual": 0, "proof_file_size_bytes": 0}
    if contradictory:
        if witness is None:
            raise AssertionError("contradictory matched graph lost GF2 witness")
        validate_witness_against_original(formula, equations, witness)
        selected = [equations[i] for i in witness]
        trace = _sparse_xor_elimination_schedule(selected)["row_operation_trace"]
        opts = dict(max_proof_clauses=2000,max_proof_bytes=40000,timeout_seconds=15)
        proof, error, proof_stats = _row_trace_refutation(formula,selected,trace,
                                                         backend="python",**opts)
        if compare_rust:
            native = _row_trace_refutation(formula,selected,trace,backend="rust",**opts)
            if native != (proof,error,proof_stats):
                raise AssertionError("native/Python matched graph candidate disagrees")
        if error is not None or not proof or not check_drat_text(formula,proof)["verified"]:
            raise AssertionError(f"matched graph original-CNF RUP proof rejected: {error}")
        if external_checker is not None and not _external_check(formula,proof,external_checker):
            raise AssertionError("independent drat-trim rejected matched graph proof")
    elif witness is not None:
        raise AssertionError("consistent matched graph invented contradiction")
    return {"n":n,"family":family,"contradictory":contradictory,
            "variables":len(degrees),"constraints":len(equations),
            "clause_width":2,"variable_degrees":sorted(degrees.values()),
            "source_clauses":formula.num_clauses,
            "gf2_support_rank":support_rank(equations),
            "minimum_inconsistent_rows":len(witness) if witness else None,
            "syndrome_reachable_states":stats["reachable_states"],
            "syndrome_peak_states":stats["peak_states"],
            "proof_clauses":proof_stats["proof_clause_count_actual"],
            "proof_bytes":proof_stats["proof_file_size_bytes"],
            "source_sha256":sha256(formula.canonical_dimacs().encode()).hexdigest(),
            "external_drat_verified":bool(proof and external_checker is not None),
            "native_differential":compare_rust}


def run_matched(*, compare_rust: bool = False,
                external_checker: str | None = None, maximum_n: int = 14):
    if maximum_n % 2 or not 4 <= maximum_n <= 16:
        raise ValueError("maximum_n outside bounded even domain")
    if external_checker is not None:
        external_checker = find_drat_trim(external_checker)
        if external_checker is None:
            raise ValueError("requested external checker unavailable")
    results=[]
    for n in range(4,maximum_n+1,2):
        for family in ("cycle","parallel_pairs"):
            results.append(measure_geometry(n,family,compare_rust=compare_rust,
                                            external_checker=external_checker))
    return {"status":"MATCHED_GEOMETRY_RESEARCH_NOT_GENERAL_COMPLEXITY",
            "external_drat_verification_performed":external_checker is not None,
            "native_differential_performed":compare_rust,
            "results":results}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-n",type=int,default=14)
    parser.add_argument("--compare-rust",action="store_true")
    parser.add_argument("--drat-trim")
    args=parser.parse_args()
    print(json.dumps(run_matched(compare_rust=args.compare_rust,
        external_checker=args.drat_trim,maximum_n=args.max_n),sort_keys=True))


if __name__=="__main__":
    main()
