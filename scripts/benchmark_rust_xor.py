"""R-005: timed native Rust XOR extraction vs Python source reference.

Both source-count timings include the same R-004 adaptive Rust
preprocessing and all PyO3 data copying; they differ ONLY in selecting
the native source XOR extractor. Both exact counts checked by Ganak.
"""
from __future__ import annotations

import json

from scripts.benchmark_crc_equivalent_encodings import equivalent_encoding
from scripts.benchmark_crc_scaling import measured
from scripts.benchmark_crc_highcount import independent_ganak
from witnora_core.crc_source import count_signed_cnf_crc


def run(n, family, variant):
    source = equivalent_encoding(n, family, variant)
    def count(extractor):
        got = count_signed_cnf_crc(
            source, n, max_inclusion_subsets=2,
            max_coefficient_states=20000, enable_orbit_oracle=True,
            source_preprocessor="rust_adaptive",
            source_extractor=extractor)
        if got is None:
            return None
        return (got.models, got.extracted_affine_rows,
                got.coefficient_stats.coefficient_backend)
    python = measured(lambda: count("python"), repeats=2, seconds=5)
    rust = measured(lambda: count("rust"), repeats=2, seconds=5)
    ganak = independent_ganak(source, n, seconds=5)
    for who, item in (("Python", python), ("Rust", rust), ("Ganak", ganak)):
        if item["status"] != "EXACT" or item["models"] != 2:
            raise AssertionError(f"{who} count mismatch: n={n} {family} {variant}: {item}")
    return {
        "n": n, "family": family, "variant": variant,
        "source_clauses": len(source),
        "python_extractor_total": python,
        "rust_extractor_total": rust,
        "ganak": ganak,
        "rust_over_python_total": round(rust["median_ms"] / python["median_ms"], 3),
        "includes_adaptive_source_preprocess": True,
        "includes_native_bridge_conversion": True,
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
        "summary": "R-005 exact native XOR source extraction",
        "cases": len(rows),
        "matched_python_and_ganak": len(rows),
        "no_general_satspeed_claim": True,
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
