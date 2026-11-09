# WU-004 — Verified affine-resolution baseline and bounded RUP(⊕) minimization

**Status:** five Rust tests pass. Two separate outcomes: (A) reproducibility
of *established* CDCL(⊕) affine conflict learning; (B) a finite diagnostic
showing nonunique, certified clause strengthenings. No claim of an original
theorem, solver-speed improvement, or progress on P versus NP.

## Established-paper anchor

Paul Beame and Glenn Sun, *Extending CDCL to Disjunctions of Parity
Equations*, SAT 2026, DOI **10.4230/LIPIcs.SAT.2026.5**.

- **Definition 2.8 / Proposition 2.10:** affine resolution computes
  `span(neg(C),neg(R),1) ∩ span(P)` for complementary uses of a newly
  propagated equation against earlier-unit space `P`.
- **Algorithm 3 / Proposition 3.8:** reversing these steps yields an
  asserting learned XNF clause.
- **Section 7:** LRUP(⊕) checks learned clauses by parity unit propagation.
- **Section 8:** a graph-theoretic notion of genuine parity first-UIP and
  principled semantic clause minimization remain explicitly open.

This diagnostic reimplements those known semantic operations independently
in Rust. Its output must not be confused with a new CDCL(⊕) algorithm.

## Outcome A: verified baseline for future frontier research

The standalone code uses augmented GF(2) equation rows, polynomial-time
Gaussian intersection via nullspaces, and explicit affine resolution:

    F_next = (span(F_current, F_reason, 1)) ∩ P_before_propagation.

No Boolean assignments are enumerated. For every learned clause we also
start a *separate* exact parity-unit-propagation check from its falsifying
space. This RUP(⊕) check must reach contradiction using the original clauses.

| Gate | Result |
| --- | ---: |
| Classical reason-graph traces (4 and 5 variables) | 4,872 |
| Disagreements with classical graph first-UIP | **0** |
| Equivalent propagation representatives in the WU-002 non-CNF example | **8/8 same learned span** |
| Unsound learned clauses by separate RUP(⊕) verifier | **0** |
| Basis transformations tested for the minimization candidate family | **168/168 invariant** |

The CNF result is restricted to a single current decision level with a
positive decision, ordinary positive propagations, and one terminal
conflict. The gauge result uses the non-CNF XNF witness in WU-002. Neither
is a general proof of a new semantic 1-UIP characterization.

## Outcome B: verified clause minimization need not be unique

Consider four Boolean variables `x,y,a,b` and the following original
clauses (all ordinary CNF; used as a calibration case):

    R_b:    ¬x ∨ ¬a ∨ b
    R_bot:  ¬y ∨ ¬b
    I_xy:   ¬x ∨ y
    I_yx:   ¬y ∨ x

One valid partial trail has decision `x=1`, propagation `y=1`, then
decision `a=1` and propagation `b=1`, after which `R_bot` conflicts.
Resolving `R_b` with `R_bot` on `b` derives

    C = ¬x ∨ ¬y ∨ ¬a.

Its falsifying affine space `F=span(x=1,y=1,a=1)` has rank three. A
**strictly stronger** XNF clause corresponds to a *proper* lower-rank
subspace `H` of `F`, because it forbids a larger set of assignments.

There are exactly `2^3−1=7` codimension-one subspaces (hyperplanes) of
`F`. We enumerated these **subspaces of equations, not Boolean
assignments**, and checked each candidate with original-formula RUP(⊕).

| Metric | Exact finite result |
| --- | ---: |
| Rank-two hyperplanes examined | 7 |
| Proof-certified strict strengthenings | **4** |
| Rejected (no contradiction derived by RUP(⊕)) | 3 |
| Unit-propagation clause scans in the certificates (fixed order) | **3–6** |

At least two validated candidates are incomparable:

    C_x = ¬x ∨ ¬a
    C_y = ¬y ∨ ¬a.

Both are genuinely stronger than `C`, but neither implies the other as
an unrestricted Boolean formula. Their soundness here comes from the
original clauses `x→y` and `y→x` and the conflict reasons. The 4
certified rank-two candidate subspaces have equal rank, but different
proof-replay scan counts under the chosen fixed clause order.

### What this establishes and what it does not

It establishes an *explicit finite example* of multiple incomparable,
RUP(⊕)-verifiable strengthenings, which forces any practical minimizer to
specify an objective. It does **not** establish a new theorem about clause
minimization, a scalable algorithm, or a measurable improvement to Xorcle.

The complete hyperplane oracle examines `2^d−1` candidates for rank `d`;
this is exponential in `d` and subject to a strict diagnostic budget of
`d≤10`. **It is not a proposed arbitrary-SAT solving method.** The
certificate-scan counts are a local verifier-cost proxy, not solver wall
time or an independent performance benchmark.

## Reproduce

Rust: `rust/witnora-ve/src/bin/wu004_affine_cut_baseline.rs`

```bash
cd rust/witnora-ve
cargo test --release --bin wu004_affine_cut_baseline
cargo run --release --bin wu004_affine_cut_baseline
```

Five deterministic tests cover CNF-first-UIP conservativity (4,872 cases),
eight non-CNF row gauges with separate RUP checks, affine intersection
rebasing, the four certified hyperplanes, and hyperplane-family invariance
under all 168 invertible 3-row generating bases.

## WU-005 frontier question

**Can a basis-invariant, reason-guided procedure find a useful certified
strict strengthening *without enumerating all `2^d−1` hyperplanes* and
while actually reducing proof/solver costs?**

Required falsification gates:

1. Certify every candidate with independently replayable LRUP(⊕)-style
   unit propagation. A single false certificate fails the method.
2. Show invariance of selected *subspaces* under equivalent equation-basis
   changes, or explicitly declare a basis-dependent heuristic.
3. Compare against both (i) no minimization and (ii) the bounded exact
   hyperplane oracle on small instances, reporting missed opportunities.
4. Measure real construction time and solver search time, not just clause
   count or proof length. Pre-register independent XNF/CNF families and
   compare against published Xorcle and standard CDCL baselines.

Research integrity: No new complexity bounds or general polynomial-time
SAT claims. The open 1-UIP and minimization questions remain open.
