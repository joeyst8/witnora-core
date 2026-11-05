# R-133–R-134: native sparse XOR min-fill schedule and elimination order

`_sparse_xor_elimination_schedule(..., backend="rust")` now computes the
deterministic GF(2) pivot candidates, row combinations, duplicate-row
reuse, contradiction handling, min-fill tie breaks and ordered operation
trace in Rust. Python formats the same reporting dictionary. R-134 threads
the native schedule through `_sparse_xor_elimination_order` with the same
ordering and diagnostics.

Focused native CI compares full schedules and traces for 120 seeded
systems plus an initial contradiction, and 100 additional seeded order
reports. This is an algebraic row-operation witness only. It does not
supplant RUP/drat-trim or Lean proof checking, and it is not an
independent DRAT refutation.
