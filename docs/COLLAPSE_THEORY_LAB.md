# Collapse Theory Lab

Witnora-Core v2.0 adds a research lab for comparing bounded collapse
grammars. It is not a product feature and it is not a new SAT-solver claim.

## Purpose

The lab studies this question:

Given a CNF verifier instance, when can a deterministic, replayable grammar
discover a collapse path to a witness or proof?

## Core Objects

- Collapse Grammar G: a finite set of deterministic transformations and
  terminal classes.
- Collapse Class W(G): formulas that collapse under G within configured
  resource bounds.
- Strictness Witness: bounded evidence that one grammar fails under the
  configured bound while an extended grammar succeeds with certificate-backed
  evidence.
- Operator Delta: the changed public outcomes between G and G plus an operator.

## Current Profiles

- `G0_BASE`: UP, PLE, SUB, BCE, VE, components, 2SAT, bounded treewidth.
- `G1_XOR`: `G0_BASE` plus exact CNF XOR extraction and sparse/min-fill XOR
  elimination.
- `G2_HORN_PROTOTYPE`: honest stub.
- `G3_CARDINALITY_PROTOTYPE`: honest stub.
- `G4_BACKDOOR_DIAGNOSTIC`: honest stub.

## Claim Boundary

Allowed claim:

Witnora v2.0 formalizes collapse grammar comparisons and demonstrates bounded
strictness examples where adding exact XOR reasoning changes selected formula
families from no-collapse to certified collapse.

Forbidden claims:

- no P vs NP progress claim
- no general SAT solving claim
- no broad XOR extraction claim
- no competitive SAT solver claim
- no lower bound against all algorithms
- no complete collapse grammar claim

