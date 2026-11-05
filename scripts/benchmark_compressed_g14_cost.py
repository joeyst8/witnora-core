"""Measured Glucose3 baseline vs complete compressed G14 kernel-verification cost.

These small samples measure proof overhead; they are not competitive solver
rankings and do not establish a speedup.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from time import perf_counter

from witnora_core.cnf import CNFFormula
from witnora_core.lean_compressed_g14_gate import verify_compressed_g14_with_lean
from witnora_core.parity_compression import (
    compress_binary_xor_components, substitute_residual_formula,
)
from witnora_core.separator_affine_family_theorem import (
    build_separator_affine_certificate, make_separator_affine_instance,
)
from witnora_core.xor import canonical_xor_cnf_clauses


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", type=int, nargs="+", default=[2, 3])
    parser.add_argument("--output", default="compressed-g14-cost.csv")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args(argv)
    from pysat.solvers import Glucose3

    observations = []
    for n in args.sizes:
        base = make_separator_affine_instance(f"saf_unsat_cover_{n}")
        original = CNFFormula.from_raw_clauses(
            base.formula.to_clause_lists() +
            list(canonical_xor_cnf_clauses((100, 101), 0))
        )
        start = perf_counter()
        with Glucose3(bootstrap_with=original.to_clause_lists()) as solver:
            oracle_unsat = not solver.solve()
        glucose_seconds = perf_counter() - start
        start = perf_counter()
        candidate = compress_binary_xor_components(original)
        residual = substitute_residual_formula(original, candidate)
        certificate = build_separator_affine_certificate(
            replace(base, formula=residual, instance_id=f"cost_g14_{n}")
        )
        certificate_seconds = perf_counter() - start
        raw = original.to_clause_lists()
        tokens = [lit for clause in raw for lit in (*clause, 0)]
        start = perf_counter()
        result = verify_compressed_g14_with_lean(
            original, certificate, raw_clauses=raw,
            source_tokens=tokens, source_spellings=list(map(str, tokens)),
            source_text=original.canonical_dimacs(),
            timeout_seconds=args.timeout,
        )
        lean_seconds = perf_counter() - start
        if not oracle_unsat or not result.get("original_unsat_kernel_verified"):
            raise AssertionError(f"baseline / Lean mismatch: {result}")
        observations.append(dict(
            family="saf_unsat_cover",
            n=n,
            original_variables=len(original.variables),
            original_clauses=original.num_clauses,
            residual_variables=len(residual.variables),
            residual_clauses=residual.num_clauses,
            original_dimacs_sha256=sha256(original.canonical_dimacs().encode()).hexdigest(),
            glucose3_seconds=round(glucose_seconds, 6),
            candidate_and_native_certificate_seconds=round(certificate_seconds, 6),
            complete_lean_g14_seconds=round(lean_seconds, 6),
            complete_verified_seconds=round(certificate_seconds + lean_seconds, 6),
            lean_kernel_verified=1,
            repeats=1,
        ))
        print(observations[-1])
    output = Path(args.output)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(observations[0]))
        writer.writeheader()
        writer.writerows(observations)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
