# R-113: native ANF algebra throughout clause and parity row generation

The public Python source-to-ANF functions now accept `backend="rust"` and
route every GF(2) XOR and Boolean-ring multiplication to the native R-107
primitives. This includes false literals, clause violations, source violation
polynomials, parity row equations, basis-reduced equations and the ANF geometry
report. CNF normalization and sketch validation remain Python.

Focused CI compares the exact immutable polynomials and geometry reports
for 72 seeded CNF inputs plus basis reductions. This migration does not
change the original CNF, certify a parity sketch as equivalent to the
source formula, or claim any new theorem.
