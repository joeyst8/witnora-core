# W-CROSSDOMAIN-019: combined covariance and GF(2) refutation

Status: preregistered before the Rust experiment results.

## Rationale and claim boundary

W-018's constant-coefficient degree-three covariance-kernel refutation
certified all 32 instances containing a complete eight-clause core,
but missed all 32 instances containing a four-equation XOR contradiction.
The complementary approach uses exact parity-equation discovery and
Gaussian elimination over `GF(2)`. This is related to established SAT
solvers with XOR reasoning; it is *not* a new theorem or P-vs-NP proof.

The W-019 router is strictly a **sound, incomplete UNSAT certificate
producer**, not a SAT decision algorithm:

1. Try exact `K w=0`, `sum(w)!=0`, using W-018's Rust integer kernel engine.
2. Otherwise find explicitly encoded three-variable XOR equations by
   grouping CNF clauses on identical variable triples. Four sign patterns
   banning every assignment of one parity imply the opposite parity.
3. Gaussian-eliminate recovered XOR rows; if they reduce to `0=1`,
   construct an independent source-clause-indexed proof witness.
4. Otherwise report `no_certificate`, *not* `SAT`.

Both proof paths must be rechecked with exact integer/bit arithmetic.
Performance claims and use as a production solver are out of scope.

## New and intentionally transformed held-out cohort

Four deterministic families, 32 cases each, `N=12`:

| Family | Seed | Clauses | Expected truth |
| --- | --- | ---: | --- |
| `fresh_planted_sat_48` | `0xD19C0DE1` | 48 | SAT |
| `fresh_uniform_boundary_48` | `0xD19C0DE2` | 48 | mixed |
| `hidden_eight_core_unsat_56` | `0xD19C0DE3` | 56 | UNSAT |
| `hidden_parity_cycle_unsat_64` | `0xD19C0DE4` | 64 | UNSAT |

For case index `i=0..31`, initialize xorshift32 state as
`seed ^ ((i+1)*0x9E3779B9 mod 2^32)`. Build the same core families
and 48 random trailing 3-clauses specified for W-018. Planted family
rejects all-positive clauses before transformation. The contradictory
parity equations are the W-018 four-equation cycle on variables 1–6.

After generating all clauses:

1. Fisher–Yates shuffle an identity permutation of variable identifiers
   `1..12`, iterating indices `11..1` in descending order. At index `i`,
   choose `j=next_xorshift32()%(i+1)` and swap.
2. Draw 12 more xorshift32 words, one per **original** variable; flip
   every literal's sign when that variable's word has low bit 1.
3. Rename the original variable `v` to `permutation[v-1]` and apply the
   sign flip associated with original variable `v`.
4. Shuffle the clause vector with the same Fisher–Yates procedure.

These transformations preserve satisfiability but obscure the location
and exact variable identities of planted contradictions. All transforms
are part of the **frozen generator**, not chosen after seeing outcomes.

## Mandatory controls

- Every formula: exact Rust truth-table SAT oracle over all 4096 assignments.
- Every emitted covariance witness: full integer `K w=0`, nonzero weight
  sum, and constant weighted energy over all assignments.
- Every XOR witness: list of selected recovered equations, each citing
  the four input clause indices encoding it; verify all source clauses,
  verify each XOR equation is entailed, and verify XORing equations yields
  empty variable mask and right-hand side `1`.
- Zero false positives on SAT cases. If neither certificate appears,
  return `no_certificate` even for a known UNSAT instance.
- Controls `i=0,1,31` in all four families: independent Python rebuild
  of the frozen transformed source, exact models, and each proof witness.
- Report per-family counts of covariance, XOR and no-certificate paths,
  the observed false-positive count, and factual verification status.
- GitHub focused Rust CI and full native Rust CI must both pass.

Related work: algebraic parity propagation / Gaussian elimination in SAT,
and polynomial calculus / Nullstellensatz refutations (see W-018 report).
