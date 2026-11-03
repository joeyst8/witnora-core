"""Actual bounded symbolic ANF common-zero counting vs source constraints.

Separately measure nonenumerative ANF construction up to 256 variables.
A nonlinear parity sketch need not be exactly source-CNF-equivalent;
source model and sketch-survivor counts are reported distinctly.
"""
from __future__ import annotations

from time import perf_counter
import tracemalloc

from scripts.generate_glucose_dense_3sat_lean import find_case, random_three_cnf
from witnora_core.aux_violation_tensors import (
    auxiliary_weight_profile_small, exact_source_models_small,
)
from witnora_core.geometry_aware_parity import geometry_aware_sparse_sketch
from witnora_core.violation_image_anf import (
    ANFCountingBudgetExceeded, analyze_parity_anf, count_common_zeros,
    row_violation_polynomials, source_violation_polynomials,
)


def timed_count(label, equations, n: int) -> int | None:
    tracemalloc.start()
    start = perf_counter()
    try:
        r = count_common_zeros(equations, n, max_states=10_000)
        ms = 1000 * (perf_counter() - start)
        _, peak = tracemalloc.get_traced_memory()
        print(f"{label} OK count={r.satisfying_assignments} "
              f"states={r.unique_states} hits={r.memo_hits} "
              f"ms={ms:.3f} peak_traced_kib={peak/1024:.1f}", flush=True)
        return r.satisfying_assignments
    except ANFCountingBudgetExceeded:
        ms = 1000 * (perf_counter() - start)
        _, peak = tracemalloc.get_traced_memory()
        print(f"{label} BUDGET_EXCEEDED ms={ms:.3f} "
              f"peak_traced_kib={peak/1024:.1f}", flush=True)
        return None
    finally:
        tracemalloc.stop()


def main() -> None:
    print("EXACT SYMBOLIC COMMON-ZERO COUNTS:", flush=True)
    samples = []
    for n, m in ((4, 5), (5, 7), (6, 9)):
        source = random_three_cnf(n, m, 730000 + n, planted=True)
        samples.append((f"{n}v{m}c-planted", source, n))
    for n, m in ((8, 54), (10, 66)):
        for planted in (False, True):
            source, _ = find_case(n, m, planted=planted)
            samples.append((f"{n}v{m}c-{('planted' if planted else 'unsat')}",
                            source, n))
    for label, source, n in samples:
        sketch = geometry_aware_sparse_sketch(source, n)
        direct = source_violation_polynomials(source, n)
        parity = row_violation_polynomials(source, sketch)
        start = perf_counter()
        geometry = analyze_parity_anf(source, sketch)
        build_ms = 1000 * (perf_counter() - start)
        print(f"{label} geometry rows={geometry.row_count} "
              f"raw_terms={geometry.raw_row_monomial_occurrences} "
              f"kept_terms={geometry.reduced_row_monomials} "
              f"degree={geometry.maximum_degree} build_ms={build_ms:.3f}",
              flush=True)
        original_count = timed_count(f"{label} sourceANF", direct, n)
        parity_count = timed_count(f"{label} parityANF", parity, n)
        finite_count = exact_source_models_small(source, n)
        survivor_count = sum(auxiliary_weight_profile_small(
            source, sketch).coefficients)
        if original_count is not None and original_count != finite_count:
            raise AssertionError(f"source ANF count mismatch {label}")
        if parity_count is not None and parity_count != survivor_count:
            raise AssertionError(f"parity ANF count mismatch {label}")

    print("LARGE ANF CONSTRUCTION ONLY (NO SAT SOLVING):", flush=True)
    for n, m in ((32, 224), (96, 576), (256, 1536)):
        source = random_three_cnf(n, m, 630000 + n, planted=True)
        sketch = geometry_aware_sparse_sketch(source, n)
        start = perf_counter()
        g = analyze_parity_anf(source, sketch)
        ms = 1000 * (perf_counter() - start)
        print(f"{n}v{m}c symbolic rows={g.row_count} "
              f"raw_terms={g.raw_row_monomial_occurrences} "
              f"kept_terms={g.reduced_row_monomials} "
              f"zeros={g.zero_rows} unique={g.unique_nonzero_rows} "
              f"degree={g.maximum_degree} construction_ms={ms:.3f}",
              flush=True)
    print("These are bounded symbolic counts/constructors, not polynomial-time SAT.",
          flush=True)


if __name__ == "__main__":
    main()
