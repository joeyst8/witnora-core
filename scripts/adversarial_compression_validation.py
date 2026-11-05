"""Adversarial parity-compression validation against independent SAT engines.

No Lean claim is issued here. The aim is to expose false XOR discovery,
wrong residual model lifts and deliberate structural blind spots.
"""
from __future__ import annotations

import argparse
import csv
from hashlib import sha256
from itertools import product
from pathlib import Path
import random
from time import perf_counter

from witnora_core.cnf import CNFFormula, formula_satisfied
from witnora_core.parity_compression import (
    compress_binary_xor_components, reconstruct_values,
    substitute_residual_formula,
)
from witnora_core.xor import canonical_xor_cnf_clauses


FAMILIES = (
    "consistent_with_3cnf",
    "contradictory_xor_cycle",
    "partial_xor_encoding",
    "non_xor_unit_contradiction",
    "random_satisfiable_3cnf",
)


def make_case(n, family, seed):
    rng = random.Random(seed * 1_000_003 + n * 101 + sum(map(ord, family)))
    values = {v: bool(rng.getrandbits(1)) for v in range(1, n + 1)}
    clauses = []
    if family != "random_satisfiable_3cnf":
        for u in range(1, n - 2):
            rhs = int(values[u] != values[u + 1])
            clauses.extend(canonical_xor_cnf_clauses((u, u + 1), rhs))
    if family == "contradictory_xor_cycle":
        rhs = int(values[1] != values[n - 2]) ^ 1
        clauses.extend(canonical_xor_cnf_clauses((1, n - 2), rhs))
    elif family == "partial_xor_encoding":
        # One of the two clauses needed to imply a binary XOR is missing.
        clauses.append((n - 1, n))
    elif family == "non_xor_unit_contradiction":
        clauses.extend(((n,), (-n,)))
    else:
        for _ in range(2 * n):
            variables = rng.sample(range(1, n + 1), 3)
            clause = [v if rng.getrandbits(1) else -v for v in variables]
            if not any((lit > 0) == values[abs(lit)] for lit in clause):
                clause[0] = variables[0] if values[variables[0]] else -variables[0]
            clauses.append(tuple(clause))
    return CNFFormula.from_raw_clauses(clauses)


def solve(formula, backend):
    from pysat.solvers import Glucose3, Minisat22
    cls = {"glucose3": Glucose3, "minisat22": Minisat22}[backend]
    with cls(bootstrap_with=formula.to_clause_lists()) as solver:
        satisfiable = bool(solver.solve())
        model = solver.get_model() if satisfiable else None
    assignment = {abs(lit): lit > 0 for lit in (model or [])}
    if satisfiable and not formula_satisfied(formula, assignment):
        raise AssertionError(f"{backend} returned an invalid SAT model")
    return satisfiable, assignment


def exhaustive_sat(formula):
    variables = formula.variables
    for bits in product((False, True), repeat=len(variables)):
        if formula_satisfied(formula, dict(zip(variables, bits))):
            return True
    return False


def benchmark(sizes, seeds):
    records = []
    for size in sizes:
        if size < 6 or size > 12:
            raise ValueError("exhaustive oracle supports sizes 6..12")
        for seed in seeds:
            for family in FAMILIES:
                formula = make_case(size, family, seed)
                start = perf_counter()
                g_sat, _ = solve(formula, "glucose3")
                m_sat, _ = solve(formula, "minisat22")
                brute_sat = exhaustive_sat(formula)
                oracle_seconds = perf_counter() - start
                if len({g_sat, m_sat, brute_sat}) != 1:
                    raise AssertionError(f"independent oracles disagree: {family} {size} {seed}")
                start = perf_counter()
                candidate = compress_binary_xor_components(formula)
                compression_seconds = perf_counter() - start
                inconsistent = candidate["status"] == "INCONSISTENT_XOR_EQUATIONS"
                if family == "partial_xor_encoding" and any(
                    {u, v} == {size - 1, size}
                    for u, v, _ in candidate.get("equations", [])
                ):
                    raise AssertionError("incomplete XOR clause pair was falsely recognized")
                if inconsistent != (family == "contradictory_xor_cycle"):
                    raise AssertionError(f"wrong structural conflict status: {family} {candidate}")
                residual = None
                residual_sat = None
                if not inconsistent:
                    residual = substitute_residual_formula(formula, candidate)
                    residual_sat, residual_model = solve(residual, "minisat22")
                    if residual_sat != g_sat:
                        raise AssertionError(f"residual changed SAT semantics: {family}")
                    if residual_sat:
                        roots = dict(candidate["roots"])
                        roots_values = {
                            root: int(residual_model.get(root, False))
                            for root in set(roots.values())
                        }
                        lifted = reconstruct_values(candidate, roots_values)
                        original_model = {
                            v: bool(lifted.get(v, residual_model.get(v, False)))
                            for v in formula.variables
                        }
                        if not formula_satisfied(formula, original_model):
                            raise AssertionError(f"model lift invalid: {family}")
                    if family == "random_satisfiable_3cnf" and candidate["root_variables_saved"] != 0:
                        raise AssertionError("spurious XOR compression in random 3-CNF")
                records.append({
                    "seed": seed, "size": size, "family": family,
                    "source_sha256": sha256(formula.canonical_dimacs().encode()).hexdigest(),
                    "original_clauses": formula.num_clauses,
                    "source_satisfiable": int(g_sat),
                    "minisat22_agrees": int(m_sat == g_sat),
                    "exhaustive_agrees": int(brute_sat == g_sat),
                    "compression_status": candidate["status"],
                    "root_variables_saved": candidate.get("root_variables_saved", 0),
                    "residual_satisfiable": "" if residual_sat is None else int(residual_sat),
                    "oracle_seconds": round(oracle_seconds, 6),
                    "compression_seconds": round(compression_seconds, 6),
                    "lean_checked": 0,
                })
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", type=int, nargs="+", default=[6, 10])
    parser.add_argument("--seeds", type=int, nargs="+", default=[7, 13, 29])
    parser.add_argument("--output", type=Path, default=Path("adversarial-compression.csv"))
    args = parser.parse_args()
    records = benchmark(args.sizes, args.seeds)
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    print({"cases": len(records), "families": FAMILIES, "output": str(args.output)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
