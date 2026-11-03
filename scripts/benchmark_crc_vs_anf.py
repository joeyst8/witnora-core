"""Small reproducible W-CRC-001 source-to-count pilot, not SAT-SOTA evidence.

Runs the unchanged Witnora structured ANF counter against the source-CNF
CRC prototype, including each side's source encoding/extraction costs.
Reports failed budgets as INCOMPLETE, not UNSAT. Times are a few
single-process Python samples, not statistically strong benchmarks.
"""
from __future__ import annotations

import json
import random
import statistics
import time
from itertools import product

from witnora_core.crc_source import count_signed_cnf_crc
from witnora_core.anf_structured_counter import count_common_zeros_structured
from witnora_core.violation_image_anf import (
    ANFCountingBudgetExceeded, source_violation_polynomials,
)


def xor_clauses(variables: tuple[int, ...], rhs: int) -> list[tuple[int, ...]]:
    return [
        tuple(v if value == 0 else -v for v, value in zip(variables, values))
        for values in product((0, 1), repeat=len(variables))
        if sum(values) % 2 != rhs
    ]


def parity_or_source(boundary_count: int) -> tuple[tuple[tuple[int, ...], ...], int, int]:
    assert boundary_count >= 3 and boundary_count % 3 == 0
    nvars = 2 * boundary_count - 2
    clauses: list[tuple[int, ...]] = []
    prev = boundary_count + 1
    clauses += xor_clauses((1, 2, prev), 0)
    for v in range(3, boundary_count):
        nxt = boundary_count + v - 1
        clauses += xor_clauses((prev, v, nxt), 0)
        prev = nxt
    clauses += xor_clauses((prev, boundary_count), 0)
    for v in range(1, boundary_count + 1, 3):
        clauses.append((v, v + 1, v + 2))
    blocks = boundary_count // 3
    return tuple(clauses), nvars, (7**blocks + (-1)**blocks) // 2


def dense_control(seed: int, nvars: int, nclauses: int) -> tuple[tuple[tuple[int, ...], ...], int]:
    rng = random.Random(seed)
    clauses = []
    for _ in range(nclauses):
        variables = rng.sample(range(1, nvars + 1), 3)
        clauses.append(tuple(v if rng.randrange(2) else -v for v in variables))
    return tuple(clauses), nvars


def timed(count_fn, repeats: int = 3):
    times = []
    value = None
    for _ in range(repeats):
        start = time.perf_counter()
        try:
            current = count_fn()
        except ANFCountingBudgetExceeded:
            return {"status": "INCOMPLETE_BUDGET", "median_ms": None}
        elapsed_ms = (time.perf_counter() - start) * 1000
        if current is None:
            return {"status": "INCOMPLETE_BUDGET", "median_ms": None}
        times.append(elapsed_ms)
        if value is not None and current[0] != value[0]:
            raise AssertionError("non-deterministic model count")
        value = current
    return {"status": "EXACT", "median_ms": round(statistics.median(times), 4),
            "models": value[0], "states_or_terms": value[1]}


def compare(source: tuple[tuple[int, ...], ...], nvars: int,
            expected: int | None = None) -> dict:
    def crc():
        r = count_signed_cnf_crc(source, nvars,
                                max_spectrum_terms=1024,
                                max_inclusion_subsets=1024)
        if r is None:
            return None
        return (r.models, r.coefficient_stats.left_fourier_terms)

    def baseline():
        polys = source_violation_polynomials(source, nvars)
        r = count_common_zeros_structured(polys, nvars, max_states=2000)
        return (r.satisfying_assignments, r.unique_states)

    c = timed(crc)
    b = timed(baseline)
    if c["status"] == "EXACT" and b["status"] == "EXACT":
        if c["models"] != b["models"]:
            raise AssertionError("independent exact counters disagree")
    if expected is not None:
        for method in (c, b):
            if method["status"] == "EXACT" and method["models"] != expected:
                raise AssertionError("known constructed count mismatch")
    return {"source_variables": nvars, "source_clauses": len(source),
            "crc": c, "structured_anf": b,
            "speedup_if_both_complete": (
                round(b["median_ms"] / c["median_ms"], 3)
                if c["status"] == b["status"] == "EXACT"
                and c["median_ms"] else None
            )}


def main() -> None:
    for k in (6, 9, 12, 15, 18):
        source, nvars, expected = parity_or_source(k)
        print(json.dumps({"family": "xor_chain_plus_disjoint_or",
                          "boundary_variables": k,
                          **compare(source, nvars, expected)}, sort_keys=True))
    for n, m, seed in ((10, 42, 20261103), (12, 51, 20261104)):
        source, nvars = dense_control(seed, n, m)
        print(json.dumps({"family": "dense_random_3cnf",
                          "seed": seed, **compare(source, nvars)}, sort_keys=True))


if __name__ == "__main__":
    main()
