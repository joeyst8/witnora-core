"""Compare bounded exact ANF counters on identical source/sketch systems.

Cached-cofactor/component splitting is a separate algorithmic search
strategy. Same-equation model counts are always checked for equality.
The disjoint-block case measures structural scope exploitation, not
general dense 3-SAT speedups.
"""
from __future__ import annotations

from statistics import median
from time import perf_counter
import tracemalloc

from scripts.generate_glucose_dense_3sat_lean import find_case, random_three_cnf
from witnora_core.anf_structured_counter import count_common_zeros_structured
from witnora_core.geometry_aware_parity import geometry_aware_sparse_sketch
from witnora_core.violation_image_anf import (
    ANFCountingBudgetExceeded, count_common_zeros,
    row_violation_polynomials, source_violation_polynomials,
)


def run_counter(label: str, equations, nvars: int, method,
                max_states: int = 5_000) -> int | None:
    timings: list[float] = []
    peaks: list[float] = []
    answer: int | None = None
    exemplar = None
    for _ in range(3):
        tracemalloc.start()
        start = perf_counter()
        try:
            result = method(equations, nvars, max_states=max_states)
        except ANFCountingBudgetExceeded:
            elapsed = 1000 * (perf_counter() - start)
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            print(f"{label} BUDGET_EXCEEDED at {max_states} states "
                  f"elapsed_ms={elapsed:.3f} peak_kib={peak/1024:.1f}",
                  flush=True)
            return None
        elapsed = 1000 * (perf_counter() - start)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        if answer is not None and answer != result.satisfying_assignments:
            raise AssertionError("non-deterministic count")
        answer = result.satisfying_assignments
        exemplar = result
        timings.append(elapsed)
        peaks.append(peak / 1024)
    extras = ""
    if hasattr(exemplar, "component_splits"):
        extras = (f" splits={exemplar.component_splits}"
                  f" forced={exemplar.forced_assignments}"
                  f" cofactor_hits={exemplar.cofactor_hits}"
                  f" cofactor_entries={exemplar.cofactor_entries}")
    print(f"{label} count={answer} states={exemplar.unique_states} "
          f"memo_hits={exemplar.memo_hits}{extras} "
          f"median_ms={median(timings):.3f} "
          f"peak_kib_median={median(peaks):.1f}", flush=True)
    return answer


def compare(label: str, equations, nvars: int) -> None:
    original = run_counter(f"{label} baseline", equations, nvars,
                           count_common_zeros)
    structured = run_counter(f"{label} structured", equations, nvars,
                             count_common_zeros_structured)
    if original is not None and structured is not None and original != structured:
        raise AssertionError(f"two ANF counters disagree: {label}")


def main() -> None:
    print("EXACT ANF COUNTER COMPARISON (three timed runs per method)", flush=True)
    for n, m in ((4, 5), (5, 7), (6, 9)):
        source = random_three_cnf(n, m, 730000 + n, planted=True)
        sketch = geometry_aware_sparse_sketch(source, n)
        compare(f"{n}v{m}c source", source_violation_polynomials(source, n), n)
        compare(f"{n}v{m}c sketch", row_violation_polynomials(source, sketch), n)
    for n, m in ((8, 54), (10, 66)):
        for planted in (False, True):
            source, _ = find_case(n, m, planted=planted)
            sketch = geometry_aware_sparse_sketch(source, n)
            suffix = "planted" if planted else "unsat"
            compare(f"{n}v{m}c {suffix} source",
                    source_violation_polynomials(source, n), n)
            compare(f"{n}v{m}c {suffix} sketch",
                    row_violation_polynomials(source, sketch), n)

    block = random_three_cnf(6, 9, 730006, planted=True)
    for nblocks in (3, 4):
        extended = [[(abs(lit) + 6 * j) * (1 if lit > 0 else -1)
                     for lit in clause]
                    for j in range(nblocks) for clause in block]
        source_eqs = source_violation_polynomials(extended, 6 * nblocks)
        print(f"DISJOINT {nblocks}x6v-block PRODUCT STRUCTURE", flush=True)
        compare(f"disjoint{nblocks} source", source_eqs, 6 * nblocks)
    print("All reported exact counts preserve their own equation system. "
          "No general SAT polynomial-time claim.", flush=True)


if __name__ == "__main__":
    main()
