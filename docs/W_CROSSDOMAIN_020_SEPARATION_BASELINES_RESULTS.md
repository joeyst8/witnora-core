# W-CROSSDOMAIN-020: independent geometry, XOR and resolution controls

Frozen protocol: `docs/W_CROSSDOMAIN_020_SEPARATION_BASELINES_PROTOCOL.md`.

## Question and sound proof formats

Does the exact clause-violation covariance nullspace detect any UNSAT
instances that the strict four-pattern XOR extractor misses? And does
that apparent advantage survive a conventional one-step resolution plus
2-SAT implication baseline?

The Rust experiment tests **all three proof formats independently** on
every formula, with no priority gate obscuring overlaps:

- **Covariance:** an exact integer `K*w=0`, `sum(w)!=0` identity that makes
  weighted clause violation strictly nonzero for every assignment.
- **XOR:** four-source-clause extraction of parity equations and a GF(2)
  cycle summing to the contradiction `0=1`.
- **Binary resolution:** source-indexed `[a,b,z]`, `[a,b,-z]` pairs derive
  `[a,b]`; a contradiction in the resulting 2-SAT implication graph
  proves the original CNF is UNSAT.

Each route is sufficient for UNSAT but none is complete. The resolution
baseline is deliberately limited to **one** derivation step and does not
represent modern CDCL or unrestricted resolution. No speedup is claimed.

## Prospectively frozen, transformed 160-case cohort

All five families have 32 seeded cases of 12 variables, with clause
order shuffled, variable names permuted and signs gauge-flipped.
The independent Python source and exhaustive truth-table preflight
give these counts:

| Family | Satisfiable | UNSAT | Independent XOR screen | Independent one-step resolution + 2-SAT screen |
| --- | ---: | ---: | ---: | ---: |
| Fresh planted, 48 clauses | 32 | 0 | 0 | 0 |
| Fresh uniform, 48 clauses | 27 | 5 | 0 | 0 |
| Disguised 2-SAT core, 56 clauses | 0 | 32 | 0 | 32 |
| Full eight-pattern core, 56 clauses | 0 | 32 | 32 | 32 |
| Four-equation XOR parity cycle, 64 clauses | 0 | 32 | 32 | 0 |

These screens do not replace exact Rust certificate verification; they
are independent preflight controls, and their failures must not be
interpreted as SAT.

## Exact Rust results

| Family | Covariance proofs | XOR proofs | Resolution proofs | Covariance uniquely beyond both baselines |
| --- | ---: | ---: | ---: | ---: |
| Fresh planted | 0 | 0 | 0 | 0 |
| Fresh uniform | 0 | 0 | 0 | 0 |
| Disguised 2-SAT | 32 | 0 | 32 | 0 |
| Full eight-pattern | 32 | 32 | 32 | 0 |
| XOR parity cycle | 0 | 32 | 0 | 0 |

The covariance engine certifies **32 cases the four-pattern XOR parser
misses**, but those same 32 cases are certified by ordinary one-step
resolution. **Covariance offers zero coverage that is unique beyond
the two baselines combined.** The parity extraction certifies 32
cases that neither the covariance kernel nor one-step binary resolution
detects. Five naturally UNSAT random-boundary cases remain without any
of the three restricted certificates. No false positives occurred.

## Verification ledger

- [x] Preregister five fresh families, transformations and all three
  proof routes before collecting the Rust release outputs.
- [x] Independent Python enumeration and separate XOR/resolution screens
  ran on all 160 formulas.
- [x] Rust release code verifies covariance weights, XOR source clauses,
  resolution source pairs and truth status on every case.
- [x] Independent Python controls for indices `0,1,31` reproduce sources,
  truth, covariance weights, XOR proofs and binary resolvents.
- [x] Focused and full native Rust CI both pass.

Implementation source commit: `fdbd4520b64a5faacc1749cd4c59fa21fc0dbddb`.
GitHub Actions runs: focused `42109994612`, native `42109994604`.
Both GitHub workflows completed **successfully** on 2026-11-05.
The focused job includes two independent Python differential tests
and the full 160-instance release Rust audit. The complete native
Rust regression workflow also passed.

## Claim boundary and expected interpretation

The eight-clause disguised 2-SAT gadget has one violated clause on
every assignment, hence an exact covariance null vector. The restricted
four-pattern XOR extractor cannot see its contradiction because each
variable triple contributes only two sign patterns. However, ordinary
resolution eliminates each padding variable and detects UNSAT with
elementary 2-SAT logic. Thus a covariance-only result versus the
restricted XOR parser is **not** evidence of a novel edge over SAT
algorithms. A convincing further experiment must use genuinely harder
held-out formulas and control full solver runtime, proof size and
stronger resolution techniques.

Related established work: XOR Gaussian elimination in SAT and
polynomial-calculus / resolution proof complexity.
