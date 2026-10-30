"""End-to-end opt-in parity compression benchmark including all Lean gate time.

The solver backend is Glucose3 in both arms. Baseline solves the original
CNF; compressed arm checks original-document Lean correspondence, extracts
and rewrites, checks canonical residual, then solves the residual. This is a
single-run exploratory timing, not publication-quality speed evidence.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from statistics import median
from time import perf_counter

from witnora_core.cnf import CNFFormula
from witnora_core.verified_compression_pipeline import (
    _glucose, solve_with_verified_compression,
)
from witnora_core.xor import canonical_xor_cnf_clauses


def make_connected_case(n: int) -> CNFFormula:
    if n < 3:
        raise ValueError("minimum n=3")
    clauses = set()
    for u in range(1, n):
        clauses.update(canonical_xor_cnf_clauses((u, u + 1), u % 2))
    clauses.add((n, n + 1, -(n + 2)))
    return CNFFormula.from_raw_clauses(clauses)


def run_benchmark(sizes=(3, 5), repeats=3, timeout=30):
    records = []
    for n in sizes:
        formula = make_connected_case(n)
        raw = formula.to_clause_lists()
        tokens = [v for row in raw for v in (*row, 0)]
        original_times = []
        baseline = None
        for _ in range(repeats):
            start = perf_counter()
            outcome = _glucose(formula)
            original_times.append(perf_counter() - start)
            baseline = outcome["status"]
        guarded = solve_with_verified_compression(
            formula, raw_clauses=raw, source_tokens=tokens,
            source_spellings=list(map(str, tokens)),
            source_text=formula.canonical_dimacs(),
            timeout_seconds=timeout,
        )
        if guarded["status"] != baseline:
            raise AssertionError("compressed solving disagrees with original solver")
        records.append({
            "xor_vertices": n,
            "original_variables": len(formula.variables),
            "original_clauses": formula.num_clauses,
            "source_sha256": formula.formula_hash,
            "original_solver_median_seconds": median(original_times),
            "guarded_gate_seconds": guarded["gate_seconds"],
            "guarded_residual_solve_seconds": guarded["solve_seconds"],
            "guarded_total_seconds": guarded["gate_seconds"] + guarded["solve_seconds"],
            "used_compression": guarded["used_compression"],
            "equivalence_kernel_verified": guarded["compression_proof_verified"],
            "unsat_kernel_verified": guarded["unsat_kernel_verified"],
            "status": guarded["status"],
            "trials": repeats,
            "lean_timeout_seconds": timeout,
        })
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", type=int, nargs="+", default=[3, 5])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--output", type=Path, default=Path("verified-compression-benchmark.csv"))
    parser.add_argument("--require-small-pass", action="store_true")
    args = parser.parse_args()
    data = run_benchmark(args.sizes, args.repeats, args.timeout)
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(data[0]))
        writer.writeheader()
        writer.writerows(data)
    for entry in data:
        print(entry)
    if args.require_small_pass and not (data[0]["used_compression"] and
                                       data[0]["equivalence_kernel_verified"]):
        raise AssertionError("small supported source-bound compression did not verify")


if __name__ == "__main__":
    main()
