# R-119: single-call native separator-conditioned exact ANF counting

`count_common_zeros_conditioned(..., backend="rust")` now performs
separator discovery, assignment enumeration, symbolic budget allocation,
forced pin equations, exact structured counting and result aggregation
in one Rust call. It reuses the R-110 and R-111 kernels and returns the
same nine fields as Python `SeparatorCountResult`. The default Python route
and its budget exception semantics remain unchanged.

Focused CI compares 160 seeded systems, including budget exhaustion,
and a 180-free-variable arbitrary-precision case. This process can still
take exponential time and does not prove a new complexity bound. A green
native wheel/differential gate is required for verification.
