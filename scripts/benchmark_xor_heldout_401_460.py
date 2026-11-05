"""Bounded heldout SAT/XOR backgrounds, disconnected components, and GF(2) rank.

Research-only diagnostics. Every UNSAT proof is checked against the unchanged
original CNF by RUP and optionally a separately compiled external DRAT checker.
"""

from __future__ import annotations

import argparse
from itertools import product
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


def _base(seed: int, *, n: int, rows: int, contradictory: bool):
    for candidate in range(seed, seed + 100):
        try:
            return parity_hypergraph(candidate, n=n, rows=rows,
                                     contradictory=contradictory), candidate
        except ValueError as exc:
            if "degenerate hypergraph seed" not in str(exc) and "closure width cap" not in str(exc):
                raise
    raise ValueError("unable to generate a nondegenerate heldout instance")


def _model(formula: CNFFormula):
    """Independent original-clause truth table; only for at most 12 variables."""
    variables = formula.variables
    if len(variables) > 12:
        raise ValueError("original-CNF model search cap exceeded")
    for bits in product((False, True), repeat=len(variables)):
        assignment = dict(zip(variables, bits))
        if all(any(assignment[abs(lit)] == (lit > 0) for lit in clause)
               for clause in formula.clauses):
            return assignment
    return None


def background_instance(seed: int, *, contradictory: bool):
    """Plant satisfiable nonlinear clauses on and beyond the XOR support."""
    (base, equations), used_seed = _base(seed, n=6, rows=6,
                                         contradictory=contradictory)
    rng = random.Random(seed ^ 0x401420)
    model = _model(base) if not contradictory else None
    if not contradictory and model is None:
        raise AssertionError("SAT control has no model")
    planted = {**{v: bool(rng.randrange(2)) for v in range(1, 11)},
               **(model or {})}
    clauses = base.to_clause_lists()
    nonlinear = []
    for index in range(12):
        pool = list(range(1, 7)) if index % 3 == 0 else list(range(1, 11))
        support = rng.sample(pool, 2 + index % 2)
        literals = [v if rng.randrange(2) else -v for v in support]
        if not contradictory and not any(planted[abs(lit)] == (lit > 0) for lit in literals):
            v = abs(literals[0])
            literals[0] = v if planted[v] else -v
        nonlinear.append(literals)
    nonlinear.append([10 if planted[10] else -10] if not contradictory else [10])
    rng.shuffle(nonlinear)
    clauses.extend(nonlinear)
    rng.shuffle(clauses)
    return CNFFormula(clauses), equations, {"source_seed": used_seed,
                                           "background_clauses": len(nonlinear)}


def disconnected_instance(seed: int, *, contradictory_components: tuple[bool, ...]):
    """At most three independent 3-variable planted components."""
    if not 1 <= len(contradictory_components) <= 3:
        raise ValueError("component cap exceeded")
    equations = []
    source_seeds = []
    for component, contradictory in enumerate(contradictory_components):
        (_, part), source_seed = _base(seed + 71 * component, n=3, rows=3,
                                       contradictory=contradictory)
        shift = 3 * component
        for equation in part:
            support = [v + shift for v in equation.variables]
            equations.append(XorEquation(support, equation.rhs,
                source_clauses=canonical_xor_cnf_clauses(support, equation.rhs)))
        source_seeds.append(source_seed)
    formula = CNFFormula(c for eq in equations for c in eq.source_clauses)
    return formula, equations, {"source_seeds": source_seeds,
                               "components": len(contradictory_components)}


def gaussian_dependency_baseline(equations: list[XorEquation], *, max_variables=16):
    """Independent augmented-matrix row rank and inconsistency baseline."""
    variables = sorted({v for eq in equations for v in eq.variables})
    if len(variables) > max_variables:
        raise ValueError("Gaussian baseline variable cap exceeded")
    bit = {v: 1 << index for index, v in enumerate(variables)}
    pivots = {}
    augmented_pivots = {}
    contradiction = False
    for equation in equations:
        mask = 0
        for v in equation.variables:
            mask ^= bit[v]
        row = mask
        while row:
            pivot = row.bit_length() - 1
            if pivot not in pivots:
                pivots[pivot] = row
                break
            row ^= pivots[pivot]
        combined = (mask << 1) | equation.rhs
        while combined:
            pivot = combined.bit_length() - 1
            if pivot not in augmented_pivots:
                augmented_pivots[pivot] = combined
                break
            combined ^= augmented_pivots[pivot]
    contradiction = len(augmented_pivots) > len(pivots)
    return {"coefficient_rank": len(pivots),
            "augmented_rank": len(augmented_pivots),
            "unsatisfiable": contradiction,
            "theoretical_states": 1 << len(augmented_pivots)}


def evaluate_heldout(seed: int, *, family: str, contradictory: bool = True,
                     components: tuple[bool, ...] = (False, True, False),
                     compare_rust=False, external_checker=None):
    if family == "background":
        formula, equations, metadata = background_instance(seed, contradictory=contradictory)
    elif family == "components":
        formula, equations, metadata = disconnected_instance(
            seed, contradictory_components=components)
        contradictory = any(components)
    else:
        raise ValueError("unknown heldout family")
    witness, states = shortest_inconsistent_subset(equations)
    oracle = exhaustive_inconsistent_subset(equations, max_rows=16)
    gaussian = gaussian_dependency_baseline(equations)
    if witness != oracle or bool(witness is not None) != gaussian["unsatisfiable"]:
        raise AssertionError("independent GF2 oracles disagree")
    if states["reachable_states"] != gaussian["theoretical_states"]:
        raise AssertionError("syndrome-state count disagrees with augmented rank")
    if exhaustive_sat(formula) == contradictory:
        raise AssertionError("original-CNF SAT truth-table result disagrees")
    proof = None
    proof_clauses = 0
    if contradictory:
        validate_witness_against_original(formula, equations, witness)
        selected = [equations[i] for i in witness]
        trace = _sparse_xor_elimination_schedule(selected)["row_operation_trace"]
        options = dict(max_proof_clauses=10000, max_proof_bytes=200000,
                       timeout_seconds=15)
        candidate = _row_trace_refutation(formula, selected, trace,
                                          backend="python", **options)
        if compare_rust and _row_trace_refutation(formula, selected, trace,
                             backend="rust", **options) != candidate:
            raise AssertionError("Rust and Python proof candidates differ")
        proof, error, proof_stats = candidate
        if error or not proof or not check_drat_text(formula, proof)["verified"]:
            raise AssertionError(f"original-CNF proof candidate not RUP: {error}")
        if external_checker and not _external_check(formula, proof, external_checker):
            raise AssertionError("external checker rejected original-CNF proof")
        proof_clauses = proof_stats["proof_clause_count_actual"]
    return {"family": family, "seed": seed, "unsatisfiable": contradictory,
            "witness": list(witness) if witness else None,
            "original_clauses": formula.num_clauses,
            "proof_clauses": proof_clauses,
            "external_verified": bool(proof and external_checker),
            "native_differential": compare_rust,
            **metadata, **states, **gaussian}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=16)
    parser.add_argument("--compare-rust", action="store_true")
    parser.add_argument("--drat-trim")
    args = parser.parse_args()
    if not 1 <= args.samples <= 64:
        raise ValueError("bounded heldout sample cap exceeded")
    checker = find_drat_trim(args.drat_trim) if args.drat_trim else None
    if args.drat_trim and not checker:
        raise ValueError("requested independent checker missing")
    results = []
    for seed in range(401000, 401000 + args.samples):
        for contradictory in (False, True):
            results.append(evaluate_heldout(seed, family="background",
                contradictory=contradictory, compare_rust=args.compare_rust,
                external_checker=checker))
        for components in ((False, False), (False, True), (True, True),
                           (False, True, False)):
            results.append(evaluate_heldout(seed, family="components",
                components=components, compare_rust=args.compare_rust,
                external_checker=checker))
    print(json.dumps({"status": "HELDOUT_ORIGINAL_CNF_PROOFS_NOT_GENERAL_SAT_THEOREM",
        "cases": len(results), "unsat": sum(r["unsatisfiable"] for r in results),
        "max_augmented_rank": max(r["augmented_rank"] for r in results),
        "external_checker_used": bool(checker),
        "native_differential_used": args.compare_rust}, sort_keys=True))


if __name__ == "__main__":
    main()
