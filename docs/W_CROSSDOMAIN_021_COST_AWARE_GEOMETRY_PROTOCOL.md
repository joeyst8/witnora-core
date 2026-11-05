# W-CROSSDOMAIN-021: cost-aware modular covariance screening against DPLL

Status: prospective, frozen before full Rust release measurements.

## Goal and scientific boundary

W-020 found **no unique UNSAT coverage** for covariance beyond strict
XOR plus one-step resolution on its synthetic 12-variable cohorts.
This experiment instead asks a performance question: can a cheap
finite-field screen avoid costly exact-integer covariance elimination
on harder held-out 16-variable 3-CNFs, while preserving every exact
certificate discovered by a naive covariance-first route?

This is a **bounded pilot** with a small custom DPLL baseline,
not SAT Competition-quality evidence. No algorithmic complexity
breakthrough, universal speedup or proof of P=NP is claimed.

## Five new deterministic n=16 families; 12 cases each

| Name | Xorshift32 seed | Clauses | Source construction |
| --- | --- | ---: | --- |
| `planted_sat_16_68` | `0xD21C0DE1` | 68 | reject all-positive random clauses |
| `uniform_boundary_16_68` | `0xD21C0DE2` | 68 | uniform random 3-clauses |
| `eight_core_unsat_16_68` | `0xD21C0DE3` | 68 | eight complete patterns on `(1,2,3)` + 60 random |
| `padded_2sat_unsat_16_68` | `0xD21C0DE4` | 68 | W020's eight padded two-SAT clauses + 60 random |
| `xor_cycle_unsat_16_68` | `0xD21C0DE5` | 68 | W018's 16 contradictory XOR-cycle clauses + 52 random |

Use case seed `base ^ ((index+1)*0x9E3779B9 mod 2^32)` and W020's
random-clause sampling. After construction apply **the same algorithm**
for a variable permutation of `1..16`, 16 per-original-variable gauge
flips, and a Fisher–Yates clause shuffle (using the ongoing RNG state).

The density 68/16=4.25 sits near the often-studied random 3-SAT
crossover; finite 16-variable samples are **not** asymptotic evidence.

## Three complete end-to-end Rust pipelines

Each pipeline produces a SAT/UNSAT decision using the same complete
degree-ordered unit-propagating DPLL fallback. The DPLL baseline is
itself the first pipeline:

1. `dpll_only`: degree-static DPLL with exact clause evaluation.
2. `exact_covariance_first`: construct covariance K, run the W018
   exact integer kernel search, replay any witness; otherwise try the
   W019 source-backed XOR proof, otherwise run DPLL.
3. `modular_screened`: construct K, use field `p=65521` to compare the
   rank of K to the rank after appending an all-ones row. Run **exact**
   integer kernel search only if augmented modular rank is greater;
   otherwise try source-backed XOR and DPLL. Modular rank is only a
   *screen*; it is **never** accepted as an UNSAT certificate.

These methods must agree on every result. The baseline DPLL and any
certificate must be independently verified on controls. A modular
screen may miss an exact rational witness for unlucky primes (only
completeness suffers); count such misses by directly comparing against
`exact_covariance_first`. Report this explicitly.

## Timing and held-out controls

- Freeze 12 cases per family and run each pipeline **three** times per
  case, with the same Rust release binary on the same CI host. Record
  elapsed nanoseconds for full pipelines, including screening,
  covariance construction, exact elimination, XOR extraction, and
  fallback as applicable. Report family mean across case medians;
  timing differences are descriptive, not statistically significant.
- Count direct covariance witnesses, XOR witnesses, DPLL fallbacks,
  modular-screen candidates and skipped-exact-witness discrepancies.
- DPLL search must be sound and complete for the 16-variable formulas;
  no budget-based "UNSAT" result is permitted.
- Independent Python generator and exhaustive 2^16-assignment truth
  tables for control indices `0,1,11` of all five families, plus a
  separate Python degree-DPLL count for controls if feasible.
- No certificate may label a satisfiable formula UNSAT. Tests verify
  every emitted witness with exact integer logic and all 16-variable
  source semantics.
- GitHub focused and full-native Rust CI must pass. Negative runtime
  results and every remaining limitation must be archived.

Relevant prior work: SAT random 3-CNF crossover near density 4.26,
Gaussian-elimination XOR reasoning, modular linear algebra, and
polynomial-calculus / resolution proof complexity. This pilot studies
practical cost, not a new proof-system theorem.
