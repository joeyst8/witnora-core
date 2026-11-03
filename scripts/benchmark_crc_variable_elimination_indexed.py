"""W-CRC-015: indexed exact VE versus frozen scan-everything VE.

Same source clauses, same externally found SAT witness, same factor
arithmetic, same max width and operation budget. Compare old vs new
full source-to-count cost and then both with independent Ganak.
"""
from __future__ import annotations

import json

from scripts.benchmark_crc_scaling import measured
from scripts.benchmark_crc_highcount import independent_ganak
from scripts.benchmark_crc_adversarial import (
    chain_source, ring_source, planted_random_source, block_source,
    get_source_model,
)
from scripts.benchmark_crc_variable_elimination import fibonacci
from witnora_core.crc_cutset_count import count_source_by_separator


def run(family, scale):
    if family == "chain":
        n = scale
        source, left, right = chain_source(n), (1,), (n,)
        expected = fibonacci(n + 2)
    elif family == "ring":
        n = scale
        source, left, right = ring_source(n), (1,), (n // 2,)
        expected = fibonacci(n - 1) + fibonacci(n + 1)
    elif family == "blocks":
        source, n, expected = block_source(scale)
        left, right = (1,), (4,)
    elif family == "random":
        n = scale
        source = planted_random_source(n, 13013)
        left, right, expected = (1,), (n,), None
    else:
        raise ValueError(family)
    boundary = tuple(range(1, n + 1))
    witness, sat_ms = get_source_model(source, n)
    if witness is None:
        raise AssertionError("planted SAT witness absent")

    def count(backend):
        got = count_source_by_separator(
            source, boundary, left, right, witness,
            max_separator_size=2, max_primal_edges=10000,
            max_component_variables=8,
            component_backend=backend,
            max_ve_factor_variables=3,
            max_ve_operations=200000)
        return None if got is None else (
            got.models, got.ve_operations, backend)

    previous = measured(lambda: count("variable_elimination"),
                        repeats=2, seconds=4)
    indexed = measured(lambda: count("variable_elimination_indexed"),
                       repeats=2, seconds=4)
    ganak = independent_ganak(source, n, seconds=4)
    if previous["status"] != indexed["status"]:
        raise AssertionError(f"old/new admission discrepancy: {family}, {n}")
    if previous["status"] == "EXACT":
        if previous["models"] != indexed["models"]:
            raise AssertionError(f"indexed math changed count: {family}, {n}")
        if previous["states"] != indexed["states"]:
            raise AssertionError(f"indexed math changed operator work: {family}, {n}")
    if expected is not None and (
        indexed["status"] != "EXACT" or indexed["models"] != expected):
        raise AssertionError(f"analytic mismatch: {family}, {n}, {indexed}")
    if ganak["status"] == "EXACT":
        if expected is not None and ganak["models"] != expected:
            raise AssertionError("Ganak analytic mismatch")
        if indexed["status"] == "EXACT" and indexed["models"] != ganak["models"]:
            raise AssertionError("Ganak indexed mismatch")
    combined = (round(sat_ms + indexed["median_ms"], 4)
                if indexed["status"] == "EXACT" else None)
    return {
        "family": family, "n": n, "scale": scale,
        "clauses": len(source), "analytic_models": expected,
        "old_scan_ve": previous, "indexed_ve": indexed,
        "indexed_over_old_time": (
            round(indexed["median_ms"] / previous["median_ms"], 3)
            if previous["status"] == indexed["status"] == "EXACT" else None),
        "glucose3_witness_ms": round(sat_ms, 4),
        "indexed_plus_witness_ms": combined,
        "ganak": ganak,
        "indexed_plus_witness_over_ganak_engine": (
            round(combined / ganak["counter_wall_ms"], 3)
            if combined is not None and ganak["status"] == "EXACT" and
            ganak["counter_wall_ms"] else None),
    }


def main():
    rows = []
    for n in (16, 32, 64, 128, 256):
        for family in ("chain", "ring"):
            row = run(family, n)
            rows.append(row)
            print(json.dumps(row, sort_keys=True), flush=True)
    for blocks in (8, 32):
        row = run("blocks", blocks)
        rows.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)
    for n in (16, 24, 32):
        row = run("random", n)
        rows.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)
    print(json.dumps({
        "summary": "W-CRC-015 incremental width-bound VE cost pilot",
        "cases": len(rows),
        "indexed_exact": sum(r["indexed_ve"]["status"] == "EXACT"
                             for r in rows),
        "ganak_exact": sum(r["ganak"]["status"] == "EXACT" for r in rows),
        "all_matched_reference": True,
        "no_general_sat_speedup_claim": True,
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
