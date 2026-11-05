"""W-CRC-016: held-out low-width, high-width and random source families.

Independent held-out graph geometries and new seeds test the limits of
indexed VE admission. A Glucose3 witness is timed in every case.
All admitted integer counts are independently checked against Ganak
when Ganak completes within a fixed time bound; no guess on timeout.
"""
from __future__ import annotations

from collections import deque
from itertools import combinations
import json
import random

from scripts.benchmark_crc_adversarial import (
    get_source_model, planted_random_source,
)
from scripts.benchmark_crc_scaling import measured
from scripts.benchmark_crc_highcount import independent_ganak
from witnora_core.crc_cutset_count import count_source_by_separator
from witnora_core.crc_separator_discovery import discover_source_separator


def tree_source(n, seed):
    rng = random.Random(seed)
    source = []
    graph = {v: set() for v in range(1, n + 1)}
    for child in range(2, n + 1):
        parent = rng.randrange(1, child)
        source.append([parent if rng.randrange(2) else -parent, child])
        graph[parent].add(child)
        graph[child].add(parent)
    distances = {1: 0}
    pending = deque([1])
    while pending:
        v = pending.popleft()
        for u in graph[v]:
            if u not in distances:
                distances[u] = distances[v] + 1
                pending.append(u)
    farthest = max(distances, key=lambda v: (distances[v], v))
    if distances[farthest] < 2:
        raise AssertionError("test tree unexpectedly has only diameter one")
    return source, (1,), (farthest,)


def ladder_source(n, seed):
    if n % 2 or n < 8:
        raise ValueError("ladder n must be even and >=8")
    rng = random.Random(seed)
    rungs = n // 2
    edges = []
    for i in range(1, rungs):
        edges.append((i, i + 1))
        edges.append((rungs + i, rungs + i + 1))
    for i in range(1, rungs + 1):
        edges.append((i, rungs + i))
    clauses = [[u if rng.randrange(2) else -u, v]
               for u, v in edges]
    return clauses, (1, rungs + 1), (rungs, n)


def bridged_cliques(size=10):
    left = tuple(range(1, size + 1))
    right = tuple(range(size + 1, 2 * size + 1))
    hub = 2 * size + 1
    clauses = [[u, v] for group in (left, right)
               for u, v in combinations(group, 2)]
    clauses.extend([[v, hub] for v in left + right])
    return clauses, hub, (left[0],), (right[0],)


def run(family, n, seed):
    if family == "tree":
        source, left, right = tree_source(n, seed)
    elif family == "ladder":
        source, left, right = ladder_source(n, seed)
    elif family == "random3":
        source = planted_random_source(n, seed)
        left, right = (1,), (n,)
    elif family == "clique_bridge":
        source, n, left, right = bridged_cliques(10)
    else:
        raise ValueError(family)
    boundary = tuple(range(1, n + 1))
    witness, sat_ms = get_source_model(source, n)
    if witness is None:
        raise AssertionError("held-out planted source unexpectedly UNSAT")
    cut = discover_source_separator(
        source, boundary, left, right, witness,
        max_separator_size=2, max_primal_edges=10000)

    def count():
        result = count_source_by_separator(
            source, boundary, left, right, witness,
            max_separator_size=2, max_primal_edges=10000,
            max_component_variables=8,
            component_backend="variable_elimination_indexed",
            max_ve_factor_variables=4, max_ve_operations=200000)
        return None if result is None else (
            result.models, result.ve_operations, result.component_backend)

    counted = measured(count, repeats=2, seconds=4)
    external = independent_ganak(source, n, seconds=4)
    if (counted["status"] == "EXACT" and external["status"] == "EXACT"
        and counted["models"] != external["models"]):
        raise AssertionError(f"held-out count mismatch: {family},n={n},seed={seed}")
    reason = ("EXACT" if counted["status"] == "EXACT" else
              "NO_ADMITTED_SMALL_CUT" if cut is None else
              "FACTOR_WIDTH_OR_WORK_BUDGET")
    combined = (
        round(sat_ms + counted["median_ms"], 4)
        if counted["status"] == "EXACT" else None)
    return {
        "family": family, "n": n, "seed": seed,
        "source_clauses": len(source), "admission": reason,
        "cut_size": len(cut.separator) if cut is not None else None,
        "witness_glucose3_ms": round(sat_ms, 4),
        "indexed_ve": counted, "combined_witness_and_ve_ms": combined,
        "ganak": external,
        "combined_over_ganak_engine": (
            round(combined / external["counter_wall_ms"], 3)
            if combined is not None and external["status"] == "EXACT"
            and external["counter_wall_ms"] else None),
    }


def main():
    results = []
    for family in ("tree", "ladder"):
        for n in (32, 64, 128, 256):
            for seed in (16016, 16017):
                row = run(family, n, seed)
                results.append(row)
                print(json.dumps(row, sort_keys=True), flush=True)
    for n in (16, 24, 32):
        for seed in (16016, 16017):
            row = run("random3", n, seed)
            results.append(row)
            print(json.dumps(row, sort_keys=True), flush=True)
    row = run("clique_bridge", 21, 16016)
    results.append(row)
    print(json.dumps(row, sort_keys=True), flush=True)
    print(json.dumps({
        "summary": "W-CRC-016 held-out primal graph admissions",
        "cases": len(results),
        "admitted": sum(r["admission"] == "EXACT" for r in results),
        "ganak_exact": sum(r["ganak"]["status"] == "EXACT"
                           for r in results),
        "admitted_external_matches": sum(
            r["admission"] == "EXACT" and
            r["ganak"]["status"] == "EXACT" for r in results),
        "rejected": sum(r["admission"] != "EXACT" for r in results),
        "no_general_sat_speedup_claim": True,
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
