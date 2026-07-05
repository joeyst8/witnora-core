# Collapse Grammar Program

## Verifier-to-Witness Motivation

Witnora studies whether structured verifier instances can be transformed by
deterministic, replayable routes into witnesses or externally checked proofs.

## Collapse Grammars

A collapse grammar is a finite set of deterministic transformations and
terminal tractable classes. A run either finds a replayable path or records that
no path was found under the configured resource bounds.

## Bounded Collapse Classes W_B(G)

For a grammar `G` and bound profile `B`, `W_B(G)` is the observed set of
formulas that collapse under `G` within `B` and emit a valid certificate/proof
when required. The bound profile includes caps such as width, XOR arity,
runtime, proof size, search nodes, operator depth, and symmetry diagnostic
limits.

The unbounded notation `W(G)` is aspirational/theoretical in the Witnora
program. Current releases report `W_B(G)` evidence only.

## Strictness Witnesses

A strictness witness records a family, a base grammar, an extended grammar, an
added operator, and certificate-backed evidence that the observed public
category changed.

## Operator Hierarchy

The v2.0 hierarchy starts with `G0_BASE`, adds exact affine reasoning in
`G1_XOR`, and keeps Horn, cardinality, and backdoor routes as honest stubs for
future work.

v2.1 adds a diagnostic `G2_SYMMETRY_PROTOTYPE` layer. It records syntactic
candidate orbits over variables, literals, and clauses. This is not full graph
automorphism detection and does not by itself define a satisfiability-preserving
quotient.

v2.2 adds `G2_SYMMETRY_CERTIFIED` for small formulas with exact automorphism
evidence. A native symmetry certificate can validate generators, recompute
orbits, record symmetry-breaking predicates, and verify reconstructed SAT
witnesses against the original CNF. It is not an external UNSAT proof unless a
DRAT proof against the original CNF is checked.

## Theorem Candidates

Theorem candidates are tracked with explicit statuses: conjecture, empirical
evidence, proof sketch, refuted, or open. A candidate is not a theorem until its
proof obligations are discharged. The initial registry includes bounded XOR
strictness, formal XOR strictness on Tseitin, a symmetry collapse conjecture,
and a collapse obstruction conjecture.

## Collapse Obstructions

Obstruction records explain bounded non-collapse under a configured grammar and
profile. They can cite treewidth over cap, XOR arity over cap, absent exact XOR
patterns, symmetry signals without a certified quotient, unsupported
cardinality/Horn structure, proof export blowup, or search caps. These records
guide operator discovery; they are not lower-bound claims.

## Relationship to P vs NP

Witnora does not claim progress on P vs NP. It provides a certificate-backed
experimental framework for studying when verifier instances admit deterministic
collapse paths to witnesses or proofs.

## Why This Does Not Prove P vs NP

The lab reports bounded, configured experiments. A no-collapse result is not a
lower bound against all algorithms, and a collapse result for a family slice is
not a general SAT-solving result.

## Research Agenda

1. Expand exact operators only when their evidence can be replayed.
2. Separate native traces from external proof certification.
3. Preserve no-collapse rows honestly.
4. Use frontier diagnostics to prioritize operators.
5. Freeze claims only after tests, artifacts, and red-team review.
6. Turn obstruction records into certified operators only when witness
   reconstruction or proof preservation is explicit.
7. Treat symmetry-breaking predicates as preservation obligations, not as
   clauses implied by the original formula unless an external proof checker
   accepts them.
