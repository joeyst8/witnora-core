# Reviewer Objections for G9-G13

These responses are intentionally conservative. They preserve the difference between native finite evidence, proof sketches, and proven theorems.

## This is just engineering.

The release defines theorem candidates, proof sketches, proof obligations, and certified finite evidence. It does not overclaim theorem status.

## Native certificates are not external proofs.

Correct. Native certificates are scoped as native unless DRAT/LRAT/FRAT export is implemented and externally checked.

## Plans are not proofs.

Correct. G12 is plan-only and G13 separates execution certificates.

## Finite examples do not imply families.

Correct. Infinite-family theorems remain proof obligations.

## Operator composition may be unsound.

G9/G13 require verified step certificates, formula handoffs, and result checks; full theoremization remains candidate/sketch level.

## Projection may be unsound.

G10 only supports exact definitions and verifies original-CNF SAT lift; UNSAT requires equisatisfiability preservation.

## Motif generalization may fake proof compression.

G11 requires every generalized reuse to be concretely checked or parametrically instantiated and verified.
