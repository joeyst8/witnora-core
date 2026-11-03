"""W-CRC-012 end-to-end exact cutset #SAT vs independent Ganak.

Includes automatic minimum-cut discovery, enumeration of *every*
separator assignment, and local component counting. Closed-form
star-family model totals are an additional independent control.
Ganak's engine timing omits Python process startup, while the
W-CRC time includes its full Python algorithm.
"""
from __future__ import annotations

import json

from scripts.benchmark_crc_scaling import measured
from scripts.benchmark_crc_highcount import independent_ganak
from witnora_core.crc_cutset_count import count_source_by_separator


def run(n: int, hubs: int):
    endpoints = tuple(range(1, n - hubs + 1))
    hub_ids = tuple(range(n - hubs + 1, n + 1))
    source = [[v, hub] for hub in hub_ids for v in endpoints]
    boundary = tuple(range(1, n + 1))
    expected = (1 << (n - hubs)) + (1 << hubs) - 1

    def algorithm():
        result = count_source_by_separator(
            source, boundary, (1,), (2,), (1 << n) - 1,
            max_separator_size=hubs,
            max_primal_edges=2 * n,
            max_component_variables=12,
            max_assignment_states=100000)
        return None if result is None else (
            result.models, result.assignment_states, "cutset")

    ours = measured(algorithm, repeats=2, seconds=4)
    ganak = independent_ganak(source, n, seconds=4)
    if ours["status"] != "EXACT" or ours["models"] != expected:
        raise AssertionError(f"analytic cutset contradiction: {n}, {hubs}, {ours}, {expected}")
    if ganak["status"] == "EXACT" and ganak["models"] != expected:
        raise AssertionError(f"independent Ganak contradiction: {n}, {hubs}, {ganak}")
    ratio = None
    if ganak["status"] == "EXACT" and ganak["counter_wall_ms"] > 0:
        ratio = round(ours["median_ms"] / ganak["counter_wall_ms"], 3)
    return {
        "n": n, "hubs": hubs,
        "clauses": len(source), "analytic_models": expected,
        "cutset": ours, "ganak": ganak,
        "cutset_over_ganak_engine_time": ratio,
    }


def main():
    rows = []
    for n in (16, 64, 128, 256):
        for hubs in (1, 2):
            row = run(n, hubs)
            rows.append(row)
            print(json.dumps(row, sort_keys=True), flush=True)
    print(json.dumps({
        "summary": "W-CRC-012 full counting versus independent Ganak",
        "cases": len(rows),
        "ganak_exact": sum(r["ganak"]["status"] == "EXACT" for r in rows),
        "cutset_analytic_exact": len(rows),
        "no_general_sat_speedup_claim": True,
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
