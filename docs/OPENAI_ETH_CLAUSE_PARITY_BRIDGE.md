# OpenAI ETH mathematics → Witnora clause-violation parity bridge

**Research checkpoint:** 2026-11-03 UTC · draft PR #121 · branch
`formal/g14-python-seen-enqueue-v121`

## What was borrowed, and what was not

OpenAI's October 2026 *Exponential Time Hypothesis is false* preprint
combines sparse parity checks on **clause-violation vectors**, a
combinatorial isolation/reduction argument, interpolation/low-degree
polynomials, and Boolean tensor-network contraction. The work was released
for independent expert review. ETH ≠ P versus NP: even a correct
subexponential-time exact counting method would not establish P = NP.

Primary references:
- [OpenAI October 26 research announcement](https://openai.com/index/building-scientific-understanding-with-academic-communities/)
- [OpenAI source, Lean scope](https://github.com/openai/math/blob/main/lean/docs/378.md)
- [OpenAI full ETH preprint sources](https://github.com/openai/math/tree/main/preprints/The-Exponential-Time-Hypothesis-is-False-October-25-2026)

Here we implemented only a small, intentionally exhaustive **mathematical
analogue of the first parity construction**. We have not implemented
expander-based deterministic sparse checks, the exact-counting reduction,
interpolation, Boolean tensor contraction, or any subexponential algorithm.

## Exact mathematical distinction

For a source CNF with clauses C_0, ..., C_(m-1), define for each Boolean
assignment x:

    v_j(x) = 1  iff  clause C_j is false under x.

A selected row R ⊆ {0,...,m-1} imposes

    ⊕_(j∈R) v_j(x) = 0          (arithmetic over F₂).

Let A be the binary incidence matrix of all rows. Then

    F(x) = true  ⇒  A v(x) = 0

for **every** CNF, without requiring affine structure or a small
separator. But the reverse can fail: two violated clauses cancel in a
parity test. Exact equivalence is obtained only if

    {v(x) : x∈{0,1}ⁿ} ∩ ker(A) = {0}.

In particular, the reduction exploits that *realizable* violation
vectors are constrained by n Boolean variables. Parity rows are linear
in the violation-vector space, **not** necessarily in original SAT
variables. For k-CNF, each v_j(x) is a multilinear polynomial of degree
at most k. This is why the existing G5 Gaussian-elimination kernel does
not alone solve the derived system.

## What the new code does

- `witnora_core/eth_clause_violation_parity.py` builds
  source-identity-bound, sparse parity rows on clause-violation bits.
- The construction greedily chooses among deterministic candidate rows
  of 2–5 source-clause IDs. It explicitly enumerates all 2ⁿ assignments
  to select rows and rechecks both directions of equivalence.
- It fails closed for invalid clause IDs, modified sources, and overlarge
  experiments (n > 14).
- `formal/Witnora/ClauseViolationParity.lean` proves the universal
  implication that every CNF model passes **all** parity rows.
- `scripts/generate_eth_clause_violation_parity_lean.py`
  emits kernel-reduction checks for both directions on the identical
  8-variable Glucose dense UNSAT and planted-SAT controls.
- `tests/test_eth_clause_violation_parity.py` exhaustively
  rechecks all six frozen sources and adversarially verifies that
  tampered sources and insufficient parity rows fail.

## Independent small-instance diagnostic (local run)

The cases are the exact existing deterministic dense 3-CNF source seeds
from `scripts/generate_glucose_dense_3sat_lean.py`, with a
complete primal co-occurrence graph and no small variable separator.

| Variables | Clauses | Seed | Source | Satisfying assignments | Greedy parity rows | Bad assignments remaining |
|---:|---:|---:|---|---:|---:|---:|
| 8 | 54 | 638000 | UNSAT | 0 | 6 | 0 |
| 8 | 54 | 738000 | planted SAT | 1 | 6 | 0 |
| 10 | 66 | 640000 | UNSAT | 0 | 7 | 0 |
| 10 | 66 | 740000 | planted SAT | 1 | 9 | 0 |
| 12 | 84 | 642000 | UNSAT | 0 | 9 | 0 |
| 12 | 84 | 742000 | planted SAT | 5 | 9 | 0 |

The 12/84 UNSAT survivor counts, from initial source-nonmodels to zero,
were 4096 → 2048 → 1024 → 480 → 214 → 97 → 38 → 14 → 3 → 0.
For 12/84 planted SAT they were
4091 → 2171 → 1003 → 491 → 221 → 87 → 29 → 10 → 2 → 0.

**Interpretation:** the finite instances permit very short exact
parity-sketch representations, even without small primal separators.
This is an experimental structural observation, **not** evidence of
faster SAT solving: constructing the sketch required checking every
assignment and the resulting nonlinear parity system still needs solving.

## Proof boundary and next milestone

1. **Lean:** kernel check the universal source-model implication; then
   kernel-reduce both directions on the two frozen 8-variable instances.
   Treat any CI failure as an unfinished obligation, not a passed theorem.
2. **Independent search:** replace exhaustive greedy row selection by
   structure-aware sparse isolation (e.g. expander-derived checks and
   a sound deterministic refinement). Prove its detection condition
   without enumerating satisfying assignments.
3. **Algorithmic bottleneck:** implement and audit the *counting* side
   (shared polynomial/tensor representation, modular exact arithmetic,
   contraction/interpolation) and measure real runtime, memory and
   worst-case growth against CDCL.
4. **Stress tests:** frozen held-out random and adversarial CNFs, including
   parity collisions, high density, and sources whose residuals have no
   small separators. Carry exact source provenance into Lean.

The next bottleneck is **finding and counting the sketch's solutions
efficiently**, not merely compressing the number of equations.


## CI verification recorded

The full general-resolution gate passed on 2026-11-03:
[GitHub Actions run 41606445630](https://github.com/joeyst8/witnora-core/actions/runs/41606445630).
It built the universal Lean clause-violation parity theorem (axioms:
`[propext, Quot.sound]`), exhaustively executed Python source-identity
and tamper tests on all six cases, kernel-reduced both equivalence
directions on the two dense 8-variable sources, and passed the previously
existing general-CNF resolution/RUP regression suite. This is *proof
soundness and finite exactness*, not faster SAT search.
