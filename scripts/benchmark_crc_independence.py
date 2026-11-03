"""W-CRC-008 exact independence-audit cost versus ordinary W-CRC counting.

The audit checks 2^(|A|+|B|) source Walsh modes and may itself be as
expensive as simply performing the exact coefficient convolution.
This is a falsifiable admission-cost pilot, not a speedup claim.
"""
from __future__ import annotations

import json
from itertools import combinations

from scripts.benchmark_crc_scaling import measured
from scripts.benchmark_crc_highcount import independent_ganak
from scripts.benchmark_crc_symmetry_stress import (
    DISPERSED, TETRAHEDRON, source_with_defects,
)
from tests.test_crc_conflict_oracle import add_conflict
from witnora_core.crc_independence_audit import audit_defect_source_independence
from witnora_core.crc_source import count_signed_cnf_crc


def run(n: int, pattern: str, *, seconds: float = 4):
    missing = DISPERSED if pattern == "dispersed" else TETRAHEDRON
    base = source_with_defects(n, missing, signed=(pattern == "tetrahedron"))
    supports = (s for s in combinations(range(1, n + 1), 3)
                if s not in missing)
    source = add_conflict(add_conflict(base, next(supports)),
                          next(supports))
    boundary = tuple(range(1, n + 1))
    left, right = (1, 2, 3), (4, 5, 6)

    def audit():
        result = audit_defect_source_independence(
            base, boundary, left, right, max_modes=64)
        if result is None:
            return None
        return (int(result.independent), result.checked_modes, "fourier_audit")

    def count():
        result = count_signed_cnf_crc(
            source, n, max_inclusion_subsets=2,
            enable_conflict_oracle=True)
        if result is None:
            return None
        return (result.models, result.coefficient_stats.coefficient_states,
                result.coefficient_stats.coefficient_backend)

    audited = measured(audit, repeats=2, seconds=seconds)
    counted = measured(count, repeats=2, seconds=seconds)
    ganak = independent_ganak(source, n, seconds=seconds)
    if (audited["status"] != "EXACT" or counted["status"] != "EXACT" or
        ganak["status"] != "EXACT" or
        counted["models"] != ganak["models"] or
        audited["states"] != 64):
        raise AssertionError(f"incomplete or wrong exact result: {audited}, {counted}, {ganak}")
    return {
        "n": n, "pattern": pattern, "base_clauses": len(base),
        "model_count": counted["models"], "independent": bool(audited["models"]),
        "audit": audited, "count": counted, "ganak": ganak,
        "audit_over_direct_count_time":
            round(audited["median_ms"] / counted["median_ms"], 3),
    }


def main():
    rows = []
    for n in (8, 12, 20, 28):
        for pattern in ("dispersed", "tetrahedron"):
            row = run(n, pattern)
            rows.append(row)
            print(json.dumps(row, sort_keys=True), flush=True)
    print(json.dumps({
        "summary": "W-CRC-008 independence admission cost pilot",
        "cases": len(rows),
        "no_unverified_speedup_claim": True,
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
