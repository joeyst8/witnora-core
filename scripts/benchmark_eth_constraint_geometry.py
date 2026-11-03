"""Reproducible diagnostic for non-enumerative dense parity construction.

All displayed timings are single-process local measurements, not a
statistical performance comparison or evidence of fast SAT solving.
"""
from __future__ import annotations

from time import perf_counter

from scripts.generate_glucose_dense_3sat_lean import random_three_cnf
from witnora_core.constraint_geometry import (
    audit_small_collisions, build_dense_random_sketch, row_statistics,
)


def main() -> None:
    print("nvars clauses rows avg_row_width build_ms false_positives")
    for nvars, nclauses in ((8, 54), (12, 84), (32, 224),
                            (96, 576), (256, 1536)):
        source = random_three_cnf(nvars, nclauses, 630000 + nvars,
                                  planted=True)
        start = perf_counter()
        sketch = build_dense_random_sketch(source, nvars,
                                           security_bits=20, seed=73)
        elapsed_ms = (perf_counter() - start) * 1000
        collisions = (str(audit_small_collisions(source, sketch).false_positives)
                      if nvars <= 12 else "NOT_AUDITED")
        print(f"{nvars} {nclauses} {len(sketch.rows)} "
              f"{row_statistics(sketch)[1]:.2f} {elapsed_ms:.3f} "
              f"{collisions}")
    print("Construction only: no assignment enumeration for n=32,96,256.")
    print("No exactness claim on unaudited instances; rows are dense.")


if __name__ == "__main__":
    main()
