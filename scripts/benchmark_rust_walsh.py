"""R-006: exact right Walsh coefficient batching vs Python and Ganak.

Both timed implementations include the left affine projection and
spectrum, right CNF normalization, component discovery and coefficient
combination. This bench intentionally isolates the coefficient engine
from source-XOR extraction and prior Rust preprocessing.
"""
from __future__ import annotations

import json

from scripts.benchmark_crc_scaling import measured
from scripts.benchmark_crc_highcount import independent_ganak
from witnora_core.crc_boundary import count_asymmetric_boundary
from witnora_core.crc_source import _xor_cnf


def run(groups: int, xor_blocks: int):
    n = 3 * groups
    boundary = tuple(range(1, n + 1))
    residual = []
    rows = []
    source = []
    for g in range(groups):
        triple = tuple(range(3 * g + 1, 3 * g + 4))
        residual.append(triple)  # All-positive OR: 7/8 models.
        source.append(triple)
        if g < xor_blocks:
            rows.append((sum(1 << (v - 1) for v in triple), 0))
            source.extend(_xor_cnf(triple, 0))
    expected = (3**xor_blocks) * (7**(groups - xor_blocks))
    def count(backend):
        got = count_asymmetric_boundary(
            rows, (), boundary, residual,
            max_spectrum_terms=64, max_inclusion_subsets=2 * groups,
            coefficient_backend=backend,
            max_rust_coefficient_operations=10000,
        )
        if got is None:
            return None
        return (got.models, got.right_violation_terms,
                got.coefficient_backend)
    py = measured(lambda: count("python"), repeats=3, seconds=5)
    native = measured(lambda: count("rust_inclusion_exclusion"),
                      repeats=3, seconds=5)
    ganak = independent_ganak(source, n, seconds=10)
    for label, got in (("python", py), ("rust", native), ("ganak", ganak)):
        if got["status"] != "EXACT" or got["models"] != expected:
            raise AssertionError(
                f"{label} failed analytic count {expected} "
                f"(n={n}, xor_blocks={xor_blocks}): {got}"
            )
    return {
        "n": n, "groups": groups, "affine_xor_blocks": xor_blocks,
        "residual_or_clauses": groups,
        "source_xor_clauses": 4 * xor_blocks,
        "expected_exact_models": expected,
        "python_right_coefficient_engine": py,
        "rust_right_coefficient_engine": native,
        "ganak": ganak,
        "native_over_python_total": round(
            native["median_ms"] / py["median_ms"], 3),
        "source_preprocessing_not_timed": True,
        "full_affine_and_coefficient_pipeline_timed": True,
    }


def main():
    rows = []
    for groups in (4, 8, 16, 20):
        for xor_blocks in (0, 1, 2, 3):
            row = run(groups, xor_blocks)
            rows.append(row)
            print(json.dumps(row, sort_keys=True), flush=True)
    print(json.dumps({
        "summary": "R-006 exact native batch right Walsh coefficients",
        "cases": len(rows),
        "matched_python_analytic_and_ganak": len(rows),
        "no_general_sat_superiority_claim": True,
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
