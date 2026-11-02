# Draft research gate: source-bound affine pair screening is redundant

## Question

Can the selective same-support affine/CNF pair check be integrated as a
sound, source-bound pruning stage in Witnora's masked DPLL and improve total
solver runtime over the current baseline?

## Structural obstruction

`detect_cnf_xor_patterns` only emits an equation when the original CNF has
the **complete exact encoding** of that equation on a fixed variable support.
`selective_screen_pairs` inspects pairs of clauses only when their exact
variable support equals that of a detected 2- or 3-variable equation.
Consequently, for every selected pair, **both clauses are already entailed
by the very detected equation**. If all detected equations are jointly
consistent, there is no contradiction to discover from such a pair. If the
detected equations are inconsistent, `gf2_dimension` already detects it,
without pair enumeration. This argument relies on the current detector's
exact-support/full-encoding requirements; it is not a universal claim about
all affine/CNF screening algorithms.

This also means the previously promising selective result with separately
provided affine rows **cannot simply be transferred to raw CNF**. The
independent rows in that benchmark were input assumptions, not recovered
from source CNF encodings.

## Reproducible synthetic check

Run from repo root with PySAT installed:

```
python -m scripts.experiment_source_bound_pair_redundancy
python -m unittest tests.test_source_bound_pair_redundancy -q
```

48 fixed synthetic formulas across 16/32 variables, eight seeds, and three
families: two exact overlapping XOR encodings alone, a CNF contradiction
from opposite unit clauses, and random 3-SAT clauses mixed with encodings.
Independent MiniSat22 SAT oracle agrees with masked DPLL in all 48 cases.

| Metric | Observed |
|---|---:|
| Formulas | 48 |
| Detected source-bound 2/3-var rows per case | 2 |
| Eligible pairs checked | 576 |
| New source-bound UNSAT witnesses | **0** |
| Baseline masked DPLL sum of per-case median times | 3.4464 ms |
| DPLL plus one up-front detection/screen sum | 20.8931 ms |
| Cases with improved end-to-end time | **0/48** |

Times are microbenchmark-level Python wall-clock measurements, not stable
performance ratios. The precheck ran only once per formula, which is a
**favorable lower overhead** compared with invoking it at many search nodes.
No source-bound pair-screen pruning benefits were observed. This is not an
external SATLIB experiment or a claim of algorithmic novelty.

## Decision

**Reject** the direct selective pair-screen integration. Preserve the test
as a negative control. A future alternative must produce logically
independent, source-justified constraints or cross-support deductions;
prove its pruning condition and charge extraction + search overhead.
An UNSAT report from externally assumed parity rows is conditional until
those rows are certified to follow from the original CNF.
