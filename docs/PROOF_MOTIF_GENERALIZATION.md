# Proof Motif Generalization

## v2.20 Planner-Guided Execution Use

G13 can use G11 as an actual execution step only when the generalized motif
certificate verifies. A planned G11 step does not prove a macro-proof exists.
The execution certificate must show that the concrete generalized template,
reuse instantiations, and final contradiction checked.

v2.18 introduces `G11_PROOF_MOTIF_GENERALIZATION_CHECKER_PROTOTYPE`, promoted
from the v2.14 obstruction recommendation
`PROOF_MOTIF_NEAR_MISS -> PROOF_MOTIF_GENERALIZATION_CHECKER`.

## Soundness Boundary

Near motif similarity is not proof. A row is certified only when the checker
verifies one of these evidence forms:

- a generalized proof template plus checked parameter constraints;
- every concrete reuse instantiation expanded into valid proof steps;
- a concrete fallback expansion for every reuse site.

If those checks fail, the row is rejected or remains diagnostic-only.
Diagnostic-only motifs cannot certify SAT or UNSAT.

## Certificate

The native certificate records:

- original formula hash;
- detection and certification mode;
- base motifs;
- generalized templates and parameter constraints;
- reuse sites with source clause ids and substitution maps;
- fallback concrete expansions;
- compression summary;
- final macro-proof contradiction;
- claim boundary.

The checker verifies that each reuse maps to actual original clauses, every
substitution is safe, every instantiated proof expansion derives the claimed
lemma, and the final macro contradiction is supported by checked reuse sites.

## Non-Claims

G11 is native-only. It is not DRAT, not a theorem, not arbitrary proof-pattern
learning, not proof-motif completeness, and not P vs NP progress. Exact motifs
already handled by G6 are duplicate controls and are not counted as novel G11
deltas.

## CLI

```bash
python -m witnora_core.proof_motif_generalization run --instances ladder_near_4 ladder_near_8 chain_near_6 gadget_variants proof_motif_near_miss exact_motif_duplicate_control loose_similarity_reject --out-root outputs/v2.18-proof-motif-generalization-checker --strict
```
