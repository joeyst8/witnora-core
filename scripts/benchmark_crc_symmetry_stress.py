"""W-CRC-005 negative controls: >r missing clauses and inconsistent signs.

For full positive rank-three CNF with four missing triples, the count
depends on whether the missing triples complete a 4-vertex tetrahedron.
This falsifies any model-count rule depending only on the defect count.
Results use independent exhaustive enumeration and Ganak, not a claim of
a novel general SAT algorithm.
"""
from __future__ import annotations

import itertools
import json
from math import comb

from scripts.benchmark_crc_highcount import independent_ganak
from witnora_core.crc_boundary import _normalized_clauses
from witnora_core.crc_orbit_oracle import query_orbit_walsh
from witnora_core.crc_source import count_signed_cnf_crc


TETRAHEDRON = ((1, 2, 3), (1, 2, 4), (1, 3, 4), (2, 3, 4))
DISPERSED = ((1, 2, 3), (1, 2, 4), (1, 3, 5), (2, 4, 6))


def source_with_defects(n: int, missing, *, signed: bool = False):
    absent = set(missing)
    return tuple(
        tuple(-v if signed and v % 2 == 0 else v for v in triple)
        for triple in itertools.combinations(range(1, n + 1), 3)
        if triple not in absent
    )


def brute_count(clauses, n: int) -> int:
    total = 0
    for bits in range(1 << n):
        if all(any(
            bool(bits & (1 << (abs(literal) - 1))) == (literal > 0)
            for literal in clause
        ) for clause in clauses):
            total += 1
    return total


def run_case(n: int, pattern: str, *, signed: bool = False, conflict: bool = False):
    missing = TETRAHEDRON if pattern == "tetrahedron" else DISPERSED
    source = source_with_defects(n, missing, signed=signed)
    if conflict:
        first = source[0]
        source = ((-first[0], *first[1:]), *source[1:])
    boundary = tuple(range(1, n + 1))
    normalized = _normalized_clauses(source, boundary)
    recognized = query_orbit_walsh(normalized, boundary, (0,))
    if recognized is not None:
        raise AssertionError("orbit oracle accepted out-of-scope defects or signs")
    exact = brute_count(source, n)
    ganak = independent_ganak(source, n, seconds=3)
    if ganak["status"] != "EXACT" or ganak["models"] != exact:
        raise AssertionError(f"Ganak disagreed with enumeration: {ganak}")
    predicted = None
    if not conflict:
        predicted = 1 + n + comb(n, 2) + 4 + int(pattern == "tetrahedron")
        if exact != predicted:
            raise AssertionError(
                f"missing-triple clique count wrong: {exact} != {predicted}"
            )
    fallback = count_signed_cnf_crc(
        source, n, max_spectrum_terms=1024,
        max_inclusion_subsets=128, max_coefficient_states=5000,
        enable_orbit_oracle=True,
    )
    if fallback is not None and fallback.models != exact:
        raise AssertionError("source CRC fallback produced an incorrect count")
    return {
        "n": n, "pattern": pattern, "signed": signed,
        "conflicting_polarity": conflict, "missing_triples": 4,
        "models": exact, "predicted_models": predicted,
        "orbit_recognized": False, "ganak": ganak["status"],
        "crc_fallback": "EXACT" if fallback is not None else "BUDGET",
    }


def main():
    outcomes = []
    for n in (8, 11):
        for pattern, signed, conflict in (
            ("dispersed", False, False),
            ("tetrahedron", True, False),
            ("dispersed", True, True),
        ):
            row = run_case(n, pattern, signed=signed, conflict=conflict)
            outcomes.append(row)
            print(json.dumps(row, sort_keys=True), flush=True)
    print(json.dumps({
        "summary": "W-CRC-005 negative controls",
        "cases": len(outcomes), "all_ganak_exact": True,
        "finding": "four missing triples can contribute an additional "
                   "higher-order compatible flip-set; defect count alone "
                   "does not determine model count",
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
