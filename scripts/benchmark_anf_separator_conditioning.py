"""Measure exact small-separator conditioning on connected CNF families.

All comparisons solve the same source ANF equations. For each planted
block family the reference model count is computed from independent
six-variable local enumerations, not from the new counter.
"""
from __future__ import annotations

from statistics import median
from time import perf_counter
import tracemalloc

from scripts.generate_glucose_dense_3sat_lean import find_case
from tests.test_anf_separator_conditioning import (
    bridge_case, independent_bridge_oracle,
)
from witnora_core.anf_separator_conditioning import (
    count_common_zeros_conditioned,
)
from witnora_core.anf_structured_counter import count_common_zeros_structured
from witnora_core.aux_violation_tensors import (
    auxiliary_weight_profile_small, exact_source_models_small,
)
from witnora_core.geometry_aware_parity import geometry_aware_sparse_sketch
from witnora_core.violation_image_anf import (
    ANFCountingBudgetExceeded, row_violation_polynomials,
    source_violation_polynomials,
)


def measure(label: str, equations, nvars: int, method,
            expected: int | None = None, max_states: int = 5_000) -> int | None:
    ms: list[float] = []
    peaks: list[float] = []
    model_count = None
    result = None
    for _ in range(3):
        tracemalloc.start()
        before = perf_counter()
        try:
            r = method(equations, nvars, max_states=max_states)
        except ANFCountingBudgetExceeded:
            elapsed = (perf_counter() - before) * 1000
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            print(f"{label} BUDGET_EXCEEDED limit={max_states} "
                  f"ms={elapsed:.3f} peak_kib={peak/1024:.1f}",
                  flush=True)
            return None
        elapsed = (perf_counter() - before) * 1000
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        if model_count is not None and model_count != r.satisfying_assignments:
            raise AssertionError("non-deterministic exact count")
        model_count, result = r.satisfying_assignments, r
        ms.append(elapsed)
        peaks.append(peak / 1024)
    if expected is not None and model_count != expected:
        raise AssertionError(f"wrong #SAT count on {label}: {model_count} != {expected}")
    state_count = getattr(result, "unique_states",
                          getattr(result, "total_unique_states", None))
    detail = ""
    if hasattr(result, "separator_found"):
        detail = (f" separator={result.separator} "
                  f"found={result.separator_found} branches={result.branches}"
                  f" splits={result.total_component_splits}"
                  f" checked={result.separator_candidates_checked}")
    print(f"{label} models={model_count} states={state_count} "
          f"median_ms={median(ms):.3f} "
          f"peak_kib={median(peaks):.1f}{detail}", flush=True)
    return model_count


def main() -> None:
    print("SEPARATOR CONDITIONING ON CONNECTED 3-CNF BLOCKS WITH 2-CNF BRIDGES",
          flush=True)
    for connectors in (1, 2):
        for nblocks in (3, 4):
            source, n = bridge_case(nblocks, connectors)
            eqs = source_violation_polynomials(source, n)
            expected = independent_bridge_oracle(nblocks, connectors)
            label = f"{connectors}bridge-{nblocks}blocks-{n}v"
            print(f"{label} independent_local_oracle={expected}", flush=True)
            measure(label+" structured", eqs, n,
                    count_common_zeros_structured, expected)
            measure(label+" conditioned", eqs, n,
                    count_common_zeros_conditioned, expected)

    print("DENSE CONNECTED 3SAT CONTROLS (NO ASSUMED SMALL SEPARATOR)",
          flush=True)
    for n, m in ((8, 54), (10, 66)):
        for planted in (False, True):
            source, _ = find_case(n, m, planted=planted)
            sketch = geometry_aware_sparse_sketch(source, n)
            prefix = f"dense{n}v{m}c-{'sat' if planted else 'unsat'}"
            for suffix, eqs, expected in (
                ("source", source_violation_polynomials(source, n),
                 exact_source_models_small(source, n)),
                ("sketch", row_violation_polynomials(source, sketch),
                 sum(auxiliary_weight_profile_small(source, sketch).coefficients)),
            ):
                label = prefix + "-" + suffix
                original = measure(label+" structured", eqs, n,
                                   count_common_zeros_structured, expected)
                conditioned = measure(label+" conditioned", eqs, n,
                                      count_common_zeros_conditioned, expected)
                if original is not None and conditioned is not None and original != conditioned:
                    raise AssertionError("separators changed exact count")
    print("This is bounded exact conditioning; no general polynomial SAT claim.",
          flush=True)


if __name__ == "__main__":
    main()
