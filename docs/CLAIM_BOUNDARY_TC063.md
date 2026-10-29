# TC-063 Claim Boundary

Allowed wording:

- `TC-063` is hardened to `RESTRICTED_THEOREM_WITH_PROOF_OBLIGATIONS`.
- TC-063 is restricted to `SAF(c,r)`.
- Polynomiality is only for fixed separator bound `c`.
- G5 affine checker soundness is an explicit dependency.
- Native separator-affine certificates are Witnora-native, not external proofs.
- Scaling tests support implementation only.

Forbidden wording:

- `THEOREM_PROVEN_UNQUALIFIED`.
- P vs NP progress.
- Polynomial-time SAT for arbitrary formulas.
- All SAT or hierarchy completeness.
- DRAT/LRAT/FRAT proof unless externally exported and checked.
- HARD or UNKNOWN accepted statuses.

Reason:

TC-063 still has proof obligations and checker-soundness dependencies. v2.23
hardens the theorem shape and review surface without overstating the result.

v2.24 preserves this boundary in the external review package. It does not claim
P vs NP progress, all-SAT coverage, hierarchy completeness, an unqualified
theorem-proven status, or DRAT/LRAT/FRAT proof status. It asks reviewers to
attack the restricted `SAF(c,r)` theorem, its G5 dependency, and its native
certificate assumptions directly.

v2.25 keeps the same TC-063 boundary in the public preprint: TC-063 is a
restricted theorem with proof obligations over `SAF(c,r)`, not a fully proven
unqualified theorem, not all-SAT coverage, and not P-vs-NP progress.

v2.26 keeps the boundary unchanged while finalizing the public submission
packet. Bibliography hardening and release checklists do not upgrade TC-063:
the status remains `RESTRICTED_THEOREM_WITH_PROOF_OBLIGATIONS`, polynomiality
remains only for fixed `c`, and native certificates remain native-only unless
externally exported and checked.

## Optional runtime G5 Lean gate (research branch)

For a G5 affine residue UNSAT certificate and its original DIMACS CNF:

```bash
python -m witnora_core.operator_genesis check-affine-residue-cert \
  --cnf original.cnf --certificate certificate.json --lean
```

This mode requires a working `lake`/Lean toolchain and the built `formal/`
project. It reports distinct `native_check` and `lean_check` objects and
returns a nonzero process status unless the Lean checker accepts a concrete
`SparseBridge.checkG5Closed = true` proof obligation. A missing toolchain,
timeout, tampered certificate or rejected obligation is **not Lean verified**.
The optional `--lean-timeout` and `--max-arity` parameters control the check.

Without `--lean`, the existing command performs the historical native
certificate check only. The certificate JSON's `lean_formal_status` remains
`NOT_LEAN_VERIFIED`; the runtime result is a separate, invocation-bound
attestation and is not a permanently authenticated certificate signature.

This closes a concrete per-certificate runtime verification path for supported
G5 UNSAT claims. It does **not** prove the universal correctness of arbitrary
Python execution, provide a formal Python-to-Lean compiler refinement, establish
TC-063 composition, or prove any P-versus-NP claim.

## G5/G14 formal composition milestone

`Witnora.G5G14Composition.original_unsat_of_checked_g5_branch_cover`
combines the G14 abstract separator coverage principle with the closed G5
certificate checker. The conclusion is original-CNF UNSAT **conditional on**
these still-unproved implementation contracts:

1. Original-CNF model lifting into the separator/component decomposition.
2. Selected component-model interpretation into the residual CNF.
3. Existence of an accepted G5 certificate for a selected component on
   **every** separator branch.

The theorem requires no exponential original-CNF UNSAT enumeration and
does not trust a Python UNSAT verdict. The three premises are substantial:
this composition theorem alone is not an end-to-end proof of Python G14
branch production, TC-063, or its stated runtime bounds.

## Lean CNF-conditioning theorem

`Witnora.Conditioning.conditionCNF_correct` proves, for any CNF,
partial separator assignment and total assignment extending it, that the
executable Lean conditioning function preserves CNF satisfaction exactly.
Satisfied clauses are removed; false assigned literals are removed; empty
residual clauses are retained. The proof is universal in the CNF size and
uses no exhaustive UNSAT enumeration.

This discharges the **Lean-specification conditioning semantics** part of
the G14 decomposition bridge. It does not by itself prove that Python's
`_reduce_clause` and `_condition_by_separator` are extensionally equal to
the Lean functions, that the Python component partition is complete for
every input, or that every G14 branch carries a valid Lean-checked G5
certificate. TC-063 remains conditional on those implementation refinements.

## Lean residual-component partition theorem

`Witnora.ComponentPartition.checkPartition_sound` proves that a checked
permutation (multiset equality) of the conditioned CNF's clauses into
residual components preserves satisfaction. The executable check rejects
missing, extra, and duplicated clauses, while allowing component order to
differ. `conditioned_partition_correct` composes this with the Lean CNF
conditioning theorem for any assignment extending the separator.

This proves a universal specification-level partition bridge. The exact
refinement from Python's component discovery, clause simplification,
serialized signed-literal encoding, and assignment iteration into this Lean
checker is **not yet proved**. Nor does this theorem ensure that Python
generates accepted G5 certificates on every required separator branch.
