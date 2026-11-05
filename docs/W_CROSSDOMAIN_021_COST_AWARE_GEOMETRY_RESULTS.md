# W-CROSSDOMAIN-021: n16 modular-screen / exact-first / DPLL pilot

Protocol: `docs/W_CROSSDOMAIN_021_COST_AWARE_GEOMETRY_PROTOCOL.md`.

## Mathematical method

The exact proof path uses the signed covariance matrix `K` of violated
3-clauses. An integer `w` satisfying `K*w=0` and `sum(w)!=0` proves the
weighted violation energy is a fixed nonzero number on every assignment,
which rules out a satisfying assignment.

The proposed cheap screening gate works over the fixed prime field
`GF(65521)`: it compares `rank(K)` with the rank after adding an
all-ones row. Only a rank increase triggers the expensive exact
integer kernel computation. **A modular rank increase is not an UNSAT
proof**. Any selected witness is independently verified over the
integers. The gate can miss potential rational witnesses for unlucky
primes; those are counted by comparing with the always-exact path.

All three pipelines end in the *same* degree-static DPLL search when
no algebraic proof is found. The timing includes the complete paths:
covariance construction, modular screen, exact arithmetic and XOR
extraction where applicable. It excludes source generation and JSON
printing. Each method is run three times per formula and case medians
are averaged within each family. This is descriptive timing on small
instances, **not a solver speedup claim**.

## Frozen cohort and independent truth preflight

Five new families of 12 formulas, each containing 68 width-three clauses
on 16 variables, with frozen seeds, variable permutations, gauge flips,
and shuffled source clause order:

| Family | SAT | UNSAT |
| --- | ---: | ---: |
| Planted SAT | 12 | 0 |
| Uniform near-boundary | 10 | 2 |
| Embedded full eight-pattern contradiction | 0 | 12 |
| Padded two-SAT contradiction | 0 | 12 |
| Four-XOR parity cycle contradiction | 0 | 12 |

These counts were independently reproduced by a Python 2^16-assignment
truth-table oracle before inspecting the Rust benchmark outputs.

## Release-Rust experimental results

| Family | DPLL mean case-median (ms) | Always-exact first (ms) | Modular-screened (ms) | Modular candidates | Missed exact covariance proofs |
| --- | ---: | ---: | ---: | ---: | ---: |
| Planted SAT | 0.009695 | 47.825502 | 0.676994 | 0 | 0 |
| Uniform near-boundary | 0.009753 | 48.738813 | 0.685832 | 0 | 0 |
| Full eight-pattern | 0.005159 | 37.676270 | 38.379102 | 12 | 0 |
| Padded two-SAT | 0.007638 | 37.971980 | 38.621643 | 12 | 0 |
| XOR parity cycle | 0.010184 | 45.337052 | 0.667534 | 0 | 0 |

The exact covariance certificate succeeded on all 24 embedded
contradictions; XOR extraction succeeded on all 12 parity cycles.
None of the 24 exact covariance proofs was missed by the modular
screen. No covariance or XOR proofs were produced for the other 24
formulas, which all used the DPLL fallback (including two UNSAT random
cases). Every pipeline agreed on the satisfiability decision.

**Negative runtime result.** DPLL was fastest across all five cohorts:
roughly 0.005--0.010 ms versus 0.667--38.622 ms for the screened
pipeline. The modular gate cuts overhead relative to always-exact
arithmetic on the planted, random, and XOR families (where it avoids
the rational kernel computation), but cannot compete with DPLL on
these small, easy instances. On the two constructed covariance-UNSAT
families, modular screening *adds* overhead to the exact proof path.
This is a measured failure of the proposed universal acceleration,
not a failure of certificate soundness.

## Verification ledger

- [x] Prospective frozen source families, modular prime, three full
  pipelines, timing repetitions and independent controls.
- [x] Independent Python truth tables classify all 60 source formulas.
- [x] Rust release executable completes exact-vs-screened-vs-DPLL audit.
- [x] Control indices `0,1,11` independently reproduce Rust source,
  complete SAT truth, DPLL scans, modular rank and witness equations.
- [x] No false UNSAT witness and no inconsistent pipeline decision.
- [x] Focused and full native GitHub CI pass.

Source commit `b8b7f7f14995948cdb3acc3ae5e43d825e7951b3`.
GitHub Actions runs: focused `42116368711`, native `42116368997`.
Both concluded `success` on 2026-11-05.

## Claim boundary

All inputs have only 16 variables; they do not establish asymptotic
hardness or a practical advantage on industrial SAT benchmarks. The
DPLL baseline is a simple deterministic implementation, **not** a
modern CDCL solver. Any observed timing gains must be interpreted in
this narrow scope; additional held-out, externally sourced problems
and stronger solver baselines remain necessary.
