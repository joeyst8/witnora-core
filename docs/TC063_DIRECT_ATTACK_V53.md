# Direct TC-063 attack: theorem target and first structural boundary (v53)

Draft PR #54, based on the all-component Lean-checked G14 fixtures. This change deliberately prioritizes the **top-level theorem** over incremental synthetic instance growth.

## The theorem now exposed in Lean

`formal/Witnora/TC063Direct.lean` defines proof-carrying `CoverData` and the precise remaining family-level obligation:

```
UnsatCoverComplete c SAF :=
  ∀ raw, SAF raw →
    (¬ ∃ assignment, signedCNFHolds raw assignment) →
    ∃ cert, cert.accepts c raw = true
```

The kernel checks `tc063_unsat_iff_checked_cover`: **if** this completeness property holds, then every member of the designated `SAF` family is UNSAT iff an accepted bounded G14/G5 UNSAT cover exists. It also checks `tc063_total_certificates_of_complete_cover`: SAT members have a concrete witness and UNSAT members have an accepted cover, **conditional on** the same premise.

Crucial: `UnsatCoverComplete` is an *explicit hypothesis*, **not a proved theorem or a new axiom**. There is no unconditional TC-063 result here. A runtime complexity theorem, a definition equating mathematical SAF membership with Python recognition, and universal Python-to-Lean refinement also remain open.

## First direct adversarial finding

Native tests now probe:

- A supported `saf_unsat_cover_2` input with supplied separator: accepted as family member.
- The same case with **automatic** separator recognition: accepted.
- A deliberately non-affine component: rejected.
- A separator exceeding the fixed bound: rejected.
- The structured input plus a *logically redundant weakened clause* (original clause extended with a new positive literal): rejected by native structural membership validation with `COMPONENT_NOT_EXACT_AFFINE`.

The last test is a meaningful boundary: adding a clause logically implied by an existing clause does not change the models. Lean's new `covered_clause_extension_iff` proves this equivalence for **every** CNF and assignment whenever the clause-coverage check accepts. Yet Python's existing exact-source-coverage notion rejects the modified structured example.

That is **not a refutation of TC-063** unless the family `SAF(c,r)` is intended to be closed under logically redundant CNF extensions. It exposes a decision we must settle mathematically: is `SAF(c,r)` defined semantically (any CNF equivalent to an exact affine residual system), or syntactically (a recognized exact clause encoding with prescribed source coverage)? Those are different families, and we cannot claim completeness for the broader one using the current validator.

## Next decisive work

1. Give `SAF(c,r)` an independent Lean mathematical definition, not one copied from Python acceptance.
2. Decide whether redundant logically implied clauses must preserve membership. If yes, the native recognizer requires a proof-producing semantic coverage extension, and the redundant-clause fixture is a concrete regression target. If no, narrow the theorem wording to a syntactic family and explain the closure restriction prominently.
3. Attempt `UnsatCoverComplete` for that *exact* definition. The actual hard subgoals are separator recognition, complete affine extraction, G5 certificate production, and bounded-cost implementation.
4. Treat any counterexample in the mathematically claimed family as a high-priority theorem blocker. Do not extend the size ladder as a substitute.
