"""W-CRC-011 bounded vertex-cut discovery versus supplied-separator audit.

A min vertex cut is computed on the signed source primal graph,
checked by reachability, then independently certified under a source
model by W-CRC-010. A given-separator audit is the timing control.
"""
from __future__ import annotations

import json

from scripts.benchmark_crc_scaling import measured
from witnora_core.crc_conditional_independence import (
    audit_conditioned_source_independence,
)
from witnora_core.crc_separator_discovery import discover_source_separator


def run(n: int, hub_value: bool):
    hub = n
    source = [[v, hub] for v in range(1, n)]
    boundary = tuple(range(1, n + 1))
    left, right = (1, 2), (n - 2, n - 1)
    witness = (1 << n) - 1 if hub_value else (1 << (n - 1)) - 1

    def given():
        result = audit_conditioned_source_independence(
            source, boundary, left, right, (hub,), witness)
        return None if result is None else (
            int(result.separated_after_conditioning),
            result.residual_clauses, "given_separator")

    def discovered():
        result = discover_source_separator(
            source, boundary, left, right, witness,
            max_separator_size=2, max_primal_edges=2 * n)
        return None if result is None else (
            int(result.separator == (hub,)),
            result.primal_edges, "min_vertex_cut")

    baseline = measured(given, repeats=2, seconds=4)
    discovered_cost = measured(discovered, repeats=2, seconds=4)
    if (baseline["status"] != "EXACT" or
        discovered_cost["status"] != "EXACT" or
        baseline["models"] != 1 or discovered_cost["models"] != 1):
        raise AssertionError(f"discovery or control failed: {baseline}, {discovered_cost}")
    return {
        "n": n, "hub_value": int(hub_value), "clauses": len(source),
        "minimum_separator_size": 1,
        "known_separator_audit": baseline,
        "discovery_and_audit": discovered_cost,
        "discovery_over_given_time":
            round(discovered_cost["median_ms"] / baseline["median_ms"], 3),
    }


def main():
    results = []
    for n in (16, 64, 128, 256):
        for hub_value in (False, True):
            row = run(n, hub_value)
            results.append(row)
            print(json.dumps(row, sort_keys=True), flush=True)
    print(json.dumps({
        "summary": "W-CRC-011 exact minimum separator discovery cost pilot",
        "cases": len(results), "all_minimum_separators_verified": True,
        "no_general_sat_speedup_claim": True,
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
