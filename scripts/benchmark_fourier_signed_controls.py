"""W-CROSSDOMAIN-009: fixed-primal-graph signed Fourier-spectrum controls.

Research truth-table orchestration only; W-CROSSDOMAIN-008 implements the
component-factorized Fourier projection in Rust. No novelty/speedup inference.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from functools import lru_cache
import json


EDGES = ((1, 2), (1, 3), (1, 4), (2, 3), (2, 5), (4, 6), (5, 6))
# The first, second and fourth clauses form the actual graph triangle 1-2-3.
CYCLE = (0, 1, 3)
NVARS = 6


def signed_source(signing: int) -> list[list[int]]:
    return [[u if signing & (1 << (2 * j)) else -u,
             v if signing & (1 << (2 * j + 1)) else -v]
            for j, (u, v) in enumerate(EDGES)]


def cycle_spectrum(signing: int) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """(all weights, triangle-even weights), both with absolute counts."""
    all_weights = [0] * (len(EDGES) + 1)
    cycle_even = [0] * (len(EDGES) + 1)
    for assignment in range(1 << NVARS):
        violations = 0
        cycle_syndrome = 0
        for j, (u, v) in enumerate(EDGES):
            satisfied = bool((assignment >> (u - 1)) & 1) == bool((signing >> (2 * j)) & 1)
            satisfied |= bool((assignment >> (v - 1)) & 1) == bool((signing >> (2 * j + 1)) & 1)
            if not satisfied:
                violations += 1
                if j in CYCLE:
                    cycle_syndrome ^= 1
        all_weights[violations] += 1
        if not cycle_syndrome:
            cycle_even[violations] += 1
    return tuple(all_weights), tuple(cycle_even)


def flip_source_variable(signing: int, variable: int) -> int:
    """Gauge transform: negate every occurrence of one source variable."""
    for j, (u, v) in enumerate(EDGES):
        if u == variable:
            signing ^= 1 << (2 * j)
        if v == variable:
            signing ^= 1 << (2 * j + 1)
    return signing


def canonical_gauge_signing(signing: int) -> int:
    """Fix the first literal incidence of each variable to negative polarity.

    Variable flips act on disjoint literal-incidence bits and commute. Every
    fully supported variable removes one independent signing bit.
    """
    for variable in range(1, NVARS + 1):
        anchor = next((2 * j + position
                       for j, edge in enumerate(EDGES)
                       for position, v in enumerate(edge) if v == variable), None)
        if anchor is not None and signing & (1 << anchor):
            signing = flip_source_variable(signing, variable)
    return signing


@lru_cache(maxsize=1)
def audit() -> dict:
    by_model_count: dict[int, set[tuple[int, ...]]] = defaultdict(set)
    by_energy: dict[tuple[int, ...], dict[tuple[int, ...], int]] = defaultdict(dict)
    for signing in range(1 << (2 * len(EDGES))):
        weights, even = cycle_spectrum(signing)
        by_model_count[weights[0]].add(weights)
        by_energy[weights].setdefault(even, signing)

    witnesses = []
    for weights, spectrums in sorted(by_energy.items()):
        if len(spectrums) < 2:
            continue
        ((even_a, signing_a), (even_b, signing_b)) = list(spectrums.items())[:2]
        witnesses.append({
            "models": weights[0], "energy_profile": list(weights),
            "signing_a": signing_a, "signing_b": signing_b,
            "cycle_even_a": list(even_a), "cycle_even_b": list(even_b),
            "source_a": signed_source(signing_a),
            "source_b": signed_source(signing_b),
        })
    gauge_controls = []
    for signing in (0, 1, 113, (1 << (2 * len(EDGES))) - 1):
        for variable in range(1, NVARS + 1):
            transformed = flip_source_variable(signing, variable)
            gauge_controls.append(cycle_spectrum(signing) == cycle_spectrum(transformed))

    gauge_classes = Counter(canonical_gauge_signing(signing)
                            for signing in range(1 << (2 * len(EDGES))))
    quotient_spectra = {cycle_spectrum(signing) for signing in gauge_classes}

    return {
        "experiment": "W-CROSSDOMAIN-009",
        "graph": [list(edge) for edge in EDGES],
        "triangle_parity_row_zero_based": list(CYCLE),
        "signings": 1 << (2 * len(EDGES)),
        "variables": NVARS,
        "source_clauses": len(EDGES),
        "distinct_model_counts": len(by_model_count),
        "distinct_energy_profiles": len(by_energy),
        "distinct_cycle_spectra": sum(len(spectrums) for spectrums in by_energy.values()),
        "energy_profiles_with_multiple_cycle_spectra": len(witnesses),
        "max_energy_profiles_per_fixed_model_count": max(map(len, by_model_count.values())),
        "gauge_controls_passed": sum(gauge_controls),
        "gauge_controls_total": len(gauge_controls),
        "gauge_orbits": len(gauge_classes),
        "gauge_orbit_size_min": min(gauge_classes.values()),
        "gauge_orbit_size_max": max(gauge_classes.values()),
        "quotient_distinct_cycle_spectra": len(quotient_spectra),
        "quotient_matches_full_spectra": len(quotient_spectra)
            == sum(len(spectrums) for spectrums in by_energy.values()),
        "first_matched_energy_witness": witnesses[0] if witnesses else None,
        "claim_boundary": "finite exhaustive source experiment, no general complexity or speedup claim",
    }


def main() -> None:
    print(json.dumps(audit(), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
