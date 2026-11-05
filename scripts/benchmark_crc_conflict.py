"""W-CRC-006 exact bounded sign-defect source pilot versus Ganak."""
from __future__ import annotations

import json
from itertools import combinations

from scripts.benchmark_crc_highcount import independent_ganak
from scripts.benchmark_crc_scaling import measured
from scripts.benchmark_crc_symmetry_stress import (
    DISPERSED, TETRAHEDRON, source_with_defects,
)
from tests.test_crc_conflict_oracle import add_conflict
from witnora_core.crc_source import count_signed_cnf_crc


def run_case(n: int, pattern: str, exceptions: int, *, seconds=4):
    missing = DISPERSED if pattern == "dispersed" else TETRAHEDRON
    source = source_with_defects(n, missing, signed=(pattern == "tetrahedron"))
    chosen = (s for s in combinations(range(1, n + 1), 3)
              if s not in missing)
    for _ in range(exceptions):
        source = add_conflict(source, next(chosen))

    def exact():
        result = count_signed_cnf_crc(
            source, n, max_inclusion_subsets=2,
            enable_conflict_oracle=True)
        if result is None:
            return None
        return (result.models, result.coefficient_stats.coefficient_states,
                result.coefficient_stats.coefficient_backend)

    crc = measured(exact, repeats=2, seconds=seconds)
    ganak = independent_ganak(source, n, seconds=seconds)
    if (crc["status"] != "EXACT" or ganak["status"] != "EXACT" or
        crc["models"] != ganak["models"] or
        crc["backend"] != "conflict_walsh"):
        raise AssertionError(f"wrong or incomplete exact count: {crc}, {ganak}")
    if count_signed_cnf_crc(
            source, n, max_inclusion_subsets=2,
            enable_defect_oracle=True) is not None:
        raise AssertionError("coherent-only backend accepted a sign exception")
    return {
        "n": n, "pattern": pattern, "exceptions": exceptions,
        "clauses": len(source), "crc": crc, "ganak": ganak,
        "ganak_engine_over_crc_ms":
            round(ganak["counter_wall_ms"] / crc["median_ms"], 3),
    }


def main():
    rows = []
    for n in (8, 12, 20, 28):
        for pattern in ("dispersed", "tetrahedron"):
            for s in (1, 2):
                row = run_case(n, pattern, s)
                rows.append(row)
                print(json.dumps(row, sort_keys=True), flush=True)
    print(json.dumps({
        "summary": "W-CRC-006 bounded mixed-polarity exact pilot",
        "cases": len(rows), "crc_exact": len(rows),
        "ganak_exact": len(rows),
        "claim": "restricted_symmetry_defect_only_not_general_sat",
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
