"""Reproducible controlled experiment for parity-cut boundary repair.

Runs hidden-separator SAT families with and without cross-CNF noise.
The candidate cut comes from the generator's ground truth, so this study
isolates the *repair* step rather than claiming parity-cut discovery.
"""
from __future__ import annotations

import json
from pathlib import Path
from statistics import mean

from witnora_core.hidden_separator_challenge import (
    make_hidden_separator, full_cnf_anchors_separated,
)
from witnora_core.parity_cut_boundary_repair import (
    repair_parity_separator, independent_minimum_anchor_cut,
)


def _independent_dfs_separated(formula, cut, left, right):
    """Second implementation of source-graph reachability for audit."""
    excluded = set(cut)
    edges = {v: set() for v in formula.variables if v not in excluded}
    for clause in formula.clauses:
        vs = set(clause.variables) - excluded
        for v in vs:
            edges[v].update(vs - {v})
    stack = [left]
    visited = set()
    while stack:
        v = stack.pop()
        if v in visited:
            continue
        visited.add(v)
        stack.extend(edges.get(v, ()) - visited)
    return right not in visited


def run_experiment(seeds=range(8)):
    records = []
    for width in (2, 3):
        for cross_noise in (False, True):
            for seed in seeds:
                formula, metadata = make_hidden_separator(
                    seed, width=width, cross_noise=cross_noise
                )
                candidate = metadata["boundary"]
                left, right = metadata["left_anchor"], metadata["right_anchor"]
                baseline = full_cnf_anchors_separated(
                    formula, candidate, left, right
                )
                repair = repair_parity_separator(
                    formula, candidate, left, right, max_extra=2
                )
                if repair["full_cnf_separated"]:
                    recovered = tuple(repair["repaired_cut"])
                    if not _independent_dfs_separated(
                            formula, recovered, left, right):
                        raise AssertionError("independent DFS rejected repair")
                optimum = independent_minimum_anchor_cut(
                    formula, left, right, max_size=5
                )
                records.append({
                    "seed": seed, "width": width, "cross_noise": cross_noise,
                    "cnf_variables": len(formula.variables),
                    "cnf_clauses": formula.num_clauses,
                    "parity_candidate_size": len(candidate),
                    "parity_candidate_sound": baseline,
                    "repair_status": repair["status"],
                    "extra_variables": repair["extra_variables"],
                    "repaired_size": (
                        len(repair["repaired_cut"])
                        if repair["repaired_cut"] is not None else None
                    ),
                    "globally_optimal_size": (
                        len(optimum) if optimum is not None else None
                    ),
                    "search_trials": repair["trials"],
                })
    n = len(records)
    summary = {
        "cases": n,
        "clean_cases": sum(not r["cross_noise"] for r in records),
        "cross_noise_cases": sum(r["cross_noise"] for r in records),
        "parity_only_sound": sum(r["parity_candidate_sound"] for r in records),
        "successful_repairs": sum(r["repaired_size"] is not None for r in records),
        "needed_extra": sum(
            r["extra_variables"] is not None and len(r["extra_variables"]) > 0
            for r in records
        ),
        "mean_search_trials": round(mean(r["search_trials"] for r in records), 2),
        "mean_repaired_size": round(mean(
            r["repaired_size"] for r in records
            if r["repaired_size"] is not None
        ), 2),
        "mean_global_optimum": round(mean(
            r["globally_optimal_size"] for r in records
            if r["globally_optimal_size"] is not None
        ), 2),
        "bounded_known_family": True,
        "novelty_established": False,
    }
    return {"summary": summary, "records": records}


def main():
    result = run_experiment()
    path = Path("research/parity_cut_boundary_repair_results.json")
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
