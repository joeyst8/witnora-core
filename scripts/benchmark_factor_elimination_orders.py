"""Frozen SAT factor graph elimination order experiment.

The objective is to identify whether separating clause-violation bits
helps when the contraction ORDER knows which variables are original.
These are greedy graph-width heuristics; no SAT solving, counting,
tensor evaluations or Lean proofs occur in this benchmark.
"""
from __future__ import annotations

from time import perf_counter

from scripts.generate_glucose_dense_3sat_lean import random_three_cnf
from witnora_core.aux_violation_tensors import (
    auxiliary_factor_scopes, direct_parity_factor_scopes,
)
from witnora_core.factor_elimination_orders import elimination_order
from witnora_core.geometry_aware_parity import geometry_aware_sparse_sketch
from witnora_core.sparse_parity_checks import min_degree_elimination_width


def main() -> None:
    print("n clauses representation strategy vertices factors "
          "width fill_edges order_ms")
    for n, m in ((32, 224), (96, 576), (256, 1536)):
        source = random_three_cnf(n, m, 630000 + n, planted=True)
        sketch = geometry_aware_sparse_sketch(source, n)
        source_factors = [{abs(lit) for lit in clause} for clause in source]
        direct_factors = direct_parity_factor_scopes(source, sketch)
        aux_factors = auxiliary_factor_scopes(source, sketch)
        source_width = min_degree_elimination_width(source_factors, n)
        flat_width = min_degree_elimination_width(direct_factors, n)
        print(f"{n} {m} source min_degree {n} {m} "
              f"{source_width} NA NA")
        print(f"{n} {m} flat min_degree {n} {len(direct_factors)} "
              f"{flat_width} NA NA")
        for strategy in ("min_degree", "source_first", "aux_first", "beam_fill"):
            start = perf_counter()
            result = elimination_order(
                aux_factors, n + m, nsource=n, mode=strategy, beam=8)
            millis = (perf_counter() - start) * 1000
            print(f"{n} {m} aux {strategy} {n+m} {len(aux_factors)} "
                  f"{result.induced_width} {result.added_fill_edges} "
                  f"{millis:.3f}", flush=True)
    print("Heuristic graph diagnostics only: no verified runtime speedup "
          "or exact contraction benchmark was executed.")


if __name__ == "__main__":
    main()
