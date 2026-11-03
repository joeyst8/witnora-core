# Larger-fish milestone: universal resolution proofs, beyond TC-063

Audit date: 2026-11-03 UTC. Draft PR #121, branch `formal/g14-python-seen-enqueue-v121`.

## Why this is a genuine domain expansion

The completed `TC063CanonicalBound.tc063_restricted_family_unsat_iff_checked_cover`
remains a proof for the explicitly promised `Family c r` class. It does **not**
decide unrestricted SAT, handle arbitrary difficult non-affine residuals through
G5 alone, or establish a polynomial-time solver.

We now have an **orthogonal, unrestricted proof-checking interface**:

- `formal/Witnora/GeneralResolution.lean` accepts an exact, by-value
  binary-resolution derivation over any finite `CNF`, with no separator,
  affine or bounded-width hypothesis.
- `GeneralResolution.signedResolution_unsat` proves universally that if the
  executable checker accepts the derivation of the empty clause, the **signed
  source CNF is UNSAT under every assignment**.
- `formal/Witnora/GeneralResolutionIndexed.lean` accepts zero-based row-ID
  references, reconstructs the parents and exact resolvents in Lean, rejects
  invalid IDs/pivots, and routes the reconstructed proof through the universal
  reference checker.
- `GeneralResolutionIndexed.signedIndexed_unsat` proves this indexed
  interface is sound for every signed source CNF.

Both theorem axiom audits report exactly **[propext, Quot.sound]**. No `sorry`,
admitted SAT-oracle result, project axiom or exhaustive original-assignment
enumeration is used by either theorem.

The **source parser/document-byte correspondence remains a separate trust
boundary**: these generic theorems start from signed clause lists. We can
compose them with the existing verified DIMACS document interface, but that
composition is not part of this milestone.

## Real non-affine adversarial fixture

`scripts/generate_general_resolution_lean.py` generates a full ordinary
resolution refutation of the pigeonhole CNF with three pigeons and two holes,
an UNSAT example whose obstruction is not an exact affine residual. It prints
**two independent Lean acceptance examples** for the same Python-generated
trace: by-value and indexed. The Lean checker re-evaluates the entire trace
from source clauses, without trusting a Python UNSAT verdict.

`tests/test_general_resolution_trace.py` checks:

1. This pigeonhole source is UNSAT by a separate *small-only* exhaustive oracle
   and its generated resolution refutation is accepted by native trace replay.
2. Forged final resolvent and forged pivot are rejected.
3. Removing a source clause used by the proof invalidates the trace.
4. A satisfiable two-pigeon/two-hole source produces no refutation.
5. Noninteger/zero source literals are rejected.

The targeted workflow passed all five tests, universal Lean theorem build and
**both generated Lean examples**:

- https://github.com/joeyst8/witnora-core/actions/runs/41597633004

The initial by-value version also passed its earlier independent workflow run:
https://github.com/joeyst8/witnora-core/actions/runs/41597376744 .

## Exact limits and where the larger research starts

This result proves **verification soundness**, **not proof-search efficiency**.

- The saturation-based Python proof producer is a deliberately tiny reference
  enumerator. It can produce exponentially many clauses and is inappropriate
  as a general industrial SAT engine.
- The indexed certificate reduces serialized row duplication, but the current
  Lean prototype expands to a full by-value trace and replays it. This is **not
  yet a streaming linear/near-linear checker**.
- The checker accepts **pure binary-resolution additions**, not arbitrary
  RUP/LRAT/DRAT/FRAT. A direct CDCL proof import requires a carefully checked
  proof-format bridge and its own universal soundness theorem.
- No arbitrary CNF has been classified as SAT/UNSAT solely from a proof
  generator without either a checked SAT model or a checked UNSAT certificate.
- Universal polynomial-time discovery, short-proof existence and industrial
  performance are not claimed. No P-versus-NP result follows.

## Next falsifiable experiments: bigger fish

1. **Proof-stream bridge**: implement a streaming indexed checker and a source-
   bound RUP/LRAT proof importer. Verify every addition, deletion, reference
   and final empty clause in Lean, preserving exact original DIMACS identity.
2. **Non-affine hard families**: frozen held-out pigeonhole, graph-coloring,
   random 3-SAT near threshold and Tseitin graph CNFs with no useful 2-cut.
   Increase sizes until the proof importer is stressed; record `TIMEOUT` and
   `OOM` honestly.
3. **Real comparative performance**: compare unmodified Glucose/Kissat/CaDiCaL
   against Witnora preprocessing plus the same backend on identical inputs,
   measuring preprocessor, solver, proof emission and Lean checking separately.
   The required claim is a reproducible **end-to-end** improvement, not merely
   fewer clauses, a beautiful separator, or an isolated subroutine speedup.
4. **New structural operators**: propose transformations for hard non-affine
   residuals, each with an exact satisfying-assignment lift and verified UNSAT
   proof lift. Keep negative controls and preregister held-out tests.
5. **Complexity honesty**: treat the unrestricted polynomial-time goal as an
   open research question. A single successful finite benchmark never implies
   a worst-case theorem.

This separates **Track A: universal logical trust** from **Track B/C:
structural discovery and operator invention** and **Track D: empirical
competitive validation**, without confusing their proof obligations.
