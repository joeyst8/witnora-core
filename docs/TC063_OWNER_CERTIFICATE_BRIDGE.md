# TC-063: Occurrence-Aware Owner-Certificate Bridge

Status: **Python prototype checked on finite tests; Lean universal proof OPEN.**
Date: 2026-11-02. Scope: SAF(c,r), not arbitrary SAT and not P vs NP.

## Why this checkpoint exists

The public Python `CNFFormula` constructor canonicalizes literals, removes
tautological clauses, and deduplicates/sorts clauses. A previous Lean clause
routing lemma reasons about *every raw clause occurrence*, including duplicate
and empty clauses. A semantic normalization bridge is required before these
representations can be identified. Do not interpret a normalized Python
clause index as a source-DIMACS occurrence index.

G14's existing `_component_dicts` obtains an owner from a Python primal-graph
traversal. To derive soundness, it is not necessary to formally verify that
entire traversal if a separate, small certificate checker checks the output
of the traversal against the original clause occurrences.

## Explicit verifier

`witnora_core/tc063_owner_certificate.py` introduces two independent
functions:

- `verify_owner_partition(raw_clauses, S, claimed_components)` checks
  disjoint exact coverage of the non-separator variable set, one-based source
  clause occurrence coverage, exact ownership of all non-separator clauses,
  component boundary variables, and a distinct separator-only clause bucket.
  It does **not** trust connected-component traversal, require maximality,
  or call the G8/G14 owner builders.
- `condition_verified_partition(..., alpha)` conditions all occurrences
  under a **total Boolean** separator assignment, retaining empty clauses
  and duplicates in their own buckets and dropping only satisfied clauses.

The owner certificate can accept non-maximal partitions, but only if every
non-separator clause fits wholly inside a single block. This is sufficient
for soundness and may lose efficiency. Discovery of a small separator and
completeness of the graph algorithm are independent performance concerns.

## Universal theorem to kernel-check next

Let `F = [C_1, ..., C_m]` be an occurrence-indexed raw CNF, `S` a set of
variables, and `B_1, ..., B_k` pairwise disjoint blocks covering exactly
`Vars(F) - S`. For each `C_j`, require either:

1. `Vars(C_j) - S = empty`, making it a separator-only clause; or
2. one unique `i` satisfies `Vars(C_j) - S subset B_i`.

For every total assignment `a` and `alpha = a|S`, let `R_0(alpha)` be
the residual clauses from case 1 and `R_i(alpha)` those owned by block `i`,
after removing satisfied separator literals and deleting satisfied clauses.

Then prove in Lean (not yet claimed):

```
Sat(F, a)
  <-> Sat(R_0(alpha), a)
      and (forall i, Sat(R_i(alpha), a))
```

This theorem must treat `[]` as a false clause, not an omitted clause.
It does not require any primal-graph or DFS theorem once the owner
certificate hypotheses are checked.

The corresponding branch-UNSAT rule is:

```
Unsat(F) <->
  forall alpha over S,
    Unsat(R_0(alpha)) or (exists i, Unsat(R_i(alpha)))
```

provided each residual family is interpreted with its unrestricted local
variables and the blocks are disjoint. For a SAT certificate, one `alpha`
and compatible models of all residual buckets suffice; independently
check the lifted model against the original CNF as an additional guard.

## Raw-to-normalized proof obligation

Prove, for all assignments `a`:

```
Sat(raw_clauses, a) <-> Sat(CNFFormula(raw_clauses).clauses, a)
```

by separately establishing:
- literal duplicate elimination preserves disjunction;
- tautological clauses are always true;
- duplicate clause elimination preserves conjunction;
- sorting clauses/literals preserves semantics;
- empty clauses are retained as contradictions.

Then connect source-DIMACS occurrence IDs to the normalization map or
explicitly verify a normalized formula at the new trust boundary.

## Validation and limitations

The Python prototype's five in-memory unit tests passed, including 800 seeded
randomized raw formulas and over 25,000 exhaustive assignment comparisons.
A separate JS structural prototype checked 1,600 random formulas.

**These are finite tests, not Lean theorems.** The Python checker is not yet
wired into G14's production acceptance gate and no Lean kernel acceptance
is claimed for this new module.

Next:
1. Encode and prove the owner partition equivalence lemma in Lean 4.
2. Prove semantics preservation of raw CNF normalization and DIMACS parsing.
3. Bind G14 certificate generation to this independent verifier, including
   separator-only branch blockers, and add end-to-end negative mutation tests.
4. Connect exact G5 certificate outcomes to the branch-UNSAT rule and finish
   `checked_ascii_dimacs_g14_unsat` on TC-063's source instance.

The restricted `SAF(c,r)` polynomial bound still applies only when `c`
and the supported affine extraction bound `r` are fixed. No theorem
completeness, general SAT breakthrough, or P-vs-NP claim is made.
