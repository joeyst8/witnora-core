"""R-007: native GF(2) projection+left Fourier vs Python and Ganak.

Both timed arms execute the complete affine/boundary coefficient path,
including R-006 Rust right Walsh coefficients, and differ ONLY in the
left projection/spectrum backend. The original source CNF (local XOR
gadget clauses + 3-OR clauses) is independently counted by Ganak.
Earlier source preprocessing/extraction is intentionally not timed.
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
    internal = tuple(range(n + 1, n + xor_blocks + 1))
    residual = []
    rows = []
    source = []
    for group in range(groups):
        triple = tuple(range(3 * group + 1, 3 * group + 4))
        residual.append(triple)
        source.append(triple)
        if group < xor_blocks:
            t = internal[group]
            # Two equations imply a^b^c = 0 and uniquely determine t.
            rows.extend((
                ((1 << (t - 1)) | (1 << (triple[0] - 1))
                 | (1 << (triple[1] - 1)), 0),
                ((1 << (t - 1)) | (1 << (triple[2] - 1)), 0),
            ))
            source.extend(_xor_cnf(triple, 0))
    expected = (3**xor_blocks) * (7**(groups - xor_blocks))
    def count(backend):
        got = count_asymmetric_boundary(
            rows, internal, boundary, residual,
            max_spectrum_terms=128, max_inclusion_subsets=2 * groups,
            left_backend=backend,
            coefficient_backend="rust_inclusion_exclusion",
            max_rust_coefficient_operations=100000,
        )
        if got is None:
            return None
        return (got.models, got.left_fourier_terms,
                "left_" + backend)
    py = measured(lambda: count("python"), repeats=3, seconds=5)
    native = measured(lambda: count("rust"), repeats=3, seconds=5)
    ganak = independent_ganak(source, n, seconds=10)
    for label, got in (("python", py), ("rust", native), ("ganak", ganak)):
        if got["status"] != "EXACT" or got["models"] != expected:
            raise AssertionError(
                f"{label} mismatch n={n} xor_blocks={xor_blocks}: {got}"
            )
    return {
        "n": n, "independent_or_components": groups,
        "projected_xor_blocks": xor_blocks,
        "internal_variables": len(internal),
        "expected_exact_models": expected,
        "python_left_rust_right": py,
        "rust_left_rust_right": native,
        "ganak": ganak,
        "native_over_python_total": round(
            native["median_ms"] / py["median_ms"], 3),
        "source_preprocessing_not_timed": True,
        "right_native_backend_identical": True,
    }


def main():
    rows = []
    for groups in (4, 8, 16, 20):
        for xor_blocks in (0, 1, 3, 6):
            if xor_blocks > groups:
                continue
            row = run(groups, xor_blocks)
            rows.append(row)
            print(json.dumps(row, sort_keys=True), flush=True)
    print(json.dumps({
        "summary": "R-007 exact GF(2) projection and sparse Fourier",
        "cases": len(rows),
        "matched_python_analytic_and_ganak": len(rows),
        "no_general_sat_performance_claim": True,
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
