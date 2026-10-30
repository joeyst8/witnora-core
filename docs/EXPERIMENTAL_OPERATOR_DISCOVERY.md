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

## Structure-guided invention and falsification round

The second experimental loop adds
`witnora_core/structural_operator_invention.py`:

- **Minimum fill:** prefer eliminating a variable whose clause graph would
  introduce the fewest missing neighbor connections.
- **XOR boundary:** prefer eliminating variables outside the detected exact
  binary-parity backbone.
- **Maximum clause release:** choose the bounded resolution elimination with
  the greatest immediate clause-count reduction.

These are **proposed elimination-order heuristics**, not new logical rules.
All use ordinary Davis–Putnam resolution; their hypotheses concern which
order produces useful structural simplifications.

`tests/test_structural_operator_invention.py` compares all three policies
against exhaustive SAT truth on 100 seeded random small formulas. The general
multi-operator search and its disjoint-seed held-out experiment also include
these strategies.

`witnora_core/operator_counterexamples.py` and
`scripts/find_operator_counterexamples.py` detect cases where a two-step
operator sequence provides no positive advantage over the best single
operator. They greedily delete clauses while preserving that negative
interaction signal, then independently check SAT truth on the minimized
original and transformed CNFs. The CI publishes complete minimized DIMACS
examples and SHA-256 hashes so future generators can target the failures.

**Current evidence:** The invariant-policy unit tests, updated train/holdout
ledger, and minimized-negative-example job pass in GitHub Actions. These
experiments are small, and held-out seeds come from the same problem
generators; this is not an independently sampled distribution shift.
The next genuinely scientific test should use unfamiliar families, larger
benchmarks and ablations that separate heuristic value from the underlying
resolution algorithm.

## Out-of-distribution scientific challenge round

A new generator module, `witnora_core/ood_sat_families.py`, introduces five
families that were **not** used by the original synthetic binary-XOR training
loop:

1. Pigeonhole instances (including known contradictions).
2. Graph coloring (including K4/3-color and odd-cycle/2-color contradictions).
3. Degree-three K4 Tseitin parity, encoded as full three-variable XOR CNF.
4. N-Queens satisfiable and unsatisfiable boards.
5. Planted satisfying random 3-CNF.

The smaller generator truths are also checked by independent exhaustive
assignment tests. `scripts/benchmark_operator_ood.py` applies the frozen
sequences from the earlier training ledger **without refitting them** and
separately evaluates newly invented graph-invariant heuristics as exploratory
comparisons. For each input and transformed CNF, Glucose3 and Minisat22 must
agree on SAT/UNSAT, and Glucose3's SAT models must satisfy their own formula.

The experiment records original/transformed SHA-256, counts, structural
interaction gain versus the strongest single operator, repeated exploratory
Glucose3 timing, and explicit `lean_checked = 0`, `promoted = 0` fields.
Timing is necessarily noisy on small instances and must not be marketed as a
competitive speed improvement.

`scripts/screen_ood_candidates.py` predeclares an intentionally demanding
screen for **further investigation only**: positive *median* interaction gain
on at least three unseen families and a majority of all evaluated cases.
Every failure is retained and reported. An accepted follow-up would still
have `novelty_verified = False`, `lean_verified = False` and
`performance_advantage_verified = False`.

The OOD generator tests, independent-solver benchmark, and follow-up screen
all passed their initial CI steps. This is materially stronger than unseen
seeds from the same original generator, but these remain small human-designed
families. Industrial or competition SAT data, larger distributions, repeated
machines, independent operator novelty review, and rigorous performance
comparisons are the next requirements before any scientific breakthrough
claim.

## Larger unfamiliar-instance stress gate

The second preregistered stage, `scripts/benchmark_ood_larger.py`, reads
`ood-candidate-screen.json` generated from the frozen independent-family screen.
It tests at most two top-ranked surviving candidate sequences on larger unseen
instances: 5-into-4 and 6-into-5 pigeonhole, K5 coloring, six-vertex complete
graph high-arity Tseitin parity (consistent and inconsistent), 5/6 queens,
and seeded planted 30-variable 3-CNF. The fresh seeds are 401 and 509.

If no candidate clears the first screen, the next stage **still runs** but
labels every record `NO_SURVIVOR_NEGATIVE_CONTROL` instead of promoting an
operator. Each record includes input/residual hashes, independent Glucose3 and
Minisat22 agreement, structural interaction gain, and measured preprocessing
and solution times. All candidates remain experimental (`lean_verified=false`,
`novelty_verified=false`, `promoted=false`). This gate is not a proof of
satisfiability preservation for arbitrary formulas, speedup, or mathematical
novelty. Its purpose is to try to falsify promising structural claims.
