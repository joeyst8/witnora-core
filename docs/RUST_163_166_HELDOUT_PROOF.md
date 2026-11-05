# R-163–R-166: held-out contradictory XOR proof experiment

This independent regression suite challenges the **existing native row-trace
candidate generator** on 120 seed-chosen inconsistent full XOR-CNF pairs of
arity 1–3 over relabeled source variables.

- **R-163:** entire native proof candidate and statistics must match Python.
- **R-164:** the independent Python RUP-subset checker must accept the output
  from the original source CNF, not just from the XOR row equations.
- **R-165:** deleting the final empty-clause line must cause RUP verification
  to reject the truncated proof.
- **R-166:** reversing the order of the contradictory XOR witnesses must not
  change proof validity; 80 seeded support cases test both source orders.

All cases are deliberately restricted to inconsistent complete XOR gadgets.
They are not general industrial SAT evidence, solver speed benchmarks or a
Lean theorem, and do not retire additional original Python modules.

**Status: experimental CI pending.**
