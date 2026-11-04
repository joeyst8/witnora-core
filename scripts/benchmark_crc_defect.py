"""W-CRC-005: end-to-end exact four-defect source counts versus Ganak.

Two families have the same number of omitted clauses but different
higher-order missing-support cliques. All runtime figures include CRC
source extraction and recognition. This is a restricted lifted-counting
pilot, not a general SAT performance claim.
"""
from __future__ import annotations

import json
from math import comb

from scripts.benchmark_crc_highcount import independent_ganak
from scripts.benchmark_crc_scaling import measured
from scripts.benchmark_crc_symmetry_stress import (
    DISPERSED, TETRAHEDRON, source_with_defects,
)
from witnora_core.crc_source import count_signed_cnf_crc


def run(n: int, pattern: str, *, seconds: float = 4):
    missing = DISPERSED if pattern == "dispersed" else TETRAHEDRON
    source = source_with_defects(n, missing, signed=(pattern == "tetrahedron"))
    expected = 1 + n + comb(n, 2) + 4 + int(pattern == "tetrahedron")

    def exact_defect():
        result = count_signed_cnf_crc(
            source, n, max_inclusion_subsets=2, enable_defect_oracle=True)
        if result is None:
            return None
        return (result.models, result.coefficient_stats.coefficient_states,
                result.coefficient_stats.coefficient_backend)

    timing = measured(exact_defect, repeats=2, seconds=seconds)
    ganak = independent_ganak(source, n, seconds=seconds)
    if timing["status"] != "EXACT" or ganak["status"] != "EXACT":
        raise AssertionError(f"bounded exact case did not finish: {timing}, {ganak}")
    if timing["models"] != expected or ganak["models"] != expected:
        raise AssertionError("independent Ganak and defect count disagree")
    if timing.get("backend") != "defect_hypergraph":
        raise AssertionError(f"wrong coefficient backend: {timing}")
    old_orbit = count_signed_cnf_crc(
        source, n, max_inclusion_subsets=2, enable_orbit_oracle=True)
    if old_orbit is not None:
        raise AssertionError("old <=r-defect recognizer accepted four deletions")
    return {
        "n": n, "pattern": pattern, "source_clauses": len(source),
        "expected_models": expected, "defect": timing, "ganak": ganak,
        "old_orbit": "OUT_OF_SCOPE",
        "ganak_ms_over_crc_ms": round(
            ganak["counter_wall_ms"] / timing["median_ms"], 3),
    }


def main():
    rows = []
    for n in (8, 12, 20, 28):
        for pattern in ("dispersed", "tetrahedron"):
            row = run(n, pattern)
            rows.append(row)
            print(json.dumps(row, sort_keys=True), flush=True)
    print(json.dumps({
        "summary": "W-CRC-005 four-defect exact hypergraph coefficient test",
        "cases": len(rows), "exact_crc": len(rows),
        "exact_independent_ganak": len(rows),
        "claim": "bounded_defect_lifted_counting_only",
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
