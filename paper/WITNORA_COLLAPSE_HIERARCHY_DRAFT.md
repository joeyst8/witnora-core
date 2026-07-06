# Witnora Collapse Hierarchy: A Certificate-Backed Program for Verifier-to-Witness Operator Discovery

## Abstract

Witnora studies bounded collapse grammars that turn selected verifier instances into checked witnesses or native proof certificates.

## Introduction

The current program organizes operators G0 through G6 as a certificate-backed ladder.

## Non-claims

This work does not prove P vs NP.
Strictness results are empirical unless marked with a formal proof.
Native certificates are not DRAT unless explicitly exported and checked.
The hierarchy is a research program, not a complete SAT algorithm.

## Bounded collapse classes

For a bound profile B and grammar G, W_B(G) is the operational set of formulas for which Witnora emits a verified SAT witness, externally checked proof, or accepted native certificate within the configured bounds.

## Grammar hierarchy G0-G6

The hierarchy is G0_BASE, G1_XOR, G2_SYMMETRY_CERTIFIED, G3_SYMMETRY_CARDINALITY_CERTIFIED, G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE, G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE, and G6_PROOF_MOTIF_COMPRESSION_PROTOTYPE.

## Native certificate types

Native certificates include symmetry, pigeonhole counting, orbit-capacity counting, affine residue, and proof-motif macro certificates.

## Empirical strictness evidence

Each hierarchy edge has witness families and bounded operator-delta records, but none is promoted to theorem status in v2.8.

## Proof obligations

The proof-obligation matrix records non-collapse obligations, checker soundness obligations, scaling obligations, and optional DRAT bridge work.

## Operator genesis

Operator genesis remains a candidate-generation and promotion discipline, not a claim of autonomous theorem discovery.

## Gap analysis

Current gaps include random 3-SAT, general circuit-SAT, arbitrary PB encodings, non-exact affine structure, realistic SAT competition formulas, and native certificates without DRAT bridges.

## Relationship to P vs NP

The motivation is verifier-to-witness structure. The artifact is a bounded experimental and theoremization framework, not a proof of P vs NP.

## Why this does not prove P vs NP

The hierarchy is bounded, operational, and evidence-backed. It does not establish lower bounds, completeness, or a polynomial-time SAT algorithm.

## Future work

Future work should discharge proof obligations, mechanize checker soundness arguments, and select the next operator from gap-driven obstruction records.