"""Exact Fourier moments of source-bound nonlinear residual SAT solutions.

This is a bounded-width factor-elimination *oracle*, not a new algorithm:
evaluate sum_{x in SAT(residual)} (-1)^(m dot x) exactly and compare it with
independently verified parity rows that follow from the original full CNF.
The hypothesis is that the original parity RHS values align with unusually
biased moments. No holdout file may enter this experiment.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter

from scripts.benchmark_real_satlib_parity_gate import fetch_file
from scripts.experiment_satlib_affine_quotient import FIXED_SHA
from scripts.experiment_satlib_residual_geometry import (
    _minfill_upper_bound, exact_bounded_width_count,
)
from witnora_core.cnf import CNFFormula
from witnora_core.xor import detect_cnf_xor_patterns


def _bits(mask):
    while mask:
        lowest = mask & -mask
        yield lowest.bit_length()  # source variable ID (one-indexed)
        mask ^= lowest


def source_residual_parity_rows(clauses, nvars, *, return_source_equations=False):
    """Eliminate XOR-only variables *first* to expose residual-only rows.

    Each output row follows by GF(2) row additions from exact source clauses.
    No guessed or manually specified parity equation is used.
    """
    formula = CNFFormula(clauses)
    detected = detect_cnf_xor_patterns(formula)
    eqs = [eq for eq in detected.equations if eq.safe_use and eq.exact_full_encoding]
    source = {tuple(c) for eq in eqs for c in eq.source_clauses}
    residual = [tuple(c.literals) for c in formula.clauses if c.literals not in source]
    resvars = {abs(lit) for clause in residual for lit in clause}
    priority = {v: (int(v not in resvars), v) for v in range(1, nvars + 1)}
    pivots = {}
    for eq in eqs:
        mask = 0
        for v in eq.variables:
            mask ^= 1 << (v - 1)
        rhs = eq.rhs
        while mask:
            pivot = max(_bits(mask), key=priority.__getitem__)
            if pivot not in pivots:
                pivots[pivot] = (mask, rhs)
                break
            old_mask, old_rhs = pivots[pivot]
            mask ^= old_mask
            rhs ^= old_rhs
        else:
            if rhs:
                raise AssertionError("contradictory exact source XOR system")
    rows = []
    for pivot in sorted(pivots):
        if pivot not in resvars:
            continue
        mask, rhs = pivots[pivot]
        if any(v not in resvars for v in _bits(mask)):
            raise AssertionError("residual row not fully projected")
        rows.append((mask, rhs))
    rows.sort(key=lambda pair: (pair[0].bit_count(), pair[0], pair[1]))
    info = {
        "full_source_xor_rows": len(eqs),
        "independent_xor_rank": len(pivots),
        "residual_only_parity_row_count": len(rows),
        "residual_parity_row_width_histogram": dict(sorted(Counter(
            mask.bit_count() for mask, _ in rows).items())),
        "residual_variables": len(resvars),
    }
    if return_source_equations:
        return (residual, tuple(sorted(resvars)), rows, info,
                tuple((tuple(eq.variables), eq.rhs) for eq in eqs))
    return residual, tuple(sorted(resvars)), rows, info


def exact_parity_row_compatibility(residual, variables, order, mask, rhs,
                                    *, total_count=None):
    """Exact compatible-model count for a residual-only parity requirement."""
    if any(v not in variables for v in _bits(mask)):
        raise ValueError("parity row references a non-residual variable")
    if rhs not in (0, 1):
        raise ValueError("invalid source parity RHS")
    if total_count is None:
        total_count, _ = exact_bounded_width_count(residual, variables, order)
    signed, scope = exact_bounded_width_count(residual, variables, order,
                                               parity_variables=tuple(_bits(mask)))
    count_plus = total_count + (1 if rhs == 0 else -1) * signed
    if count_plus & 1 or count_plus < 0 or count_plus > 2 * total_count:
        raise AssertionError("inconsistent integer Fourier identity")
    compatible = count_plus // 2
    return {"row_width": mask.bit_count(), "rhs": rhs,
            "satisfied_residual_models": str(compatible),
            "residual_model_compatibility_fraction": round(compatible / total_count, 8)
                if total_count else None,
            "exact_signed_fourier_moment": str(signed),
            "max_factor_scope": scope}


def analyze(clauses, nvars, max_rows=32):
    if not (1 <= max_rows <= 218):
        raise ValueError("row sample must have 1..218 members")
    residual, variables, rows, info = source_residual_parity_rows(clauses, nvars)
    structural = _minfill_upper_bound(
        variables, [tuple(abs(lit) for lit in clause) for clause in residual],
        include_order=True)
    if structural["minfill_upper_bound_width"] > 4:
        raise ValueError("the bounded-width oracle is not authorized for larger widths")
    total, scope = exact_bounded_width_count(residual, variables,
                                             structural["elimination_order"])
    results = []
    for mask, rhs in rows[:max_rows]:
        entry = exact_parity_row_compatibility(
            residual, variables, structural["elimination_order"], mask, rhs,
            total_count=total)
        if not int(entry["satisfied_residual_models"]):
            # The complete original source is SAT. Such a row would reveal
            # a bug in our derivation or counting algorithm.
            raise AssertionError("SAT source has impossible implied parity row")
        results.append(entry)
    fractions = [x["residual_model_compatibility_fraction"] for x in results]
    return {"source": info, "oracle_width_bound": structural["minfill_upper_bound_width"],
            "exact_residual_models": str(total), "count_factor_max_scope": scope,
            "selection_rule": "shortest rows first, mask ascending; no RHS tuning",
            "rows_scored": len(results),
            "minimum_row_compatibility_fraction": min(fractions, default=None),
            "maximum_row_compatibility_fraction": max(fractions, default=None),
            "near_deterministic_rows": sum(x < 0.01 or x > 0.99 for x in fractions),
            "rows": results}


def benchmark(name="par32-1-c.cnf.Z", max_rows=32):
    if name not in FIXED_SHA:
        raise ValueError("holdout locked")
    source = fetch_file(name, True)
    if source["dimacs_sha256"] != FIXED_SHA[name]:
        raise AssertionError("source changed")
    return {"benchmark": name, "source_sha": source["dimacs_sha256"],
            "result": analyze(source["clause_lists"], source["variables"],
                              max_rows=max_rows)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-rows", type=int, default=32)
    args = parser.parse_args()
    print(json.dumps(benchmark(max_rows=args.max_rows), indent=2))
