# R-084: bounded mixed-polarity Walsh correction in Rust

The Rust counterpart now selects exceptional clauses against majority source
polarity, enumerates a bounded exception truth table, performs its exact
fast Walsh-Hadamard transform, and constructs the required base coefficient
mode set. Its arbitrary-precision rational convolution consumes exact Walsh
coefficients from the previously verified Rust defect oracle (R-082).

Python remains the reference/default and orchestrates the native preparation,
base query and convolution. The focused differential suite covers 100 seeded
mixed-sign 3-CNF instances, free boundary variables, nonexceptional controls,
and resource caps. This is fixed-parameter experiment logic, not a general
SAT complexity improvement or Lean theorem.

Status: focused native CI pending.
