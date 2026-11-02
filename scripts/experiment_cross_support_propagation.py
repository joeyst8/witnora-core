"""Exploratory CNF-source-bound XOR elimination and DPLL unit propagation.

Exact 3-XOR patterns imply rows. XORing rows with overlapping supports can
produce 1- or 2-variable deductions. Propagation always retains source CNF.
Known Gaussian elimination / XOR reasoning, not a novelty claim.
"""
from __future__ import annotations

from collections import Counter
from random import Random
from statistics import median
from time import perf_counter

from pysat.solvers import Minisat22
from witnora_core.cnf import CNFFormula
from witnora_core.xor import canonical_xor_cnf_clauses, detect_cnf_xor_patterns
from scripts.experiment_inloop_masked_state import run_masked


def extract_rows(formula):
    system = detect_cnf_xor_patterns(formula, max_k=3)
    return tuple((sum(1 << (v - 1) for v in eq.variables), eq.rhs)
                 for eq in system.equations
                 if eq.exact_full_encoding and eq.safe_use)


def derive_small_rows(rows, max_rows=256):
    """Bounded pairwise GF(2) consequences; no invented source assumptions."""
    known = set(rows)
    derived = set()
    for i, (left, a) in enumerate(rows):
        for right, b in rows[i + 1:]:
            mask = left ^ right
            if mask.bit_count() <= 2 and mask:
                derived.add((mask, a ^ b))
                if len(derived) >= max_rows:
                    return tuple(sorted(known | derived))
    return tuple(sorted(known | derived))


def unit_affine(rows, assignment):
    """Derive implied literals, or contradiction, from XOR rows under a branch."""
    result = {}
    for mask, rhs in rows:
        remaining = mask
        for v, value in assignment.items():
            bit = 1 << (v - 1)
            if remaining & bit:
                remaining ^= bit
                rhs ^= int(value)
        if remaining == 0:
            if rhs:
                return None
        elif remaining.bit_count() == 1:
            v = remaining.bit_length()
            value = bool(rhs)
            if v in result and result[v] != value:
                return None
            result[v] = value
    return result


def simplify(clauses, assignment):
    output = []
    for clause in clauses:
        if any(abs(l) in assignment and (l > 0) == assignment[abs(l)] for l in clause):
            continue
        new = tuple(l for l in clause if abs(l) not in assignment)
        if not new:
            return None
        output.append(new)
    return tuple(output)


def solve(clauses, rows, counters, assignment=None):
    assignment = {} if assignment is None else assignment
    counters["nodes"] += 1
    while True:
        if not clauses:
            return True
        cnf_units = {abs(c[0]): c[0] > 0 for c in clauses if len(c) == 1}
        if any(len(c) == 1 and cnf_units[abs(c[0])] != (c[0] > 0) for c in clauses):
            return False
        affine_units = unit_affine(rows, assignment)
        if affine_units is None:
            counters["affine_conflicts"] += 1
            return False
        if not cnf_units and not affine_units:
            break
        new = dict(cnf_units)
        for v, value in affine_units.items():
            if v in new and new[v] != value:
                counters["affine_conflicts"] += 1
                return False
            new[v] = value
        new = {v: val for v, val in new.items() if v not in assignment}
        if not new:
            break
        if any(v in assignment and assignment[v] != value for v, value in new.items()):
            return False
        counters["affine_implied"] += sum(v in affine_units and v not in cnf_units for v in new)
        clauses = simplify(clauses, new)
        if clauses is None:
            return False
        assignment = {**assignment, **new}
    if not clauses:
        return True
    occurrences = Counter(abs(l) for c in clauses for l in c)
    chosen = min(occurrences, key=lambda v: (-occurrences[v], v))
    counters["decisions"] += 1
    for value in (True, False):
        next_clauses = simplify(clauses, {chosen: value})
        if next_clauses is not None and solve(next_clauses, rows, counters,
                                              {**assignment, chosen: value}):
            return True
    return False


def make_case(n, seed, kind):
    rng = Random(991 * n + seed)
    clauses = []
    # Shared two-variable core causes pairwise cancellation:
    # (x1 xor x2 xor x3) xor (x1 xor x2 xor x4) = x3 xor x4.
    clauses += canonical_xor_cnf_clauses((1, 2, 3), 0)
    clauses += canonical_xor_cnf_clauses((1, 2, 4), 0)
    if kind == "conflict":
        clauses += [(3,), (-4,)]
    elif kind == "imply":
        clauses += [(3,)]
    elif kind == "sat":
        clauses += [(3,), (4,)]
    else:
        for _ in range(n):
            vars_ = rng.sample(range(5, n + 1), 3)
            clauses.append(tuple(v if rng.randrange(2) else -v for v in vars_))
    return CNFFormula.from_raw_clauses(clauses)


def run(seeds=8, repeats=3):
    records = []
    for n in (16, 32):
        for seed in range(seeds):
            for kind in ("conflict", "imply", "sat", "random"):
                formula = make_case(n, seed, kind)
                raw = extract_rows(formula)
                derived = derive_small_rows(raw)
                assert len(derived) > len(raw)
                with Minisat22(bootstrap_with=formula.to_clause_lists()) as oracle:
                    expected = oracle.solve()
                baseline = [run_masked(formula) for _ in range(repeats)]
                timings = []
                data = None
                for _ in range(repeats):
                    t = perf_counter()
                    source_rows = extract_rows(formula)
                    implications = derive_small_rows(source_rows)
                    counters = Counter()
                    found = solve(tuple(map(tuple, formula.to_clause_lists())),
                                  implications, counters)
                    timings.append((perf_counter() - t) * 1000)
                    data = dict(counters)
                    assert found == expected
                assert all(x["sat"] == expected for x in baseline)
                records.append({"n": n, "seed": seed, "kind": kind,
                                "expected_sat": expected,
                                "base_nodes": baseline[0]["nodes"],
                                "new_nodes": data.get("nodes", 0),
                                "affine_implied": data.get("affine_implied", 0),
                                "affine_conflicts": data.get("affine_conflicts", 0),
                                "base_ms": median(x["elapsed_ms"] for x in baseline),
                                "new_ms": median(timings)})
    return {"summary": {"cases": len(records),
                        "new_time_wins": sum(r["new_ms"] < r["base_ms"] for r in records),
                        "new_node_wins": sum(r["new_nodes"] < r["base_nodes"] for r in records),
                        "affine_implied": sum(r["affine_implied"] for r in records),
                        "affine_conflicts": sum(r["affine_conflicts"] for r in records),
                        "base_total_ms": round(sum(r["base_ms"] for r in records), 4),
                        "new_total_ms": round(sum(r["new_ms"] for r in records), 4)},
            "records": records}


if __name__ == "__main__":
    import json
    print(json.dumps(run()["summary"], indent=2))
