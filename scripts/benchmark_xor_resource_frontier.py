"""Exact state/proof cap thresholds for bounded GF2 contradiction witnesses."""

from __future__ import annotations

import argparse
import json

from scripts.benchmark_xor_constraint_geometry import geometry
from scripts.benchmark_xor_frontier import _external_check
from scripts.benchmark_xor_syndrome_frontier import (
    shortest_inconsistent_subset,validate_witness_against_original,
)
from witnora_core.drat_check import check_drat_text
from witnora_core.drat_trim import find_drat_trim
from witnora_core.xor_drat import _row_trace_refutation,_sparse_xor_elimination_schedule


def measure_cap(n: int, *, compare_rust: bool = False,
                external_checker: str | None = None):
    formula, equations = geometry(n,"cycle",contradictory=True)
    expected_states = 1 << n
    witness, stats = shortest_inconsistent_subset(equations,max_states=expected_states)
    if stats["reachable_states"] != expected_states:
        raise AssertionError("exact GF2 state count changed")
    try:
        shortest_inconsistent_subset(equations,max_states=expected_states-1)
    except ValueError as exc:
        if "state cap" not in str(exc):
            raise
    else:
        raise AssertionError("one-under GF2 state cap did not fail closed")
    validate_witness_against_original(formula,equations,witness)
    selected=[equations[i] for i in witness]
    trace=_sparse_xor_elimination_schedule(selected)["row_operation_trace"]
    opts=dict(max_proof_clauses=2000,max_proof_bytes=40000,timeout_seconds=15)
    proof,error,counts=_row_trace_refutation(formula,selected,trace,backend="python",**opts)
    if compare_rust:
        rust=_row_trace_refutation(formula,selected,trace,backend="rust",**opts)
        if rust != (proof,error,counts):
            raise AssertionError("native/Python proof cap experiment disagrees")
    if error is not None or not proof or not check_drat_text(formula,proof)["verified"]:
        raise AssertionError("bounded cap experiment proof not RUP verified")
    if external_checker is not None and not _external_check(formula,proof,external_checker):
        raise AssertionError("independent checker rejected cap experiment proof")
    clauses=counts["proof_clause_count_actual"]
    size=counts["proof_file_size_bytes"]
    def rejected(**override):
        attempt=_row_trace_refutation(formula,selected,trace,backend="python",
                                       **{**opts,**override})
        if attempt[0] is not None:
            raise AssertionError("under-cap proof unexpectedly succeeded")
        return attempt[1]
    if rejected(max_proof_clauses=clauses-1)!="SKIPPED_PROOF_SIZE_CAP":
        raise AssertionError("clause cap error changed")
    if rejected(max_proof_bytes=size-1)!="SKIPPED_PROOF_BYTES_CAP":
        raise AssertionError("byte cap error changed")
    exact=_row_trace_refutation(formula,selected,trace,backend="python",
                                 **{**opts,"max_proof_clauses":clauses,"max_proof_bytes":size})
    if exact!=(proof,error,counts):
        raise AssertionError("exact proof cap should permit identical candidate")
    return {"n":n,"source_clauses":formula.num_clauses,
            "gf2_states":expected_states,"minimum_inconsistent_rows":len(witness),
            "proof_clauses":clauses,"proof_bytes":size,
            "state_under_cap_rejected":True,"proof_under_caps_rejected":True,
            "external_drat_verified":bool(external_checker),
            "native_differential":compare_rust}


def run_resource(*, maximum_n=16,compare_rust=False,external_checker=None):
    if maximum_n%2 or not 4<=maximum_n<=16:
        raise ValueError("resource maximum_n outside bounded even domain")
    if external_checker is not None:
        external_checker=find_drat_trim(external_checker)
        if external_checker is None:
            raise ValueError("requested external checker unavailable")
    rows=[measure_cap(n,compare_rust=compare_rust,external_checker=external_checker)
          for n in range(4,maximum_n+1,2)]
    return {"status":"BOUNDED_GF2_CAPS_PASSED_NOT_GENERAL_SOLVER",
            "external_drat_verification_performed":external_checker is not None,
            "native_differential_performed":compare_rust,"rows":rows}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-n",type=int,default=16)
    parser.add_argument("--compare-rust",action="store_true")
    parser.add_argument("--drat-trim")
    args=parser.parse_args()
    print(json.dumps(run_resource(maximum_n=args.max_n,
        compare_rust=args.compare_rust,external_checker=args.drat_trim),sort_keys=True))


if __name__=="__main__":
    main()
