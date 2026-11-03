"""W-CRC-010 small separator admits conditional independence in star CNFs.

The unconditional source graph stays connected, but fixing the shared
hub variable removes every cross-group dependency. This is a source-
model-checked, graph-based pilot; it does not solve SAT.
"""
from __future__ import annotations

import json

from scripts.benchmark_crc_scaling import measured
from witnora_core.crc_conditional_independence import (
    audit_conditioned_source_independence,
)
from witnora_core.crc_structural_independence import (
    audit_structural_source_independence,
)


def run(n: int, hub_value: bool):
    hub = n
    clauses = [[v, hub] for v in range(1, n)]
    boundary = tuple(range(1, n + 1))
    left, right = (1, 2), (n - 2, n - 1)
    witness = (1 << n) - 1 if hub_value else (1 << (n - 1)) - 1

    def before():
        got = audit_structural_source_independence(
            clauses, boundary, left, right, witness)
        return None if got is None else (
            int(got.separated), got.clauses_checked, "unconditional")

    def after():
        got = audit_conditioned_source_independence(
            clauses, boundary, left, right, (hub,), witness)
        return None if got is None else (
            int(got.separated_after_conditioning),
            got.residual_clauses, "conditional")

    a = measured(before, repeats=2, seconds=4)
    b = measured(after, repeats=2, seconds=4)
    if (a["status"] != "EXACT" or b["status"] != "EXACT"
        or a["models"] != 0 or b["models"] != 1
        or b["states"] != (0 if hub_value else n - 1)):
        raise AssertionError(f"incorrect graph result: {a}, {b}")
    return {
        "n": n, "clauses": len(clauses), "separator_size": 1,
        "hub_value": int(hub_value),
        "unconditional_audit": a, "conditional_audit": b,
    }


def main():
    rows = []
    for n in (16, 64, 128, 256):
        for hub_value in (False, True):
            row = run(n, hub_value)
            rows.append(row)
            print(json.dumps(row, sort_keys=True), flush=True)
    print(json.dumps({
        "summary": "W-CRC-010 conditioned source-factorization pilot",
        "cases": len(rows), "all_certified": True,
        "no_general_sat_speedup_claim": True,
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
