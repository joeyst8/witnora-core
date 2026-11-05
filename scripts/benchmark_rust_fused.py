"""R-008: end-to-end one-call Rust fused vs staged Rust and Ganak.

Both measured arms begin with the original source CNF, include extraction,
preprocessing, affine/left/right counting, and report whole-call latency.
The single-call native arm makes no Python mathematical decisions.
"""
from __future__ import annotations

import json

from scripts.benchmark_crc_scaling import measured
from scripts.benchmark_crc_highcount import independent_ganak
from tests.test_crc_rust_fused import or_xor_groups
from witnora_core.crc_source import count_signed_cnf_crc


def forcing_source(n):
    source = []
    for u in range(1, n):
        for v in range(u + 1, n + 1):
            source.append([u, v])
            source.append([u, -v])
    source.extend([[v] for v in range(1, n)])
    return source, n, 2


def run_case(name, clauses, n, expected):
    common = {
        "source_preprocessor": "rust_adaptive",
        "max_spectrum_terms": 4096,
        "max_inclusion_subsets": 4096,
        "max_preprocess_passes": 64,
        "max_preprocess_clause_visits": 1000000,
        "max_rust_coefficient_operations": 2000000,
    }

    def timed(fused):
        if fused:
            got = count_signed_cnf_crc(
                clauses, n, source_backend="rust_fused", **common)
        else:
            got = count_signed_cnf_crc(
                clauses, n, source_backend="pipeline",
                source_extractor="rust", left_backend="rust",
                coefficient_backend="rust_inclusion_exclusion", **common)
        if got is None:
            return None
        return (got.models, got.coefficient_stats.left_fourier_terms,
                "rust_fused" if fused else "staged_rust")

    staged = measured(lambda: timed(False), repeats=2, seconds=12)
    fused = measured(lambda: timed(True), repeats=2, seconds=12)
    ganak = independent_ganak(clauses, n, seconds=15)
    for label, result in (("staged_rust", staged), ("fused_rust", fused), ("ganak", ganak)):
        if result.get("status") != "EXACT" or result.get("models") != expected:
            raise AssertionError(
                f"R-008 {name} {label}: expected {expected}, got {result}")
    return {
        "name": name, "nvars": n, "clauses": len(clauses),
        "expected_models": str(expected), "staged_rust": staged,
        "fused_rust": fused, "ganak": ganak,
        "fused_over_staged_wall_time": round(
            fused["median_ms"] / staged["median_ms"], 3)
            if staged["median_ms"] else None,
        "full_source_path_timed": True,
        "independent_exact_counter": "Ganak",
    }


def main():
    results = []
    for groups in (4, 8, 16, 20):
        for xor_blocks in (0, 1, 3, 6):
            if xor_blocks > groups:
                continue
            clauses, n, expected = or_xor_groups(groups, xor_blocks)
            result = run_case(
                f"or_xor_groups_{groups}_xor_{xor_blocks}", clauses, n, expected)
            results.append(result)
            print(json.dumps(result, sort_keys=True), flush=True)
    for n in (8, 32, 64):
        clauses, _, expected = forcing_source(n)
        result = run_case(f"forcing_{n}", clauses, n, expected)
        results.append(result)
        print(json.dumps(result, sort_keys=True), flush=True)
    med = sorted(row["fused_over_staged_wall_time"] for row in results)
    summary = {
        "summary": "R-008 fused source-CNF exact Rust counting",
        "verified_cases": len(results), "independent_ganak_agreements": len(results),
        "median_fused_over_staged": med[len(med) // 2],
        "fused_faster_cases": sum(r["fused_over_staged_wall_time"] < 1 for r in results),
        "source_to_count_measured": True,
        "no_general_sat_speedup_claim": True,
    }
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
