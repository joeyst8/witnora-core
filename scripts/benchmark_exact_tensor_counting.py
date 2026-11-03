"""ACTUAL exact contraction pilot, limited by explicit polynomial-table budgets.

Includes factor construction, contraction, and Python traced peak memory;
compares original CNF #SAT to sparse-parity auxiliary Z_H(t) extraction.
This is NOT competitive industrial SAT/#SAT benchmarking.
"""
from __future__ import annotations

from time import perf_counter
import tracemalloc

from scripts.generate_glucose_dense_3sat_lean import random_three_cnf
from tests.test_exact_tensor_counting import collision_sketch
from witnora_core.aux_violation_tensors import exact_source_models_small
from witnora_core.exact_tensor_counting import (
    ContractionBudgetExceeded, count_auxiliary_weight_polynomial,
    count_source_exact,
)
from witnora_core.geometry_aware_parity import geometry_aware_sparse_sketch


def measured(label: str, call) -> tuple[int | None, str]:
    tracemalloc.start()
    start = perf_counter()
    try:
        result = call()
        duration = (perf_counter() - start) * 1000
        _, peak = tracemalloc.get_traced_memory()
        count = result.coefficients[0] if result.coefficients else 0
        print(f"{label} ok {count} {len(result.coefficients)} "
              f"{result.max_bucket_variables} {result.visited_assignments} "
              f"{result.peak_table_entries} {duration:.3f} {peak/1024:.1f}",
              flush=True)
        return count, "ok"
    except ContractionBudgetExceeded as exc:
        duration = (perf_counter() - start) * 1000
        _, peak = tracemalloc.get_traced_memory()
        print(f"{label} BUDGET_EXCEEDED NA NA NA NA NA "
              f"{duration:.3f} {peak/1024:.1f} # {exc}", flush=True)
        return None, "budget"
    finally:
        tracemalloc.stop()


def main() -> None:
    print("case representation status sat_count polynomial_terms "
          "max_bucket_bits visited_assignments peak_table_entries ms "
          "peak_traced_kib", flush=True)
    cases = [
        ("triple3", [[1, 2, 3], [1, -2, 3], [-1, 2, 3]], 3, None),
        ("four-collision", *collision_sketch(), None),
    ]
    # The four-collision row above is expanded differently below to
    # retain a uniform (label, source, nvars, sketch) structure.
    cases = [cases[0]]
    source, sketch = collision_sketch()
    cases.append(("four-collision", source, 4, sketch))
    for n, m in ((4, 5), (5, 7), (6, 9), (8, 12)):
        source = random_three_cnf(n, m, 730000 + n, planted=True)
        cases.append((f"{n}v{m}c", source, n, None))

    for label, source, n, existing in cases:
        sketch = existing or geometry_aware_sparse_sketch(source, n)
        source_count, source_status = measured(
            f"{label} source",
            lambda: count_source_exact(
                source, n, max_bucket_variables=11,
                max_visited_assignments=1_000_000))
        aux_count, aux_status = measured(
            f"{label} aux",
            lambda: count_auxiliary_weight_polynomial(
                source, sketch, max_bucket_variables=11,
                max_visited_assignments=1_000_000))
        if source_status == "ok" and aux_status == "ok":
            expected = exact_source_models_small(source, n)
            if source_count != aux_count or source_count != expected:
                raise AssertionError(f"source/aux/independent count mismatch {label}")
    print("Each successful auxiliary result computes the complete exact "
          "Z_H(t) polynomial, not merely its t^0 term. "
          "The first coefficient is #SAT(source).", flush=True)


if __name__ == "__main__":
    main()
