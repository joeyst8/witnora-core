"""Exploratory exact SAT comparison: plain DPLL vs discovered-cut decomposition.

Both arms use the same deterministic DPLL implementation. This is NOT an
industrial SAT-solver comparison. Discovery and conditioning overhead count.
"""
from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter

from witnora_core.cnf import CNFFormula
from witnora_core.autonomous_parity_separator import discover_repaired_separator
from scripts.experiment_autonomous_parity_separator import (
    _random_three_sat, _bridged_controls, _dense_bridge_negative,
)
from witnora_core.hidden_separator_challenge import make_hidden_separator


def simplify(rows, assignment):
    output = []
    for row in rows:
        if any((lit > 0) == assignment[abs(lit)] for lit in row
               if abs(lit) in assignment):
            continue
        remaining = tuple(lit for lit in row if abs(lit) not in assignment)
        if not remaining:
            return None
        output.append(remaining)
    return output


def solve_dpll(rows, stats):
    """Deterministic unit-propagating DPLL; count recursive search calls."""
    stats["nodes"] += 1
    rows = tuple(tuple(row) for row in rows)
    while True:
        if not rows:
            return True
        if any(not row for row in rows):
            return False
        units = {abs(row[0]): row[0] > 0 for row in rows if len(row) == 1}
        if not units:
            break
        # Conflicting unit literals must not be silently overwritten.
        for row in rows:
            if len(row) == 1 and units[abs(row[0])] != (row[0] > 0):
                return False
        result = simplify(rows, units)
        if result is None:
            return False
        rows = tuple(result)
    variable = min(abs(lit) for row in rows for lit in row)
    for value in (True, False):
        reduced = simplify(rows, {variable: value})
        if reduced is not None and solve_dpll(reduced, stats):
            return True
    return False


def components(rows):
    """Connected clause sets in the primal graph, including singleton vars."""
    adj = {}
    for row in rows:
        vs = {abs(lit) for lit in row}
        for v in vs:
            adj.setdefault(v, set()).update(vs - {v})
    labels = {}
    groups = []
    for start in sorted(adj):
        if start in labels:
            continue
        todo = [start]
        seen = {start}
        labels[start] = len(groups)
        while todo:
            for nxt in adj[todo.pop()]:
                if nxt not in seen:
                    seen.add(nxt)
                    labels[nxt] = len(groups)
                    todo.append(nxt)
        groups.append([])
    for row in rows:
        groups[labels[abs(row[0])]].append(row)
    return groups


def solve_with_cut(rows, cut, stats):
    """Condition on every cut assignment, then solve remaining components."""
    for mask in range(1 << len(cut)):
        stats["boundary_assignments"] += 1
        assignment = {v: bool(mask & (1 << i)) for i, v in enumerate(cut)}
        reduced = simplify(rows, assignment)
        if reduced is None:
            continue
        if all(solve_dpll(group, stats) for group in components(reduced)):
            return True
    return False


def benchmark(seed_count=8):
    cases = []
    for width in (2, 3):
        for noisy in (False, True):
            for seed in range(seed_count):
                formula, _ = make_hidden_separator(seed, width=width,
                                                   cross_noise=noisy)
                cases.append(("hidden_noisy" if noisy else "hidden_clean",
                              seed, formula))
    for name, generator in (
        ("random_3sat", _random_three_sat),
        ("bridged_stress", _bridged_controls),
        ("dense_bridge_negative", _dense_bridge_negative),
    ):
        for seed in range(seed_count):
            cases.append((name, seed, generator(seed)))
    results = []
    for family, seed, formula in cases:
        rows = formula.to_clause_lists()
        plain_stats = {"nodes": 0}
        t = perf_counter()
        plain_answer = solve_dpll(rows, plain_stats)
        plain_ms = (perf_counter() - t) * 1000
        t = perf_counter()
        detected = discover_repaired_separator(formula)
        detection_ms = (perf_counter() - t) * 1000
        cut = detected["cut"] if detected["status"] == "FOUND" else None
        cut_stats = {"nodes": 0, "boundary_assignments": 0}
        t = perf_counter()
        assisted_answer = (solve_with_cut(rows, cut, cut_stats)
                           if cut is not None
                           else solve_dpll(rows, cut_stats))
        assisted_ms = (perf_counter() - t) * 1000 + detection_ms
        if plain_answer != assisted_answer:
            raise AssertionError((family, seed, "SAT mismatch"))
        results.append({
            "family": family, "seed": seed, "num_vars": formula.num_vars,
            "clauses": formula.num_clauses, "sat": plain_answer,
            "cut": cut, "plain_nodes": plain_stats["nodes"],
            "assisted_nodes": cut_stats["nodes"],
            "boundary_assignments": cut_stats["boundary_assignments"],
            "plain_ms": round(plain_ms, 4),
            "assisted_ms_including_discovery": round(assisted_ms, 4),
            "discovery_ms": round(detection_ms, 4),
        })
    split = [r for r in results if r["cut"] is not None]
    return {
        "summary": {
            "total": len(results), "answers_agree": len(results),
            "detected": len(split),
            "node_reductions": sum(r["assisted_nodes"] < r["plain_nodes"]
                                   for r in split),
            "node_increases": sum(r["assisted_nodes"] > r["plain_nodes"]
                                  for r in split),
            "node_ties": sum(r["assisted_nodes"] == r["plain_nodes"]
                            for r in split),
            "time_wins_including_discovery": sum(
                r["assisted_ms_including_discovery"] < r["plain_ms"]
                for r in split),
            "plain_total_ms": round(sum(r["plain_ms"] for r in results), 3),
            "assisted_total_ms_including_discovery": round(
                sum(r["assisted_ms_including_discovery"] for r in results), 3),
            "industrial_solver_baseline": False,
            "novelty_established": False,
        },
        "records": results,
    }


def main():
    data = benchmark()
    path = Path("research/solver_decomposition_benchmark.json")
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    print(json.dumps(data["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
