"""R-003/R-004: full source preprocessor + adaptive gate versus Ganak.

Compares identical CNFs with and without opt-in native consensus.
Both timings include source parsing; native timing also includes
the PyO3 preprocessing. No preprocessing cost is hidden.
"""
from __future__ import annotations

import json

from scripts.benchmark_crc_equivalent_encodings import equivalent_encoding
from scripts.benchmark_crc_scaling import measured
from scripts.benchmark_crc_highcount import independent_ganak
from witnora_core.crc_source import count_signed_cnf_crc
from witnora_core.crc_rust_preprocess import simplify_source_in_rust


def run(n, family, variant):
    source = equivalent_encoding(n, family, variant)
    def crc(mode):
        got = count_signed_cnf_crc(
            source, n, max_inclusion_subsets=2,
            max_coefficient_states=20000, enable_orbit_oracle=True,
            source_preprocessor=mode)
        if got is None:
            return None
        return (got.models, got.extracted_affine_rows,
                got.coefficient_stats.coefficient_backend)
    raw = measured(lambda: crc("none"), repeats=2, seconds=5)
    native = measured(lambda: crc("rust_consensus"), repeats=2, seconds=5)
    adaptive = measured(lambda: crc("rust_adaptive"), repeats=2, seconds=5)
    ganak = independent_ganak(source, n, seconds=5)
    simplified = simplify_source_in_rust(source, n)
    adapted = simplify_source_in_rust(source, n, adaptive=True)
    if simplified is None or adapted is None:
        raise AssertionError("native simplification budget refused controlled input")
    if native["status"] != "EXACT" or native["models"] != 2:
        raise AssertionError(f"native count missed analytic 2: n={n} {family} {variant}")
    if adaptive["status"] != "EXACT" or adaptive["models"] != 2:
        raise AssertionError(f"adaptive count missed analytic 2: n={n} {family} {variant}")
    if raw["status"] == "EXACT" and raw["models"] != 2:
        raise AssertionError("reference source count wrong")
    if ganak["status"] != "EXACT" or ganak["models"] != 2:
        raise AssertionError("independent Ganak did not match analytic count")
    return {
        "n": n, "family": family, "variant": variant,
        "source_clauses": len(source),
        "rust_simplified_clauses": len(simplified.clauses),
        "rust_consensus_pairs": simplified.consensus_pairs,
        "rust_preprocess_passes": simplified.passes,
        "rust_adaptive_skipped": adapted.skipped,
        "crc_without_preprocess": raw,
        "crc_with_rust_preprocess": native,
        "crc_with_rust_adaptive": adaptive,
        "ganak": ganak,
        "native_total_over_raw_if_both_exact": (
            round(native["median_ms"] / raw["median_ms"], 3)
            if native["status"] == raw["status"] == "EXACT" else None
        ),
        "preprocessing_included_in_native_wall_ms": True,
        "admission_included_in_adaptive_wall_ms": True,
    }


def main():
    rows = []
    for n in (8, 16, 32, 64):
        for family, variant in (
            ("pairwise_forcing", "base"),
            ("pairwise_forcing", "entailed_units"),
            ("pairwise_parity", "base"),
        ):
            row = run(n, family, variant)
            rows.append(row)
            print(json.dumps(row, sort_keys=True), flush=True)
    print(json.dumps({
        "summary": "R-003/R-004 native consensus and adaptive admission before CRC",
        "cases": len(rows),
        "independent_ganak_matches": len(rows),
        "native_exact": sum(r["crc_with_rust_preprocess"]["status"] == "EXACT"
                            for r in rows),
        "raw_incomplete": sum(r["crc_without_preprocess"]["status"] != "EXACT"
                              for r in rows),
        "adaptive_exact": sum(r["crc_with_rust_adaptive"]["status"] == "EXACT"
                              for r in rows),
        "adaptive_skipped": sum(r["rust_adaptive_skipped"] for r in rows),
        "no_general_sat_speedup_claim": True,
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
