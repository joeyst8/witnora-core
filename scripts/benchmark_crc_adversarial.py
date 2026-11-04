"""W-CRC-013: challenge easy-hub #SAT wins with heterogeneous sources.

Includes explicitly timed Glucose3 witness acquisition (missing from
W-CRC-012), exact small-component factorization, a dedicated Ganak
comparison, and documented INCOMPLETE outcomes for non-admitted inputs.
This is a pilot with controls, not a broad solver competition.
"""
from __future__ import annotations

import json
import random
import statistics
import time

from scripts.benchmark_crc_scaling import measured
from scripts.benchmark_crc_highcount import independent_ganak
from witnora_core.crc_cutset_count import count_source_by_separator
from witnora_core.crc_separator_discovery import discover_source_separator


def block_source(blocks):
    hub = 3 * blocks + 1
    source = []
    for i in range(blocks):
        a, b, c = 3 * i + 1, 3 * i + 2, 3 * i + 3
        source.extend([
            [a, b], [-a, c], [b, -c],
            [hub, a], [hub, b],
        ])
    return source, hub, 3 ** blocks + 1


def chain_source(n):
    return [[v, v + 1] for v in range(1, n)]


def ring_source(n):
    return chain_source(n) + [[n, 1]]


def planted_random_source(n, seed):
    rng = random.Random(seed)
    source = []
    for _ in range(3 * n):
        vs = rng.sample(range(1, n + 1), 3)
        lits = [v if rng.randrange(2) else -v for v in vs]
        lits[0] = vs[0]  # all-one witness exists
        source.append(lits)
    return source


def get_source_model(source, n):
    """One timed external SAT solve, with all source-model bits returned."""
    from pysat.solvers import Solver
    start = time.perf_counter()
    with Solver(name="g3", bootstrap_with=source) as solver:
        if not solver.solve():
            return None, (time.perf_counter() - start) * 1000
        model = solver.get_model()
    mask = sum(1 << (abs(lit) - 1) for lit in model
               if lit > 0 and abs(lit) <= n)
    return mask, (time.perf_counter() - start) * 1000


def run(label, source, n, expected=None):
    groups = ((1,), (4,)) if label.startswith("blocks") else ((1,), (n,))
    witness, sat_ms = get_source_model(source, n)
    if witness is None:
        raise AssertionError("seeded source unexpectedly UNSAT")
    cap_args = dict(max_separator_size=2, max_primal_edges=5000,
                    max_component_variables=8, max_assignment_states=100000)
    cut = discover_source_separator(
        source, tuple(range(1, n + 1)), *groups, witness,
        max_separator_size=2, max_primal_edges=5000)

    def count():
        result = count_source_by_separator(
            source, tuple(range(1, n + 1)), *groups, witness, **cap_args)
        return None if result is None else (
            result.models, result.assignment_states, "cutset")

    counted = measured(count, repeats=2, seconds=4)
    if expected is not None and (
        counted["status"] != "EXACT" or counted["models"] != expected):
        raise AssertionError(f"analytic contradiction: {label}: {counted}, {expected}")
    ganak = independent_ganak(source, n, seconds=4)
    if (ganak["status"] == "EXACT" and
        counted["status"] == "EXACT" and
        ganak["models"] != counted["models"]):
        raise AssertionError(f"Ganak exact contradiction: {label}")
    if expected is not None and ganak["status"] == "EXACT":
        if ganak["models"] != expected:
            raise AssertionError(f"Ganak analytic contradiction: {label}")
    admission = ("EXACT" if counted["status"] == "EXACT" else
                 "NO_ADMITTED_SMALL_CUT" if cut is None else
                 "LARGE_COMPONENT_OR_STATE_BUDGET")
    total_with_sat = (
        round(sat_ms + counted["median_ms"], 4)
        if counted["status"] == "EXACT" else None)
    return {
        "case": label, "n": n, "clauses": len(source),
        "expected_closed_form": expected, "admission": admission,
        "witness_glucose3_ms": round(sat_ms, 4),
        "cut_size": len(cut.separator) if cut is not None else None,
        "cutset": counted,
        "total_witness_plus_cutset_ms": total_with_sat,
        "ganak": ganak,
        "total_over_ganak_engine": (
            round(total_with_sat / ganak["counter_wall_ms"], 3)
            if total_with_sat is not None and ganak["status"] == "EXACT"
            and ganak["counter_wall_ms"] else None),
    }


def main():
    rows = []
    for blocks in (4, 8, 16, 32, 64):
        source, n, expected = block_source(blocks)
        row = run(f"blocks_{blocks}", source, n, expected)
        rows.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)
    for n in (16, 32):
        for family, source in (
            ("chain", chain_source(n)),
            ("ring", ring_source(n)),
        ):
            row = run(f"{family}_{n}", source, n)
            rows.append(row)
            print(json.dumps(row, sort_keys=True), flush=True)
    for n in (16, 24, 32):
        row = run(f"random3_{n}", planted_random_source(n, 13013), n)
        rows.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)
    print(json.dumps({
        "summary": "W-CRC-013 heterogeneous and adversarial admission pilot",
        "cases": len(rows),
        "admitted": sum(r["admission"] == "EXACT" for r in rows),
        "ganak_exact": sum(r["ganak"]["status"] == "EXACT" for r in rows),
        "witness_search_timed": True,
        "resource_failures_reported": True,
        "no_general_sat_speedup_claim": True,
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
