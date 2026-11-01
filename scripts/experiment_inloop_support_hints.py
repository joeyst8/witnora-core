"""In-loop separator-candidate prototype: repeated CNF support signatures.

Clause supports are registered as the solver ingests the clauses. If two
distinct frequently recurring supports intersect in a small variable set,
that intersection is a *candidate* cut for branching. No external separator
search, oracle, or actual separation claim. Control: frequency heuristic.
"""
from __future__ import annotations

from collections import Counter
from time import perf_counter
from itertools import combinations
import json
from pathlib import Path

from witnora_core.cnf import CNFFormula
from scripts.benchmark_separator_decomposition import simplify
from scripts.benchmark_scaled_minisat_separator import scale_hidden_formula
from scripts.experiment_autonomous_parity_separator import (
    _random_three_sat, _dense_bridge_negative,
)


def support_candidates(rows):
    """Gather support frequency during clause ingestion, without XOR parsing."""
    counts = Counter(frozenset(abs(x) for x in row) for row in rows
                     if len(row) >= 3)
    strong = sorted((support for support, n in counts.items() if n >= 3),
                    key=lambda group: tuple(sorted(group)))
    scored = Counter()
    for left, right in combinations(strong, 2):
        shared = left & right
        if 1 <= len(shared) <= 3:
            for variable in shared:
                scored[variable] += counts[left] * counts[right]
    return scored


def dpll(rows, stats, mode="smallest", hints=None):
    stats["nodes"] += 1
    rows = tuple(tuple(row) for row in rows)
    while True:
        if not rows:
            return True
        if any(not row for row in rows):
            return False
        units = [row[0] for row in rows if len(row) == 1]
        if not units:
            break
        assignment = {}
        for literal in units:
            variable = abs(literal)
            value = literal > 0
            if variable in assignment and assignment[variable] != value:
                return False
            assignment[variable] = value
        reduced = simplify(rows, assignment)
        if reduced is None:
            return False
        rows = tuple(reduced)
    frequencies = Counter(abs(lit) for row in rows for lit in row)
    if mode == "smallest":
        chosen = min(frequencies)
    elif mode == "frequency":
        chosen = min(frequencies, key=lambda v: (-frequencies[v], v))
    elif mode == "support":
        chosen = min(frequencies, key=lambda v: (
            -(hints or {}).get(v, 0), -frequencies[v], v))
    else:
        raise ValueError("unknown mode")
    stats["decisions"] += 1
    if mode == "support" and hints and hints.get(chosen, 0):
        stats["hinted_decisions"] += 1
    for value in (True, False):
        reduced = simplify(rows, {chosen: value})
        if reduced is not None and dpll(reduced, stats, mode, hints):
            return True
    return False


def measure(formula, mode):
    rows = formula.to_clause_lists()
    start = perf_counter()
    hints = support_candidates(rows) if mode == "support" else {}
    stats = {"nodes": 0, "decisions": 0, "hinted_decisions": 0}
    sat = dpll(rows, stats, mode, hints)
    elapsed_ms = (perf_counter() - start) * 1000
    return {
        "sat": sat, "nodes": stats["nodes"],
        "decisions": stats["decisions"],
        "hinted_decisions": stats["hinted_decisions"],
        "candidate_count": len(hints),
        "elapsed_ms": round(elapsed_ms, 5),
    }


def benchmark(seed_count=8):
    records = []
    for copies in (1, 2, 4, 8):
        for seed in range(seed_count):
            formula = scale_hidden_formula(seed, copies)
            records.append(("structured", copies, seed, formula))
    for seed in range(seed_count):
        records.append(("random_3sat", 0, seed, _random_three_sat(seed)))
        records.append(("dense_bridge_negative", 0, seed,
                        _dense_bridge_negative(seed)))
    output = []
    for family, copies, seed, formula in records:
        result = {mode: measure(formula, mode)
                  for mode in ("smallest", "frequency", "support")}
        if len({part["sat"] for part in result.values()}) != 1:
            raise AssertionError(("SAT disagreement", family, copies, seed))
        output.append({
            "family": family, "copies": copies, "seed": seed,
            "vars": formula.num_vars, "clauses": formula.num_clauses,
            **result,
        })
    return {
        "summary": {
            "total": len(output), "answers_agree": len(output),
            "support_hints_present": sum(
                r["support"]["candidate_count"] > 0 for r in output),
            "support_beats_smallest_nodes": sum(
                r["support"]["nodes"] < r["smallest"]["nodes"] for r in output),
            "support_beats_frequency_nodes": sum(
                r["support"]["nodes"] < r["frequency"]["nodes"] for r in output),
            "support_beats_frequency_time": sum(
                r["support"]["elapsed_ms"] < r["frequency"]["elapsed_ms"]
                for r in output),
            "novelty_established": False,
            "full_separator_audit_performed": False,
        },
        "records": output,
    }


def main():
    outcome = benchmark()
    path = Path("research/inloop_support_hint_results.json")
    path.write_text(json.dumps(outcome, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    print(json.dumps(outcome["summary"], sort_keys=True))
    for copies in (1, 2, 4, 8):
        selected = [r for r in outcome["records"]
                    if r["family"] == "structured" and r["copies"] == copies]
        print(json.dumps({
            "copies": copies,
            "smallest_nodes": sum(r["smallest"]["nodes"] for r in selected),
            "frequency_nodes": sum(r["frequency"]["nodes"] for r in selected),
            "support_nodes": sum(r["support"]["nodes"] for r in selected),
            "hinted_decisions": sum(
                r["support"]["hinted_decisions"] for r in selected),
        }, sort_keys=True))


if __name__ == "__main__":
    main()
