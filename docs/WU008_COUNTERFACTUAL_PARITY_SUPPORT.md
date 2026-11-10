# WU-008 — Counterfactual parity support selection: redundancy and cost

**Status:** bounded algebraic falsification, explicit adverse witnesses,
independent RUP(⊕) replay and synthetic proof-pipeline microbenchmarks.
This is **not** a new SAT solver, complexity proof, or demonstrated
improvement in SAT solving time.

## Established research boundary

- Beame & Sun, *Extending CDCL to Disjunctions of Parity Equations*, SAT
  2026, [DOI 10.4230/LIPIcs.SAT.2026.5](https://doi.org/10.4230/LIPIcs.SAT.2026.5):
  known affine resolution and parity proof checks behind our testbed.
- Pollitt et al., *Factoring Learned Clauses*, SAT 2026,
  [DOI 10.4230/LIPIcs.SAT.2026.28](https://doi.org/10.4230/LIPIcs.SAT.2026.28):
  already studies globally reusable XOR/ITE structure in CDCL. No
  novelty claim for caching or deletion-based simplification.
- Berlekamp, McEliece and van Tilborg, *On the Inherent Intractability
  of Certain Coding Problems* (IEEE Trans. IT, 1978),
  [DOI 10.1109/TIT.1978.1055873](https://doi.org/10.1109/TIT.1978.1055873):
  general binary linear-code decoding is NP-complete. Minimizing the
  number/weight of selected XOR rows representing a target syndrome is
  a form of the **established** minimum-weight linear-system problem.
  We do not claim arbitrary optimal support selection is polynomial.

WU-007 falsified indiscriminate global lemma caching: unrelated and
connected-but-useless lemmas inflate verifier work. WU-008 asks whether
we can *avoid proving useless lemmas*, while preserving the global
target information that enables the three certified strengtheners.

## Definitions, soundness and bounded oracle

Each candidate unit parity lemma is first *nominated* by known semantic
consensus on two complementary guarded XNF clauses; it is not admitted
as a premise until independent RUP(⊕) verification. Represent parity
equations as augmented GF(2) rows with the RHS bit. For the rank-three
target falsity space `F`, let

`A = F ∩ span(1, E1, ..., Em)`.

Here `1` is the RHS contradiction row. All candidate unit equations
are only **hypothetical** until selected and independently certified.
The support-selection objective is to keep a subset `S` of nominated
lemmas satisfying `A ⊆ span(1, E_i for i in S)`; because `S` is a
subset, this preserves exactly the full-set intersection `A` and its
candidate-hyperplane family. The original disjunctive clauses are never
incorrectly treated as unit equations.

Three methods are compared:

1. **H8A, independent leave-one-out:** keep `Ei` iff removing it from
   the **full set** destroys some part of `A`. It uses `m` Gaussian
   counterfactual tests. This is a candidate hypothesis, **not complete**.
2. **H8B, reverse deletion:** start with all candidate units and try
   deleting each in order, retaining a unit only when removal would
   lose part of `A`. The final set preserves `A` by construction; it
   need not minimize cost. We test natural order and descending-weight
   order. This is an **established class of simplification algorithms**.
3. **Exact diagnostic oracle:** test all `2^m` *reason subsets* for
   `m≤12` and select the minimum total weight preserving `A`. This is
   exponential in candidate count, and **does not enumerate Boolean
   assignments**. It is not a scalable research proposal.

The XNF fixture's proof-cost weight proxy `2(i+1)` is computed from
the position of a complementary guard pair; in this restricted clause
order, it equals the number of RUP clause scans to prove its lemma.
It is **not** a general predictor of learned-lemma proof cost; real
proof-cost estimation and its overhead remain unsolved.

## Finite controlled results

Each case uses a consistent original XNF formula and a rank-three
target. All three final candidate hyperplanes are separately RUP(⊕)
verified after only the selected intermediate lemma proofs are added.

| XNF family | Candidate units | Leave-one-out selected / preserves target? | Cost-aware deletion selected | Exact minimum units | Proxy cost selected / exact | Total proof scans selected / all |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| Single XOR path, 4 edges | 4 | 4 / yes | 4 | 4 | 20 / 20 | 56 / 56 |
| Same path + 8 irrelevant connected leaves | 12 | 4 / yes | 4 | 4 | 20 / 20 | **104 / 240** |
| Two parallel 3-edge paths | 6 | **0 / no** | 3 | 3 | 12 / 12 | 57 / 87 |
| Parallel paths of 3 and 4 edges | 7 | **0 / no** | 3 | 3 | 12 / 12 | 63 / 107 |

Why H8A fails: in a parallel-path formula, removing **any one** edge
leaves the other path, so every edge looks unnecessary when separately
tested. But removing *all* individually unnecessary edges removes both
paths, losing the needed equation `x⊕y=1`. This is a concrete
counterexample to interpreting leave-one-out relevance as a safe
simultaneous selection rule.

## Exact cost-optimality is not achieved by greedy deletion

An abstract GF(2) witness has candidate rows `A`, `B`, `A+B+C`, `C`
with weights `3,3,1,4`, and goal `A+B`. It has two two-row
representations: `A+B` of cost **6**, and `(A+B+C)+C` of cost **5**.
Cost-descending deletion discards `C` first because the `A+B` alternative
remains; it then keeps the cost-6 alternative and misses cost 5.
The exact 16-subset oracle confirms these totals. This is a finite
greedy counterexample, not a new NP-hardness proof.

For **64 deterministically seeded** small parity graphs, each with
9 XNF guarded edge lemmas (and a planted consistent parity labeling):

- H8A fails to preserve the target global anchor in **64/64**.
- Cost-descending deletion preserves all three independently verified
  final hyperplanes in **64/64**.
- It is *more expensive than the bounded exact support oracle* in
  **15/64** cases; the sum of excess proxy cost over those 64 cases
  is **42**.
- The exact oracle evaluates 512 reason subsets per instance, which
  is deliberately not proposed as a scalable method.

These 64 cases were generated from a fixed set of seeds (`0..63`);
they are **not** an independently held-out industrial benchmark or a
trained statistical predictor. Their only scientific purpose here is
to test whether a proposed deterministic selection rule survives
redundant parity explanations.

## Does selection cost erase the apparent savings?

Proof-scan counts exclude candidate discovery and the Gaussian
counterfactual tests. To expose that omission, the Rust implementation
also times two entire small pipelines: (a) discover *all* semantic
consensus candidates, certify all, then verify hyperplanes; (b) discover
the same candidates, perform weighted deletion, certify only retained
lemmas, then verify hyperplanes. Each pipeline uses seven timing batches
of 25 runs after four warmups. One local release-mode run produced:

| Synthetic XNF case | Prove all (µs) | Select then prove (µs) |
| --- | ---: | ---: |
| Four-edge path, no noise | **18.5** | 19.9 |
| Four-edge path + eight leaves | 194.3 | **179.4** |
| Two redundant 3-edge paths | 38.5 | **36.8** |
| Seeded graph #17 | 85.7 | **76.8** |

A repeat run gave similar qualitative rankings but slightly different
numbers. *Even reducing certificate scans by more than half on connected
noise delivered only a modest elapsed-time reduction*, because discovery
and counterfactual Gaussian work remained. On the simple un-noisy path,
selection actually lost. These are **microbenchmarks of this prototype**,
not production SAT search times or solver-level speedups.

## Verification, limits and next falsification gate

Implementation:
`rust/witnora-ve/src/bin/wu008_counterfactual_support.rs`.

- Every selected lemma passes independent RUP(⊕) against the original
  clauses before it becomes a premise for a final candidate.
- Every final reported candidate passes separate RUP(⊕) against the
  corresponding extended formula.
- Algebraic support preservation is checked against the *full* anchor,
  not just one chosen representation.
- The code reuses WU-006's independent GF(2) and RUP implementation;
  only the visibility of two helper functions was extended.
- No Boolean assignments are enumerated; the exact oracle searches
  *reason subsets* (exponential, bounded).

**Decision:** reject independent leave-one-out simultaneous selection;
retain deletion as an honest, sound baseline, but not an optimal or
universally beneficial policy. The unsolved engineering/science question
is whether a **cheap, generalizable** model of useful parity subspaces,
including future reuse and proof cost, can beat (i) no minimization,
(ii) deletion-based selection and (iii) existing factoring/vivification
when integrated into actual SAT search on held-out formulas. WU-009
should move to solver integration or explicitly stop claiming practical
progress until such integration is available.

### Reproduction

```sh
cd rust/witnora-ve
cargo test --release --bin wu008_counterfactual_support
cargo run --release --quiet --bin wu008_counterfactual_support
cargo test --release --all-targets --quiet
```
