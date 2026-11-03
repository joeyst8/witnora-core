"""W-CRC-009 certificate cost against full W-CRC-008 Fourier audit.

The source model witness is independently checked. A structural True is
sufficient for independence, while False means inconclusive. This is a
benchmark of audit overhead, not a general SAT or #SAT speedup claim.
"""
from __future__ import annotations

import json

from scripts.benchmark_crc_scaling import measured
from tests.test_crc_orbit_oracle import near_complete_source
from witnora_core.crc_independence_audit import audit_defect_source_independence
from witnora_core.crc_structural_independence import (
    audit_structural_source_independence,
)


def run(n: int, disconnected: bool):
    active = n - 2 if disconnected else n
    source = near_complete_source(
        active, 3, {v: True for v in range(1, active + 1)}, set())
    boundary = tuple(range(1, n + 1))
    left = (1, 2)
    right = (n - 1, n) if disconnected else (3, 4)
    witness = (1 << n) - 1

    def structural():
        result = audit_structural_source_independence(
            source, boundary, left, right, witness)
        return None if result is None else (
            int(result.separated), result.clauses_checked, "structural")

    def fourier():
        result = audit_defect_source_independence(
            source, boundary, left, right, max_modes=16)
        return None if result is None else (
            int(result.independent), result.checked_modes, "fourier")

    fast = measured(structural, repeats=2, seconds=4)
    exact = measured(fourier, repeats=2, seconds=4)
    if (fast["status"] != "EXACT" or exact["status"] != "EXACT" or
        fast["models"] != int(disconnected) or
        exact["models"] != int(disconnected)):
        raise AssertionError(f"certificate mismatch: {fast}, {exact}")
    return {
        "n": n, "disconnected": disconnected,
        "source_clauses": len(source),
        "structural": fast, "full_fourier": exact,
        "structural_over_fourier_time":
            round(fast["median_ms"] / exact["median_ms"], 3),
    }


def main():
    rows = []
    for n in (8, 12, 20, 28):
        for disconnected in (True, False):
            row = run(n, disconnected)
            rows.append(row)
            print(json.dumps(row, sort_keys=True), flush=True)
    print(json.dumps({
        "summary": "W-CRC-009 sufficient structural certificate audit cost",
        "cases": len(rows), "soundness_checked_against_fourier": True,
        "no_general_sat_speedup_claim": True,
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
