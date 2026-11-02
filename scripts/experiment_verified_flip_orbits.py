"""Draft: source-bound CNF sign-flip symmetry and assignment orbit quotient.

Uses detected exact XOR rows only to *propose* flip masks. Each candidate is
accepted only if it maps the full original CNF clause set bijectively onto
itself. Tested independent generators form a group under bitwise XOR.
This is known SAT symmetry reduction, not a new algorithm or solver.
"""
from __future__ import annotations

from random import Random
from statistics import median
from time import perf_counter

from pysat.solvers import Minisat22
from witnora_core.cnf import CNFFormula
from witnora_core.xor import canonical_xor_cnf_clauses, detect_cnf_xor_patterns


def kernel_basis(masks, nvars):
    pivots = {}
    for source in masks:
        row = source
        while row:
            p = row.bit_length() - 1
            if p in pivots:
                row ^= pivots[p]
            else:
                pivots[p] = row
                break
    vectors = []
    for free in range(nvars):
        if free in pivots:
            continue
        vector = 1 << free
        for pivot in sorted(pivots):
            if (vector & pivots[pivot]).bit_count() & 1:
                vector ^= 1 << pivot
        if any((vector & row).bit_count() & 1 for row in masks):
            raise AssertionError("kernel calculation failed")
        vectors.append(vector)
    return tuple(vectors)


def verified_flip(formula, mask):
    if not mask or mask >> formula.max_var:
        return False
    source = {tuple(c.literals) for c in formula.clauses}
    transformed = {
        tuple(sorted(-lit if mask & (1 << (abs(lit) - 1)) else lit for lit in clause))
        for clause in source
    }
    return transformed == source


def independent_pivots(vectors):
    pivots = {}
    for vector in vectors:
        row = vector
        while row:
            pivot = row.bit_length() - 1
            if pivot in pivots:
                row ^= pivots[pivot]
            else:
                pivots[pivot] = row
                break
    return pivots


def discover(formula, *, max_candidate_span=1 << 12, require_source_rows=False):
    equations = detect_cnf_xor_patterns(formula, max_k=3).equations
    masks = tuple(sum(1 << (v - 1) for v in eq.variables)
                  for eq in equations if eq.exact_full_encoding and eq.safe_use)
    if require_source_rows and not masks:
        # Safe incomplete trigger: no expensive full-CNF sign-flip scan
        # without any exact source-bound XOR row as a candidate hint.
        return {"pivots": {}, "rank": 0, "source_rows": 0,
                "candidate_span_tested": 0, "accepted_mask_count": 0,
                "complete_candidate_span": False}
    kernel = kernel_basis(masks, formula.max_var)
    # Enumerate the entire small candidate span. For larger kernels use
    # only basis candidates (incomplete discovery, never unsound acceptance).
    if (1 << len(kernel)) <= max_candidate_span:
        candidates = []
        for subset in range(1, 1 << len(kernel)):
            mask = 0
            for i, gen in enumerate(kernel):
                if subset & (1 << i):
                    mask ^= gen
            candidates.append(mask)
    else:
        candidates = list(kernel)
    accepted = [m for m in candidates if verified_flip(formula, m)]
    pivots = independent_pivots(accepted)
    return {"pivots": pivots, "rank": len(pivots),
            "source_rows": len(masks), "candidate_span_tested": len(candidates),
            "accepted_mask_count": len(accepted),
            "complete_candidate_span": (1 << len(kernel)) <= max_candidate_span}


def canonical(assignment, pivots):
    value = assignment
    for bit in sorted(pivots, reverse=True):
        if value & (1 << bit):
            value ^= pivots[bit]
    return value


def satisfies(formula, assignment):
    return all(any(((assignment >> (abs(lit) - 1)) & 1) == int(lit > 0)
                   for lit in clause) for clause in formula.to_clause_lists())


def enumerate_search(formula, pivots=None):
    visited = 0
    for value in range(1 << formula.max_var):
        if pivots is not None and canonical(value, pivots) != value:
            continue
        visited += 1
        if satisfies(formula, value):
            return True, visited
    return False, visited


def make_case(nvars, seed, kind):
    rng = Random(7299 + 131 * nvars + seed)
    planted = {v: rng.randrange(2) for v in range(1, nvars + 1)}
    clauses = []
    if kind != "random_3sat":
        for v in range(1, nvars - 1, 2):
            support = (v, v + 1, v + 2)
            rhs = sum(planted[x] for x in support) % 2
            clauses.extend(canonical_xor_cnf_clauses(support, rhs))
    if kind == "xor_unsat":
        clauses.extend(((nvars,), (-nvars,)))
    elif kind == "partially_broken":
        clauses.append((nvars,))
    elif kind == "random_3sat":
        for _ in range(4 * nvars):
            support = rng.sample(range(1, nvars + 1), 3)
            clauses.append(tuple(v if rng.randrange(2) else -v for v in support))
    elif kind != "xor_sat":
        raise ValueError("invalid family")
    return CNFFormula.from_raw_clauses(clauses)


def benchmark(seeds=5, repeats=3):
    if not 1 <= seeds <= 20 or not 1 <= repeats <= 10:
        raise ValueError("invalid experiment budget")
    records = []
    for nvars in (10, 14):
        for seed in range(seeds):
            for kind in ("xor_sat", "xor_unsat", "partially_broken", "random_3sat"):
                f = make_case(nvars, seed, kind)
                with Minisat22(bootstrap_with=f.to_clause_lists()) as oracle:
                    truth = oracle.solve()
                checks = []
                mini_times = []
                for _ in range(repeats):
                    start = perf_counter()
                    plain, plain_visited = enumerate_search(f)
                    plain_ms = (perf_counter() - start) * 1000
                    start = perf_counter()
                    info = discover(f)
                    quot, quot_visited = enumerate_search(f, info["pivots"])
                    quot_ms = (perf_counter() - start) * 1000
                    if not (plain == quot == truth):
                        raise AssertionError((nvars, seed, kind, truth, plain, quot))
                    checks.append((plain_ms, quot_ms))
                    start = perf_counter()
                    with Minisat22(bootstrap_with=f.to_clause_lists()) as native:
                        if native.solve() != truth:
                            raise AssertionError("native MiniSat answer changed")
                    mini_times.append((perf_counter() - start) * 1000)
                records.append({"nvars": nvars, "seed": seed, "family": kind,
                                "sat": truth, "rank": info["rank"],
                                "source_rows": info["source_rows"],
                                "candidate_span_tested": info["candidate_span_tested"],
                                "plain_visits": plain_visited, "quotient_visits": quot_visited,
                                "plain_ms": median(t[0] for t in checks),
                                "quotient_ms": median(t[1] for t in checks),
                                "minisat_ms": median(mini_times)})
    return {"summary": {"cases": len(records), "all_answers_match_minisat": True,
                        "positive_rank_cases": sum(r["rank"] > 0 for r in records),
                        "quotient_visit_wins": sum(r["quotient_visits"] < r["plain_visits"] for r in records),
                        "quotient_time_wins": sum(r["quotient_ms"] < r["plain_ms"] for r in records),
                        "plain_total_visits": sum(r["plain_visits"] for r in records),
                        "quotient_total_visits": sum(r["quotient_visits"] for r in records),
                        "plain_total_ms": round(sum(r["plain_ms"] for r in records), 3),
                        "quotient_total_ms": round(sum(r["quotient_ms"] for r in records), 3),
                        "minisat_total_ms": round(sum(r["minisat_ms"] for r in records), 3)},
            "records": records}


if __name__ == "__main__":
    import json
    print(json.dumps(benchmark()["summary"], indent=2))
