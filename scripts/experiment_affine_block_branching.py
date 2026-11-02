"""Costed comparison: one-clause versus two-clause affine-space branching.

The pair operator forms disjoint intersections of two clause-branch covers.
It is a research control, not a claim of a novel solver or SATLIB result.
"""
from __future__ import annotations

from itertools import combinations
from statistics import mean, median
from time import perf_counter

from scripts.experiment_affine_dimension_diagnostic import (
    disjoint_clause_branches, gf2_dimension, synthetic_instance,
)


def two_clause_branches(nvars, rows, first, second):
    """Disjoint cover of assignments satisfying both clauses."""
    return [branch for left, _ in disjoint_clause_branches(nvars, rows, first)
            for branch in disjoint_clause_branches(nvars, left, second)]


def measure_candidate(nvars, rows, clauses, *, pair=False, pool=6):
    """Return exact surviving model count, largest-branch dimension, work."""
    start = perf_counter()
    dimension = gf2_dimension(nvars, rows)
    if dimension is None:
        return None
    evaluated = []
    for clause in clauses:
        children = disjoint_clause_branches(nvars, rows, clause)
        models = sum(1 << dim for _, dim in children)
        if models < 1 << dimension:
            evaluated.append((models, tuple(clause), children))
    evaluated.sort(key=lambda item: (item[0], item[1]))
    if not evaluated:
        return None

    if pair:
        best = None
        for left, right in combinations(evaluated[:pool], 2):
            children = two_clause_branches(nvars, rows, left[1], right[1])
            models = sum(1 << dim for _, dim in children)
            key = (models, left[1], right[1])
            if best is None or key < best[0]:
                best = (key, children)
        if best is None:
            return None
        children = best[1]
    else:
        children = evaluated[0][2]

    models = sum(1 << dim for _, dim in children)
    return {
        "initial_models": 1 << dimension,
        "surviving_models": models,
        "largest_branch_dimension": max(dim for _, dim in children) if children else None,
        "branch_count": len(children),
        "elapsed_ms": (perf_counter() - start) * 1000,
    }


def run(seeds=8, repeats=5):
    if not 1 <= seeds <= 32 or not 1 <= repeats <= 20:
        raise ValueError("invalid experiment budget")
    records = []
    for nvars in (16, 32):
        for seed in range(seeds):
            rows, clauses = synthetic_instance(nvars, seed)
            single, paired = [], []
            for i in range(repeats):
                order = (False, True) if i % 2 == 0 else (True, False)
                for pair in order:
                    outcome = measure_candidate(nvars, rows, clauses, pair=pair)
                    (paired if pair else single).append(outcome)
            def outcome_without_timing(outcome):
                return {k: v for k, v in outcome.items() if k != "elapsed_ms"}

            assert all(outcome_without_timing(x) == outcome_without_timing(single[0])
                       for x in single)
            assert all(outcome_without_timing(x) == outcome_without_timing(paired[0])
                       for x in paired)
            records.append({
                "nvars": nvars, "seed": seed,
                "single": {**single[0], "elapsed_ms": median(x["elapsed_ms"] for x in single)},
                "paired": {**paired[0], "elapsed_ms": median(x["elapsed_ms"] for x in paired)},
            })
    return {
        "status": "SYNTHETIC_OPERATOR_COST_TEST_NOT_SATLIB",
        "by_size": [{
            "nvars": nvars,
            "single_models": mean(x["single"]["surviving_models"] for x in records
                                  if x["nvars"] == nvars),
            "paired_models": mean(x["paired"]["surviving_models"] for x in records
                                  if x["nvars"] == nvars),
            "single_branches": mean(x["single"]["branch_count"] for x in records
                                    if x["nvars"] == nvars),
            "paired_branches": mean(x["paired"]["branch_count"] for x in records
                                    if x["nvars"] == nvars),
            "single_ms": mean(x["single"]["elapsed_ms"] for x in records
                              if x["nvars"] == nvars),
            "paired_ms": mean(x["paired"]["elapsed_ms"] for x in records
                              if x["nvars"] == nvars),
        } for nvars in (16, 32)],
        "records": records,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2))
