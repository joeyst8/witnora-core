"""Out-of-family audit for event-driven residual-component caching.

Generators differ from hidden_separator_challenge. Every solver answer is
checked against a separately implemented MiniSat22 baseline. No parameter
tuning on these instances; timing medians use five fresh solver runs.
"""
from __future__ import annotations

import json
from pathlib import Path
from random import Random
from statistics import median

from pysat.solvers import Minisat22

from witnora_core.cnf import CNFFormula
from witnora_core.xor import canonical_xor_cnf_clauses
from scripts.experiment_inloop_dynamic_split import run


def random_three_sat(seed, *, variables=24, clauses=90):
    rng = Random(100000 + seed)
    rows = []
    for _ in range(clauses):
        vs = rng.sample(range(1, variables + 1), 3)
        rows.append([v if rng.getrandbits(1) else -v for v in vs])
    return CNFFormula.from_raw_clauses(rows)


def disconnected_three_sat(seed):
    rng = Random(110000 + seed)
    rows = []
    for block in range(4):
        pool = list(range(1 + 9 * block, 10 + 9 * block))
        for _ in range(28):
            vs = rng.sample(pool, 3)
            rows.append([v if rng.getrandbits(1) else -v for v in vs])
    return CNFFormula.from_raw_clauses(rows)


def mixed_random_parities(seed, *, blocks=6, bridge=False):
    """New randomized local parity modules with optional cross-edges."""
    rng = Random(120000 + seed)
    shared = rng.sample(range(1, 60), 2)
    used = set(shared)
    rows = []
    local_vars = []
    for block in range(blocks):
        # Distinct local sets, not the hidden separator generator.
        local = [100 + 5 * block + i for i in range(3)]
        local_vars.extend(local)
        used.update(local)
        support = tuple(shared + local[:2])
        rows.extend(canonical_xor_cnf_clauses(support, rng.getrandbits(1)))
        # Local noise makes the formula more than a pure XOR encoding.
        rows.extend([[local[0], local[2]], [-local[1], local[2]]])
    if bridge:
        for block in range(blocks - 1):
            rows.append([local_vars[3 * block],
                         local_vars[3 * (block + 1)], -shared[0]])
    # Independently randomize labels and literal signs globally.
    old = sorted(used)
    labels = rng.sample(range(101, 2001), len(old))
    mapping = dict(zip(old, labels))
    flips = {v: rng.getrandbits(1) for v in old}
    randomized = [[
        mapping[abs(lit)] * (1 if ((lit > 0) != bool(flips[abs(lit)])) else -1)
        for lit in row] for row in rows]
    return CNFFormula.from_raw_clauses(randomized)


def minicheck(formula):
    with Minisat22(bootstrap_with=formula.to_clause_lists()) as solver:
        return solver.solve()


def timed_variant(formula, name, repeats=5):
    outputs = [run(formula, name) for _ in range(repeats)]
    first = outputs[0]
    if any(item["sat"] != first["sat"] for item in outputs):
        raise AssertionError("non-deterministic answer")
    return {**first, "median_ms": median(item["elapsed_ms"]
                                        for item in outputs)}


def benchmark(seed_count=8):
    records = []
    families = (
        ("random_3sat", lambda seed: random_three_sat(seed)),
        ("disconnected_3sat", disconnected_three_sat),
        ("mixed_parity", lambda seed: mixed_random_parities(seed)),
        ("bridged_mixed_parity",
         lambda seed: mixed_random_parities(seed, bridge=True)),
    )
    for name, generate in families:
        for seed in range(seed_count):
            formula = generate(seed)
            truth = minicheck(formula)
            a = timed_variant(formula, "frequency")
            b = timed_variant(formula, "support_split_event2_cache")
            e = timed_variant(formula, "support_split_equiv_cache")
            refined = timed_variant(formula, "support_split_refined_cache")
            if not (a["sat"] == b["sat"] == e["sat"] == refined["sat"] == truth):
                raise AssertionError((name, seed, "incorrect SAT answer"))
            records.append({
                "family": name, "seed": seed, "vars": formula.num_vars,
                "clauses": formula.num_clauses, "sat": truth,
                "baseline": a, "event_cached": b,
                "equivalence_cached": e,
                "refined_cached": refined,
            })
    return {
        "summary": {
            "total": len(records), "minisat_answers_agree": len(records),
            "event_cached_time_wins": sum(
                r["event_cached"]["median_ms"] < r["baseline"]["median_ms"]
                for r in records),
            "event_cached_node_wins": sum(
                r["event_cached"]["nodes"] < r["baseline"]["nodes"]
                for r in records),
            "event_cached_total_ms": round(sum(
                r["event_cached"]["median_ms"] for r in records), 5),
            "baseline_total_ms": round(sum(
                r["baseline"]["median_ms"] for r in records), 5),
            "cache_hits": sum(r["event_cached"]["cache_hits"] for r in records),
            "equivalence_hits": sum(
                r["equivalence_cached"]["equivalence_hits"] for r in records),
            "equivalence_node_wins_vs_event": sum(
                r["equivalence_cached"]["nodes"]
                < r["event_cached"]["nodes"] for r in records),
            "equivalence_time_wins_vs_event": sum(
                r["equivalence_cached"]["median_ms"]
                < r["event_cached"]["median_ms"] for r in records),
            "refined_equivalence_checks": sum(
                r["refined_cached"]["equivalence_checks"]
                for r in records),
            "coarse_equivalence_checks": sum(
                r["equivalence_cached"]["equivalence_checks"]
                for r in records),
            "refined_equivalence_hits": sum(
                r["refined_cached"]["equivalence_hits"]
                for r in records),
            "refined_total_ms": round(sum(
                r["refined_cached"]["median_ms"] for r in records), 5),
            "refined_vs_coarse_time_wins": sum(
                r["refined_cached"]["median_ms"]
                < r["equivalence_cached"]["median_ms"] for r in records),
            "equivalence_total_ms": round(sum(
                r["equivalence_cached"]["median_ms"] for r in records), 5),
            "novelty_established": False,
            "genuinely_new_formula_families": True,
        },
        "by_family": [{
            "family": name,
            "cases": sum(r["family"] == name for r in records),
            "wins": sum(r["family"] == name and
                        r["event_cached"]["median_ms"]
                        < r["baseline"]["median_ms"] for r in records),
            "baseline_ms": round(sum(
                r["baseline"]["median_ms"] for r in records
                if r["family"] == name), 5),
            "event_ms": round(sum(
                r["event_cached"]["median_ms"] for r in records
                if r["family"] == name), 5),
            "cache_hits": sum(r["event_cached"]["cache_hits"] for r in records
                              if r["family"] == name),
            "equivalence_hits": sum(
                r["equivalence_cached"]["equivalence_hits"] for r in records
                if r["family"] == name),
        } for name, _ in families],
        "records": records,
    }


def main():
    result = benchmark()
    path = Path("research/event_cached_ood_results.json")
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    print(json.dumps(result["summary"], sort_keys=True))
    for group in result["by_family"]:
        print(json.dumps(group, sort_keys=True))


if __name__ == "__main__":
    main()
