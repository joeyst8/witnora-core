# R-126: native XOR assignment verifier

`verify_xor_assignment(system, assignment, backend="rust")` tests every
XOR row under the supplied assignment in one Rust call. Missing variables,
contradictions and false parity checks fail the verifier. No equations is
vacuously true, matching Python.

Focused native CI covers 350 seeded systems with partial assignments,
inconsistent rows and large variable IDs. The Python verifier remains the
default and independent certificate verification still requires the
established trusted proof checker, not merely this parity check.
