# Symmetry Certification Lemma

## Purpose

This note records the v2.2 soundness boundary for symmetry/orbit reasoning.

## Automorphism Evidence

A claimed variable permutation is accepted only if it maps the original CNF
clause set exactly onto itself. The independent checker recomputes this
condition from the original CNF and the recorded generators.

## Symmetry-Breaking Predicates

Symmetry-breaking predicates are generally not logical consequences of the
original formula. They remove duplicate witnesses from symmetric orbits.

The preservation obligation is:

`F` is satisfiable iff `F and SBP` is satisfiable.

This is justified only when the certificate records that every satisfying
assignment orbit under the verified automorphism group has at least one
representative satisfying the SBP.

## SAT Witness Reconstruction

For SAT rows, Witnora accepts the native symmetry certificate only when the
reconstructed or lifted assignment directly satisfies the original CNF. This is
stronger than trusting the quotient or symmetry-broken formula alone.

## UNSAT Boundary

`F and SBP` being UNSAT does not by itself prove `F` is UNSAT. A native UNSAT
symmetry certificate must include automorphism evidence, the SBP preservation
argument, and a replayable proof that the strengthened formula is UNSAT. An
external DRAT claim is made only when the proof is checked against the original
CNF.

## Claim Boundary

v2.2 provides certified toy and graph-coloring symmetry evidence plus
pigeonhole orbit diagnostics. It does not claim P vs NP progress, general SAT
solving, full pigeonhole collapse, or a general symmetry-collapse theorem.
