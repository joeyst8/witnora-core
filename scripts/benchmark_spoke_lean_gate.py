"""Measure *real* Lean source-certificate verification, including failures.

CSV fields distinguish detection/construction time from total gate time.
No mocked subprocesses or trusted Python status fields are used.
Run after 'lake build' in formal/:
  PYTHONPATH=. python scripts/benchmark_spoke_lean_gate.py --sizes 3 5 9 25 --timeout 45
A timeout or rejection is reported as a failed data point, never hidden.
"""
from __future__ import annotations

import argparse
import csv
import platform
import sys
from time import perf_counter

from witnora_core.spoke_collapse import make_spoke_family
from witnora_core.spoke_discovery import (
    discover_parity_spoke_conflicts,
    extract_binary_xor_equations,
    extract_spoke_paths,
)
from witnora_core.lean_spoke_gate import verify_discovered_spoke_with_lean


def benchmark(sizes: list[int], timeout: int):
    writer = csv.DictWriter(sys.stdout, fieldnames=[
        "spokes", "variables", "clauses", "binary_equations", "paths",
        "proposals", "discovery_seconds", "lean_gate_seconds",
        "verified", "status", "reason", "proof_source_sha256",
    ])
    print("# " + platform.platform(), flush=True)
    writer.writeheader()
    results = []
    for count in sizes:
        formula, _ = make_spoke_family(count, contradictory=True)
        raw = formula.to_clause_lists()
        tokens = [v for clause in raw for v in (*clause, 0)]
        start = perf_counter()
        edges = extract_binary_xor_equations(formula)
        paths = extract_spoke_paths(formula)
        proposals = discover_parity_spoke_conflicts(formula)
        discovery_seconds = perf_counter() - start
        start = perf_counter()
        result = verify_discovered_spoke_with_lean(
            formula, raw_clauses=raw, source_tokens=tokens,
            source_text=formula.canonical_dimacs(), timeout_seconds=timeout,
        )
        lean_seconds = perf_counter() - start
        row = dict(
            spokes=count, variables=len(formula.variables),
            clauses=formula.num_clauses, binary_equations=len(edges),
            paths=len(paths), proposals=len(proposals),
            discovery_seconds=f"{discovery_seconds:.6f}",
            lean_gate_seconds=f"{lean_seconds:.6f}",
            verified=result.get("verified", False),
            status=result.get("lean_formal_status", ""),
            reason=result.get("reason", "") + (
                ": " + str(result.get("detail", ""))[:100]
                if not result.get("verified", False) else ""
            ),
            proof_source_sha256=result.get("proof_source_sha256", ""),
        )
        results.append(row)
        writer.writerow(row)
        sys.stdout.flush()
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", nargs="+", type=int, default=[3, 5, 9, 25])
    parser.add_argument("--timeout", type=int, default=45)
    parser.add_argument("--require-small-pass", action="store_true")
    args = parser.parse_args()
    if args.timeout <= 0 or any(n < 2 for n in args.sizes):
        parser.error("positive timeout and at least two spokes required")
    rows = benchmark(args.sizes, args.timeout)
    if args.require_small_pass and not rows[0]["verified"]:
        raise SystemExit("small-instance Lean gate failed")


if __name__ == "__main__":
    main()
