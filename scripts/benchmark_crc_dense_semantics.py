"""W-CRC-017 dense primal graph with different source algebra.

Same complete primal K_n graph, but different signed CNF semantics:
consistent binary parity has 2 models; one contradictory parity edge
has 0; positive all-pairs OR has n+1; planted mixed-sign OR is general.
Uses existing exact source-affine and orbit backends, without claiming
a new rank algorithm or complexity theorem.
"""
from __future__ import annotations

from itertools import combinations, product
import json
import random

from scripts.benchmark_crc_scaling import measured
from scripts.benchmark_crc_highcount import independent_ganak
from witnora_core.crc_source import count_signed_cnf_crc


def dense_source(n, family, seed=17017):
    rng = random.Random(seed)
    polarity = {v: rng.randrange(2) for v in range(1, n + 1)}
    source = []
    for u, v in combinations(range(1, n + 1), 2):
        if family.startswith("parity"):
            rhs = polarity[u] ^ polarity[v]
            if family == "parity_inconsistent" and (u, v) == (1, n):
                rhs ^= 1
            for a, b in product((0, 1), repeat=2):
                if a ^ b != rhs:
                    source.append((u if a == 0 else -u,
                                   v if b == 0 else -v))
        elif family == "positive_or":
            source.append((u, v))
        elif family == "signed_or":
            first = u if rng.randrange(2) else -u
            source.append((first, v))
        else:
            raise ValueError(family)
    return source


def run(n, family):
    source = dense_source(n, family)
    expected = (
        2 if family == "parity_consistent" else
        0 if family == "parity_inconsistent" else
        n + 1 if family == "positive_or" else None
    )
    def crc():
        result = count_signed_cnf_crc(
            source, n, max_inclusion_subsets=2,
            max_coefficient_states=20000,
            enable_orbit_oracle=True)
        if result is None:
            return None
        return (result.models, result.extracted_affine_rows,
                result.coefficient_stats.coefficient_backend)

    got = measured(crc, repeats=2, seconds=4)
    ganak = independent_ganak(source, n, seconds=4)
    if expected is not None and (
        got["status"] != "EXACT" or got["models"] != expected):
        raise AssertionError(f"dense analytic contradiction: {family}, n={n}, {got}")
    if ganak["status"] == "EXACT" and expected is not None:
        if ganak["models"] != expected:
            raise AssertionError(f"dense Ganak analytic contradiction: {family},n={n}")
    if got["status"] == ganak["status"] == "EXACT":
        if got["models"] != ganak["models"]:
            raise AssertionError(f"CRC/Ganak disagreement: {family},n={n}")
    return {
        "n": n, "family": family,
        "complete_primal_edges": n * (n - 1) // 2,
        "source_clauses": len(source),
        "analytic_expected": expected,
        "crc": got, "ganak": ganak,
        "crc_over_ganak_engine": (
            round(got["median_ms"] / ganak["counter_wall_ms"], 3)
            if got["status"] == ganak["status"] == "EXACT"
            and ganak["counter_wall_ms"] else None),
    }


def main():
    rows = []
    for n in (8, 16, 32, 64):
        for family in (
            "parity_consistent", "parity_inconsistent",
            "positive_or", "signed_or",
        ):
            row = run(n, family)
            rows.append(row)
            print(json.dumps(row, sort_keys=True), flush=True)
    print(json.dumps({
        "summary": "W-CRC-017 equal-primal-graph algebraic structure test",
        "cases": len(rows),
        "crc_exact": sum(r["crc"]["status"] == "EXACT" for r in rows),
        "ganak_exact": sum(r["ganak"]["status"] == "EXACT" for r in rows),
        "analytic_verified": sum(r["analytic_expected"] is not None
                                 for r in rows),
        "no_novel_complexity_claim": True,
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
