# WU-006 — Guarded-XNF consensus, gauge invariance and staged certificates

**Status:** six deterministic Rust tests, bounded oracle and a single
explicit falsifying model. All results below are about finite synthetic
instances or a restricted, *established* inference rule. There is **no**
new parity-resolution theorem, general SAT algorithm, or speedup claim.

## Literature and precise question

Paul Beame and Glenn Sun, *Extending CDCL to Disjunctions of Parity
Equations*, SAT 2026, DOI [10.4230/LIPIcs.SAT.2026.5](https://doi.org/10.4230/LIPIcs.SAT.2026.5),
Definition 2.2 (semantic clause falsity as an equation subspace),
Theorem 2.5 (addition and change of basis), Definition 2.8
(affine resolution), and Section 3.1 (parity unit propagation).

WU-005 found that a reason-local intersection heuristic misses all three
certified rank-two strengthenings on unit-parity chain constraints,
whereas one global Gaussian calculation recovers them. Extending that
calculation by falsely treating every *disjunct* as asserted would be
unsound. **WU-006 tests a sound, narrow route through intermediate
clauses**, and specifically tests the difference between a valid
consequence and direct RUP(⊕)-certifiability.

## Intrinsic two-clause consensus (known parity resolution)

Let `G1`, `G2` be the **falsity equation subspaces** of two XNF clauses.
Compute `K=G1∩G2` over GF(2). When both `dim(Gi/K)=1`, and the constant
contradiction equation `1` belongs to `G1+G2`, their conjunction implies
the clause whose falsity space is `K`. This is an instance of the
published parity-resolution framework, written intrinsically; the
implementation makes **no originality claim for this rule**.

Reason: modulo `K`, the two extra independent equations differ by the
contradiction `1`. Both clauses could hold under all of `K` only if both
of these complementary equations were simultaneously falsified, which is
impossible. The construction is independent of the generators selected
for the input XNF clauses. Every emitted intermediate lemma is still
checked by a separate fixed-point RUP(⊕) replay.

The diagnostic considers only non-tautological unit conclusions of this
rule (rank-one `K`), not arbitrary multi-equation resolvents.

## Guarded unit-XOR path family

For every integer `m≥2`, reuse the WU-005 path:

`x — z1 — ... — z(m−1) — y`.

Each edge asserts equality of its endpoints except the final edge,
which asserts inequality; together these constraints imply `x⊕y=1`.
But replace each unit parity assertion `Ei` by the **two genuine
disjunctive-XNF clauses**

`(pi=0 OR Ei)` and `(pi=1 OR Ei)`,

using a separate, otherwise unconstrained guard variable `pi` per edge.
Each input clause has a rank-two falsity space. The pair semantically
resolves to `Ei`; there are `m` such verified intermediate lemmas.
The target has falsity `F=span(x=1,y=1,a=1)`, rank three, with seven
rank-two hyperplanes.

Crucial certificate distinction: on these instances, starting RUP(⊕)
directly from **each target hyperplane** against the original guarded
formula does not propagate a first equation, so none of seven passes
directly. Each lemma `Ei`, however, is independently RUP(⊕)-certifiable
from the original guarded clauses. After *logging those m lemmas*,
unit-XOR global Gaussian closure nominates three hyperplanes, and all
three RUP(⊕)-verify against the augmented formula.

| Edges m | Direct target RUP certified / 7 | Intermediate unit lemmas independently certified | Final hyperplanes certified after lemmas | Lemma replay scans | Final replay scans | Direct oracle scans (failed) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 0 | 2 | 3 | 6 | 18 | 28 |
| 3 | 0 | 3 | 3 | 12 | 27 | 42 |
| 4 | 0 | 4 | 3 | 20 | 36 | 56 |
| 5 | 0 | 5 | 3 | 30 | 45 | 70 |
| 6 | 0 | 6 | 3 | 42 | 54 | 84 |

The numbers are deterministic **clause scans performed during certificate
replay**, *not* measured runtime, total solver work, or competitive
SAT benchmarks. In fact, the staged proof-scan sum exceeds the failed
direct-oracle scans for `m≥5`. The latter certifies no strengtheners,
so these counts should not be interpreted as a speedup comparison.
The overall inference is a combination of **known** parity resolution,
intermediate lemma checking and global Gaussian elimination for units.

## Soundness traps and stress checks

1. **False globalization example:** `(p=0 OR E1)` together with
   `(p=1 OR E2)` does not assert both `E1` and `E2` when they differ.
   Choosing `E1: x⊕z=0`, `E2: y⊕z=1`, the single explicit assignment
   `x=y=a=1, z=0, p=0` satisfies both clauses while falsifying the
   proposed target, and thereby all seven target hyperplane clauses.
   Thus the naive globalization would derive **three unsound**
   hyperplane candidates; independent RUP(⊕) rejects all seven.
   The safe semantic consensus rule correctly rejects this pair.
   This is **one constructed model**, not assignment enumeration.
2. **Gauge test:** all `6×6=36` ordered rank-two bases for each input
   guarded-pair (two edges) yield exactly the same derived subspace;
   independent RUP verifies every representation. The test also
   changes literal-looking representatives explicitly.
3. **Subspace-pair stress:** of the 35 rank-two subspaces of the
   four-dimensional augmented GF(2) equation space (3 variables),
   discard seven containing `1`, leaving **28 consistent subspaces**.
   All **378 unordered pairs** are inspected; the rule applies to
   **42** and all 42 derived clauses pass independent two-premise
   RUP(⊕). This enumerates *equation subspaces*, never assignments.
4. **Staged verification:** for each `m=2..6`, every intermediate
   lemma is checked against the original guarded formula and each
   final candidate is checked against original clauses **plus
   individually verified lemmas**. There is no unverified inference
   added as a premise.

## Research decision and WU-007 gate

We can extract useful parity information from guarded disjunctive XNF
without pretending its disjuncts are units. However, a **proof-provenance
and cost problem remains**: a useful global parity closure may require
logging intermediate clauses that direct RUP will not discover on its
own. This family alone is not a frontier speedup.

Next: pre-register independently generated XNF/CNF families and measure
whether sharing selected intermediate lemmas across **multiple** conflict
cuts amortizes (i) pairwise matching cost, (ii) lemma proof scans, (iii)
global elimination, and (iv) the resulting changes to solver search.
Compare against no minimization, exact bounded oracle, and published
Xorcle / standard SAT baselines; explicitly report losing cases.
The code currently has no production CDCL integration, wall-time
benchmarks, or serialized LRUP(⊕) proof format. Do not advertise those.

## Reproduce

Rust implementation: `rust/witnora-ve/src/bin/wu006_guarded_xnf_consensus.rs`.

```sh
cd rust/witnora-ve
cargo test --bin wu006_guarded_xnf_consensus
cargo run --quiet --bin wu006_guarded_xnf_consensus
cargo test --release --all-targets --quiet
```
