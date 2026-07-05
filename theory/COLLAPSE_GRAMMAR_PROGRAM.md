# Collapse Grammar Program

## Verifier-to-Witness Motivation

Witnora studies whether structured verifier instances can be transformed by
deterministic, replayable routes into witnesses or externally checked proofs.

## Collapse Grammars

A collapse grammar is a finite set of deterministic transformations and
terminal tractable classes. A run either finds a replayable path or records that
no path was found under the configured resource bounds.

## Collapse Classes W(G)

For a grammar `G`, `W(G)` is the observed set of formulas that collapse under
`G` within a stated configuration. The configuration is part of the claim.

## Strictness Witnesses

A strictness witness records a family, a base grammar, an extended grammar, an
added operator, and certificate-backed evidence that the observed public
category changed.

## Operator Hierarchy

The v2.0 hierarchy starts with `G0_BASE`, adds exact affine reasoning in
`G1_XOR`, and keeps Horn, cardinality, and backdoor routes as honest stubs for
future work.

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

