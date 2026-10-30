# Experimental Operator Discovery — rapid-prototyping sprint

This research track deliberately generates speculative operator compositions
**before** formal proof. It never upgrades a speculative transformation to
a trusted solver status or labels ordinary SAT operations mathematically novel.

## First executable prototype

`witnora_core/experimental_operator_search.py` searches bounded sequences
of four operators:

1. `parity_root`: existing exact binary-XOR component substitution.
2. `unit_propagation`: repeated unit-clause simplification.
3. `subsumption`: remove clauses implied by another existing clause.
4. `bounded_elimination`: one size-limited Davis–Putnam variable elimination.

A beam search of up to three operators (configurable to depth five) retains
distinct canonical CNF outputs, their full operator sequences, source and
candidate SHA-256 hashes, variable/clauses/literal reductions, and scores.
The score is a cheap structural **ranking heuristic**. It is not a claim
about runtime, correctness, novelty or mathematical generalization.

All records explicitly carry:
`UNVERIFIED_DISCOVERY_CANDIDATE`,
`lean_verified = False`,
`novelty_verified = False`,
`promoted = False`.

## Test first, explain later

`tests/test_experimental_operator_search.py` independently enumerates all
Boolean assignments for 120 seeded small random CNFs, testing each primitive
and all returned compositions for exact SAT/UNSAT agreement.

`scripts/experiment_operator_discovery.py` splits synthetic adversarial
families by disjoint random seeds:

- **Training:** operator sequence exploration and ranking.
- **Holdout:** apply selected sequences to previously unseen seeds.
- **Oracles:** Glucose3 and Minisat22 independently agree on original and
  transformed satisfiability.
- **Interaction score:** compare each sequence to the strongest single
  operator on that same instance. Positive interaction gain is only a
  *candidate for further investigation*.
- **Failure learning:** retain examples with no structural gain or negative
  gain alongside positive results, so future searches can learn the limits
  of a sequence rather than training solely on successes.

The CI emits a machine-readable CSV experiment ledger. Every row binds the
source/candidate hashes, train/holdout split, seed, problem family, sequence,
structural score, oracle truth and promotion restrictions.

## What this does not establish

These four transformations are existing SAT techniques. A combination
showing positive interaction gain is **not** automatically a new theorem or
a competitive algorithm. The small generated cases cannot establish
generalization to industrial SAT, algebraic coding, hardware verification,
cryptanalysis or combinatorial optimization.

The next sprint should introduce genuinely exploratory operators
(invariant-guided elimination orders, graph separator rewrites, discovered
symmetry schemas), then run larger unseen benchmarks, train/holdout
ablation studies, automatic counterexample minimization, and independent
novelty review. Only the most compelling survivors should be formalized in
Lean and considered for the verified production gate.
