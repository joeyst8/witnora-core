# PR #119 — TC-063 G14 single-variable cover bridge (Dubois20)

Status: `KERNEL_CHECK_PENDING` until the pinned Lean CI job passes.

## Exact mathematical statement

`theory/TC063DuboisOneBitCover.lean` introduces a reusable theorem
`Witnora.TC063.two_branch_unsat_cover`. Given:

1. An original proposition over a model.
2. A Boolean separator expression and a residual proposition for each value.
3. A proved **exact semantic equivalence** between the original and the
   residual at the separator's actual value.
4. Proven contradictions for **both** Boolean assignments.

It derives that every original model is impossible. This is the one-bit
assignment-exhaustiveness / UNSAT-cover fragment of TC-063 G14.

## Concrete source fixture

- Instance: archived 60-variable, 160-clause `dubois20.cnf.Z`.
- Decompressed DIMACS SHA-256:
  `82059aba0e5773644b386eb6bcbe53680655390cb041873a3cb3e93f7bd896a7`.
- Split on original DIMACS variable 1 (`BitVec 60`, LSB bit 0).
- Substitute its value literally into the eight clauses comprising
  `sourceGroup0` and `sourceGroup1`. Preserve the other 152 clauses in the
  remaining 38 source groups unchanged.
- Prove `sourceCNF bits ↔ residualCNF (bits.getLsbD 0) bits` by kernel
  definitional equality. Prove its arbitrary-assigned-value variant.
- Refute both branches by lifting each residual back into the source CNF,
  invoking the source-exact G5 CNF→XOR equivalence and 39-step contradiction.
- Apply the general two-branch cover theorem.

The proof intentionally **does not** use the previously established
`source_unsat` theorem as a lemma; both branches invoke the verified G5
certificate directly. They nevertheless share the same global certificate,
not independent component-local certificates.

## Trust and novelty boundary

**This does not prove full TC-063.** In particular:

- We have **not** proved that this single variable separates the primal
  graph into distinct components, that residuals decompose into independent
  affine components, or that any selected separator lies in a bounded
  `SAF(c,r)` recognizer class.
- We have **not** established general indexed-variable substitution,
  arbitrary-width assignment enumeration, SAT lifting, polynomial
  complexity, or an external DIMACS-parser-to-Lean refinement proof.
- Branch contradiction uses the already known G5 global XOR contradiction.
  No new solver speed or general SAT advantage follows from this bridge.

## Checks and next work

`python -B -m unittest tests.test_tc063_dubois_one_bit_cover -v` checks that
the two modified clause groups are **exact literal replacements** and all 38
others remain in order with no bit-0 occurrence. Lean CI separately compiles
the G5 source theorem and the G14 bridge and prints the derived theorem's
axioms. Next meaningful TC-063 milestone: prove a **generic indexed-variable
substitution and residual-component ownership theorem** with the local G5
certificate-to-residual bridge, then complete the structural separator
decomposition and UNSAT-cover soundness for recognized `SAF(c,r)` inputs.
