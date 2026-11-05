# W-CROSSDOMAIN-020: covariance/XOR separation with a resolution baseline

Status: frozen before Rust measurements or outcome comparisons.

## Research question

W-019's combined proof router certified 64 deliberately UNSAT instances,
but an XOR-only baseline already certified those same instances. Can a
covariance-kernel witness certify anything *not* detected by the strict
four-pattern XOR extractor, and does this benefit survive an elementary
resolution/2-SAT baseline?

This is a test of **restricted certificate formats**, not a claim to
improve over modern CDCL SAT solvers or to decide SAT in polynomial time.

## Five prospective 32-case cohorts (`N=12`)

| Family | Seed | Source clauses | Intended truth |
| --- | --- | ---: | --- |
| `fresh_planted_sat_48` | `0xD20C0DE1` | 48 | SAT |
| `fresh_uniform_boundary_48` | `0xD20C0DE2` | 48 | mixed |
| `disguised_2sat_unsat_56` | `0xD20C0DE3` | 56 | UNSAT |
| `full_eight_unsat_56` | `0xD20C0DE4` | 56 | UNSAT |
| `parity_cycle_unsat_64` | `0xD20C0DE5` | 64 | UNSAT |

As in W-019, initialize xorshift32 with
`seed ^ ((i+1)*0x9E3779B9 mod 2^32)` for case indices `0..31`, then
append random distinct-variable 3-clauses to the specified target size.
Reject all-positive clauses for the planted family before transforms.

The three constructed contradictions are:

- **Disguised 2-SAT:** the eight clauses
  `(1,2,3)`, `(1,2,-3)`, `(1,-2,4)`, `(1,-2,-4)`,
  `(-1,2,5)`, `(-1,2,-5)`, `(-1,-2,6)`, `(-1,-2,-6)`.
  Their violated-clause count is exactly one on every assignment.
  However no triple has the four sign patterns required to extract
  a three-variable XOR equation. One resolution step eliminating each
  padding variable gives four contradictory 2-CNF clauses.
- **Full eight-core:** all eight 3-literal sign patterns over variables
  `(1,2,3)`; gives an exact zero-variance certificate and both opposing
  parity equations on that triple.
- **Four-XOR parity cycle:** the four inconsistent parity constraints
  specified by W-018 on `(1,2,3)`, `(1,4,5)`, `(2,4,6)`, `(3,5,6)`;
  each is expanded into four forbidden-assignment clauses.

Apply to every family the **same transformation algorithm as W-019**:
Fisher–Yates variable permutation with descending indices 11..1,
then 12 xorshift sign-flip bits for original variables, then transform
every literal and Fisher–Yates shuffle the entire clause vector.
Do not adjust generators after observing outcomes.

## Three independent sound tests, all run on every case

1. **Covariance:** exact integer `K w=0` and `sum(w)!=0`, then verify
   the constant weighted energy identity over all 4096 assignments.
2. **XOR:** the four-pattern per-triple extractor and GF(2) contradiction
   witness from W-019; recheck every cited source-clause index.
3. **Resolution / 2-SAT baseline:** derive every binary resolvent
   `[a,b]` from a pair `[a,b,z]`, `[a,b,-z]`. Only original 3-clauses
   may be premises. Check whether the entire set of derived binary
   clauses is UNSAT using implication-graph reachability. Every derived
   clause has a source pair of original clause IDs; independently
   verify these pairs. This restricted one-step baseline is *not* full
   resolution or a modern SAT solver.

Every case also receives exact SAT status from exhaustive 4096-assignment
truth tables. Report all overlaps (covariance-only, XOR-only, both,
and whether resolution covers each), rather than prioritizing one proof
path and hiding the others. Count coverage **only among actual UNSAT**
cases. No false positives are allowed, and missing certificates mean
`UNKNOWN`, never SAT.

At control indices `0,1,31` independently reproduce all source clauses,
truth counts, emitted covariance weights, XOR source clauses, derived
binary resolution premises and 2-SAT implication contradiction in
Python. Use Rust for the experiment and Python only for oracle checks.
Pass focused and full-native GitHub CI before calling the experiment
verified. Report negative results; no solver speedup is claimed.

Prior art: resolution and 2-SAT implication graphs, XOR Gaussian
elimination (e.g. CryptoMiniSat), and low-degree Nullstellensatz /
polynomial-calculus certificates. The construction is a comparison
among known techniques, not a novel proof of P vs NP.
