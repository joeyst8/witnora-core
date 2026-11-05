# W-CROSSDOMAIN-022: external CNF and budgeted spectral profiling pilot

Status: **prospective**, frozen before obtaining runtime measurements.

## Hypothesis and honest scope

W-021's exact covariance preprocessing was much slower than direct DPLL on
60 tiny formulas. Test a cheaper, approximately linear-time structural
observable on **externally sourced** hard SAT cases. This is a measurement
and validation pilot, **not** a new SAT decision procedure and **not** a
claim to have accelerated a CDCL solver.

Measure a signed incidence-graph spectral signal from math/physics, and
the additional runtime required to obtain it before a modern SAT solve.
Preprocessing of an unchanged CNF cannot, by itself, make a solver faster;
any positive algorithmic claim requires a separately implemented policy
using the signal, tested prospectively against Kissat-only.

## Fixed external sources and controls

Use the **VLSAT-2** suite from INRIA (Pierre Bouvier and Hubert Garavel),
which models real concurrency systems; VLSAT-2 documents 50 SAT and 50
UNSAT instances and the difficulty labels. Original source index:
https://cadp.inria.fr/resources/vlsat/2.html

Freeze this initial, intentionally small and imbalanced set without
inspecting our measurements:

| File stem | Expected label |
| --- | --- |
| `vlsat2_544_8738` | UNSAT |
| `vlsat2_600_11440` | UNSAT |
| `vlsat2_684_9417` | UNSAT |
| `vlsat2_684_13953` | UNSAT |
| `vlsat2_708_10259` | UNSAT |
| `vlsat2_736_11022` | UNSAT |
| `vlsat2_1000_22250` | SAT |
| `vlsat2_3456_192912` | SAT |

Input URL: `https://cadp.inria.fr/ftp/benchmarks/vlsat/{stem}.cnf.bz2`.
Log compressed SHA-256 and decompressed SHA-256 for reproducibility.
Fail closed if an input is missing, truncated or invalid DIMACS; do not
replace it with a synthetic instance. The exact number of variables and
clauses is part of the frozen expected identity.

## Rust-only scientific observable

For each CNF make the signed bipartite clause-variable matrix
`B[c,v]=sum of signs of occurrences of v in clause c /
sqrt(length(c)*degree(v))`. Start with deterministic signed literal
imbalance `x[v]=(positive_degree-negative_degree)/sqrt(degree(v))`;
if its norm is zero, use a fixed nonzero fallback. Normalize x and run
exactly **8 normalized power iterations** of the symmetric positive
semidefinite operator `B^T B`.

Report the final Rayleigh quotient and inverse participation ratio
`sum(x[v]^4)`, along with variable polarity conflict fraction,
variable/edge counts, clause-width mean, and source-parse plus feature
runtime. This is a finite spectral **proxy**, neither a proof nor an
exact eigenvalue. Complexity is O(8*literal_occurrences); memory is
O(literals + variables + clauses).

The CLI must correctly parse general DIMACS, including clause wrapping,
comments, empty clauses and non-3-CNF; reject malformed/trailing clauses,
headers and out-of-range literals. It must not solve SAT or infer truth
labels from features. An independent Python oracle verifies exact counts
and all scalar feature definitions on at least three tiny control CNFs.

## Modern solver baseline and resource controls

- Run **Kissat** official release `rel-4.0.4` from
  `https://github.com/arminbiere/kissat`, record resolved Git commit.
- Per instance cap Kissat at 15 wall-clock seconds; classify exits as
  SAT (code 10), UNSAT (20), TIMEOUT, or ERROR (no fabricated verdict).
- Compare returned status with INRIA published label when it completes.
  Truth labels from the benchmark publisher are independent of timing.
  Do not claim independently checked UNSAT proof until a proof verifier
  has checked a genuine proof artifact.
- Time bare Kissat and the Rust feature extraction **separately** on
  the same CI runner. This measures possible *overhead*, not speedup.
- Record raw JSON per formula, all timeouts, source SHA-256, resolved
  solver commit, and aggregate with no imputation. Keep raw results as
  downloadable CI artifact.
- Correlation with difficulty is exploratory and confounded by size,
  label imbalance, solver censoring and nonrandom source selection.

## Predeclared pass/fail boundary

Pass the engineering milestone only if the Rust CLI and independent
controls pass; all eight external CNFs download, validate their declared
sizes and labels; the pinned Kissat build executes; no returned solver
status contradicts publisher truth; and structured results are saved.

Passing this milestone **does not** establish general solver advantage,
novel mathematics, computational hardness prediction, or P=NP. If the
external host fails, report the blocker and do not alter the sample.
