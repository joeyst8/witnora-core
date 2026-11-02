"""Bounded affine/CNF two-clause UNSAT screen (experimental, sound only).

If every disjoint affine-consistent branch satisfying a selected clause pair
is eliminated, the original affine rows plus CNF are UNSAT. Failure to find
a contradiction says UNKNOWN, never SAT.
"""
from __future__ import annotations

from itertools import combinations
from random import Random
from statistics import mean
from time import perf_counter

from scripts.experiment_affine_block_branching import two_clause_branches
from scripts.experiment_affine_dimension_diagnostic import (
    disjoint_clause_branches, gf2_dimension, synthetic_instance,
)


def screen_pairs(nvars, rows, clauses, max_pairs=120):
    if max_pairs < 1:
        raise ValueError("pair work budget must be positive")
    start = perf_counter()
    if gf2_dimension(nvars, rows) is None:
        return {"status": "UNSAT", "reason": "AFFINE_CONTRADICTION",
                "pairs_checked": 0, "elapsed_ms": (perf_counter() - start) * 1000}

    for i, clause in enumerate(clauses):
        if not disjoint_clause_branches(nvars, rows, clause):
            return {"status": "UNSAT", "reason": "SINGLE_CLAUSE_CONFLICT",
                    "source_indices": [i], "pairs_checked": 0,
                    "elapsed_ms": (perf_counter() - start) * 1000}

    trials = 0
    for i, j in combinations(range(len(clauses)), 2):
        if trials >= max_pairs:
            break
        trials += 1
        if not two_clause_branches(nvars, rows, clauses[i], clauses[j]):
            return {"status": "UNSAT", "reason": "PAIR_AFFINE_CONTRADICTION",
                    "source_indices": [i, j], "pairs_checked": trials,
                    "elapsed_ms": (perf_counter() - start) * 1000}
    return {"status": "UNKNOWN", "pairs_checked": trials,
            "elapsed_ms": (perf_counter() - start) * 1000}


def selective_screen_pairs(nvars, rows, clauses, max_pairs=120):
    """Sound but incomplete: inspect only pairs matching small affine support."""
    if max_pairs < 1:
        raise ValueError("pair work budget must be positive")
    start = perf_counter()
    if gf2_dimension(nvars, rows) is None:
        return {"status": "UNSAT", "reason": "AFFINE_CONTRADICTION",
                "pairs_checked": 0, "elapsed_ms": (perf_counter() - start) * 1000}
    buckets = {}
    for i, clause in enumerate(clauses):
        buckets.setdefault(frozenset(abs(lit) for lit in clause), []).append(i)
    checked = set()
    trials = 0
    for mask, _ in rows:
        if not 2 <= mask.bit_count() <= 3:
            continue
        support = frozenset(v for v in range(1, nvars + 1)
                             if mask & (1 << (v - 1)))
        for i, j in combinations(buckets.get(support, ()), 2):
            if (i, j) in checked:
                continue
            checked.add((i, j))
            if trials >= max_pairs:
                return {"status": "UNKNOWN", "pairs_checked": trials,
                        "elapsed_ms": (perf_counter() - start) * 1000}
            trials += 1
            if not two_clause_branches(nvars, rows, clauses[i], clauses[j]):
                return {"status": "UNSAT", "reason": "SELECTIVE_PAIR_CONTRADICTION",
                        "source_indices": [i, j], "pairs_checked": trials,
                        "elapsed_ms": (perf_counter() - start) * 1000}
    return {"status": "UNKNOWN", "pairs_checked": trials,
            "elapsed_ms": (perf_counter() - start) * 1000}


def controlled_instance(nvars, seed, kind):
    """Source rows represent x1 xor x2 = 0 plus independent distractors."""
    rng = Random(63126 + 100 * nvars + seed)
    planted = {v: rng.randrange(2) for v in range(3, nvars + 1)}
    rows = [(0b11, 0)]
    for _ in range(nvars // 4):
        variables = rng.sample(range(3, nvars + 1), 3)
        rows.append((sum(1 << (v - 1) for v in variables),
                     sum(planted[v] for v in variables) % 2))
    if kind == "unsat_pair":
        clauses = [(1, 2), (-1, -2)]
    elif kind == "sat_control":
        clauses = [(1, 2), (1, -2)]
    else:
        raise ValueError("unknown controlled family")
    for _ in range(nvars // 2):
        variables = rng.sample(range(3, nvars + 1), 3)
        clause = [v if rng.randrange(2) else -v for v in variables]
        if not any((lit > 0) == bool(planted[abs(lit)]) for lit in clause):
            clause[0] = -clause[0]
        clauses.append(tuple(clause))
    return tuple(rows), tuple(clauses)


def run(seeds=8, max_pairs=120):
    if not 1 <= seeds <= 32:
        raise ValueError("invalid seed budget")
    records = []
    for nvars in (16, 32):
        for seed in range(seeds):
            for kind in ("unsat_pair", "sat_control", "planted_ood"):
                if kind == "planted_ood":
                    rows, clauses = synthetic_instance(nvars, seed)
                else:
                    rows, clauses = controlled_instance(nvars, seed, kind)
                result = screen_pairs(nvars, rows, clauses, max_pairs=max_pairs)
                selective = selective_screen_pairs(
                    nvars, rows, clauses, max_pairs=max_pairs)
                records.append({"nvars": nvars, "seed": seed, "family": kind,
                                **result, "selective": selective})
    return {"status": "BOUNDED_CONDITIONAL_UNSAT_SCREEN_NOT_SOLVER",
            "summary": {
                "cases": len(records),
                "targeted_pair_detected": sum(r["family"] == "unsat_pair" and
                                              r["reason"] == "PAIR_AFFINE_CONTRADICTION"
                                              for r in records if "reason" in r),
                "sat_control_false_unsat": sum(r["family"] == "sat_control" and
                                                 r["status"] == "UNSAT" for r in records),
                "mean_unknown_check_ms": mean(r["elapsed_ms"] for r in records
                                               if r["status"] == "UNKNOWN"),
                "selective_targeted_detected": sum(
                    r["family"] == "unsat_pair" and
                    r["selective"]["status"] == "UNSAT" for r in records),
                "selective_mean_unknown_ms": mean(
                    r["selective"]["elapsed_ms"] for r in records
                    if r["selective"]["status"] == "UNKNOWN"),
            },
            "records": records}


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2))
