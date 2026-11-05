"""Real exact counting before/after certified GF(2) sparse-row removal.

Small cases contract the COMPLETE auxiliary polynomial, not just t^0.
Large cases build/verify a row-space basis without assignment enumeration,
but DO NOT perform tensor contraction at large variable counts.
"""
from __future__ import annotations

from time import perf_counter
import tracemalloc

from scripts.generate_glucose_dense_3sat_lean import random_three_cnf
from tests.test_exact_tensor_counting import collision_sketch
from witnora_core.exact_tensor_counting import (
    ContractionBudgetExceeded, count_auxiliary_weight_polynomial,
)
from witnora_core.geometry_aware_parity import geometry_aware_sparse_sketch
from witnora_core.gf2_sparse_row_basis import build_sparse_parity_basis


def measure(label: str, source, sketch, basis=None) -> tuple[int | None, str]:
    tracemalloc.start()
    start = perf_counter()
    try:
        result = count_auxiliary_weight_polynomial(
            source, sketch, basis=basis,
            max_bucket_variables=11, max_visited_assignments=1_000_000)
        ms = (perf_counter() - start) * 1000
        _, peak = tracemalloc.get_traced_memory()
        count = result.coefficients[0] if result.coefficients else 0
        print(f"{label} OK {count} {len(result.coefficients)} "
              f"{result.max_bucket_variables} {result.visited_assignments} "
              f"{ms:.3f} {peak / 1024:.1f}", flush=True)
        return count, "ok"
    except ContractionBudgetExceeded as exc:
        ms = (perf_counter() - start) * 1000
        _, peak = tracemalloc.get_traced_memory()
        print(f"{label} BUDGET_EXCEEDED NA NA NA NA "
              f"{ms:.3f} {peak/1024:.1f} # {exc}", flush=True)
        return None, "budget"
    finally:
        tracemalloc.stop()


def main() -> None:
    print("case representation result source_count poly_terms "
          "max_bucket_bits visited_assignments ms traced_peak_kib",
          flush=True)
    source, sketch = collision_sketch()
    cases = [("four-collision", source, 4, sketch)]
    for n, m in ((4, 5), (5, 7), (6, 9), (8, 12)):
        source = random_three_cnf(n, m, 730000 + n, planted=True)
        cases.append((f"{n}v{m}c", source, n,
                      geometry_aware_sparse_sketch(source, n)))
    for label, source, n, sketch in cases:
        cert = build_sparse_parity_basis(sketch)
        print(f"{label} basis original_rows={len(sketch.rows)} "
              f"rank={cert.rank} nullity={cert.nullity} "
              f"max_width={max(map(len, cert.rows), default=0)}",
              flush=True)
        before, bstatus = measure(f"{label} original", source, sketch)
        after, astatus = measure(f"{label} reduced", source, sketch, cert)
        if bstatus == "ok" and astatus == "ok" and before != after:
            raise AssertionError(f"GF(2) basis changed exact source count {label}")
    print("LARGE CONSTRUCTION ONLY (NO SAT/COUNTING):", flush=True)
    for n, m in ((32, 224), (96, 576), (256, 1536)):
        source = random_three_cnf(n, m, 630000 + n, planted=True)
        sketch = geometry_aware_sparse_sketch(source, n)
        start = perf_counter()
        cert = build_sparse_parity_basis(sketch)
        ms = (perf_counter() - start) * 1000
        print(f"{n}v{m}c GF2-basis {len(sketch.rows)} "
              f"{cert.rank} {cert.nullity} {ms:.3f} ms", flush=True)
    print("No large SAT/counting runtime or general polynomial algorithm established.",
          flush=True)


if __name__ == "__main__":
    main()
