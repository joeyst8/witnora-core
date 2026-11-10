# WU-009 — Certified parity deductions in actual DPLL search: an end-to-end negative result

**Status:** implemented, release-mode benchmarked, independently cross-checked
against Boolean-CNF RUP on bounded examples. This is **not** a production
CDCL solver, a solver speedup, or a new parity inference rule.

## Scientific question

WU-008 reduced the number of RUP(⊕) scans needed to prove candidate
parity lemmas. This was *not* evidence that these lemmas reduce the actual
time required to solve SAT. Here we put both variants in an instrumented
Rust SAT-search loop and ask:

> Does the reduction in DPLL work pay for discovering, selecting, proving
> and encoding the parity deductions before solving a source CNF?

The claim being tested is deliberately narrow. The source search engine
is a deterministic, unoptimized DPLL with Boolean unit propagation,
degree-based variable order, and exhaustive *search only as necessary*.
It is distinct from Witnora's separate width-bounded model-counting
engine in `lib.rs`. This test does not simulate Xorcle, industrial CDCL,
clause learning or a real incremental solver.

## Literature boundary

- Paul Beame and Glenn Sun, *Extending CDCL to Disjunctions of Parity
  Equations*, SAT 2026, DOI
  [10.4230/LIPIcs.SAT.2026.5](https://doi.org/10.4230/LIPIcs.SAT.2026.5):
  Xorcle already implements CDCL(⊕), affine learning, and LRUP(⊕).
- Tero Laitinen, Tommi Junttila and Ilkka Niemelä, *Extending Clause
  Learning SAT Solvers with Complete Parity Reasoning*, 2012,
  [arXiv:1207.0988](https://arxiv.org/abs/1207.0988):
  incremental Gauss–Jordan XOR deductions inside DPLL(XOR) are established.
- *Proof Generation for CDCL Solvers Using Gauss-Jordan Elimination*,
  [arXiv:2304.04292](https://arxiv.org/abs/2304.04292):
  integrating XOR reasoning and proof logging has been studied.
- Pollitt et al., *Factoring Learned Clauses*, SAT 2026,
  [DOI 10.4230/LIPIcs.SAT.2026.28](https://doi.org/10.4230/LIPIcs.SAT.2026.28):
  learned-structure factoring is not a new idea introduced here.

There is **no originality claim** for the inference, ordinary unit
propagation, XNF-to-CNF expansion, proof checking, or selection heuristic.
The incremental engineering question of choosing useful *certified*
parity structures under total-cost constraints remains the research
target—not a discovered new theorem.

## Experiment design and correctness gates

Three variants solve exactly the same original CNF plus the same assumed
Boolean units:

1. **Plain:** convert original disjunctive XOR constraints and a rank-three
   target into CNF, then run DPLL.
2. **All certified:** discover all candidate two-clause semantic-consensus
   parity units, certify each against original XNF with independent
   RUP(⊕), generate and RUP(⊕)-check three target hyperplanes, encode all
   confirmed deductions as additional CNF clauses, then run DPLL.
3. **Selected certified:** same candidate discovery, but first run
   WU-008's descending-cost deletion to preserve the target affine
   intersection; certify and encode only the retained units plus the
   three validated hyperplanes, then run DPLL.

The DPLL engine uses the **actual expanded Boolean CNF** with unit
propagation and backtracking. Unlike the earlier proof-pipeline timing,
all measured wall times here include translation, candidate discovery,
counterfactual selection (where applicable), two stages of RUP(⊕), CNF
encoding and full DPLL SAT search. SAT answers are rechecked against the
unaugmented source CNF; every variant must return the same result.

The XNF-to-CNF translator enumerates only assignments of up to **three
variables within an individual clause** in these fixtures to produce
the exact equivalent CNF. There is no global Boolean-assignment
enumeration used for parity discovery. The DPLL search itself branches
as required for a complete search algorithm.

**Independent cross-representation check:** a separately written Boolean
CNF RUP implementation verifies every encoded new clause in staged
order against the original CNF and preceding certified additions. This
test does *not* rely on the affine RUP checker that produced the
deductions. It is still an internal checker, not an external formal
certificate checker or DRAT/LRAT output.

## Controlled observed results

One local release-mode run, medians of seven batches of twelve runs,
after three warmups:

| Case | Result | Plain DPLL nodes | All-certified nodes | Selected nodes | Full pipeline plain (µs) | All certified (µs) | Selected (µs) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Four-edge path | SAT | 4 | 1 | 1 | 2.5 | 21.6 | 22.7 |
| Four-edge path | UNSAT | 7 | 1 | 1 | 1.8 | 21.3 | 22.8 |
| Four-edge path + 8 leaves | SAT | 12 | 1 | **10** | 7.8 | 195.8 | 181.4 |
| Four-edge path + 8 leaves | UNSAT | 7 | 1 | 1 | 6.2 | 197.2 | 177.4 |
| Two parallel three-edge paths | UNSAT | 5 | 1 | 1 | 3.0 | 44.2 | 40.7 |
| Seeded graph #17 | UNSAT | 3 | 1 | 1 | 3.2 | 92.6 | 83.3 |

On the eight-leaf UNSAT case, all certified deductions cut DPLL
source-clause scans from **307 to 59**, but made total runtime over
30 times larger (6.2 → 197.2 µs). Selected deductions required
104 RUP(⊕) scans versus 240 for the full set, but were still far
slower end-to-end than the plain source solver.

**A separate search-relevance witness:** on the SAT case with eight
leaves, weighted deletion retains the same target affine intersection,
but the all-certified strategy finishes in one DPLL node while the
selected strategy takes ten. Thus *target-intersection preservation
does not guarantee preservation of DPLL search behavior*. The reason
includes the different added clauses and hence different variable
degrees. This finite observation is not a general complexity claim.

### Held-out stress gate

The benchmark then tested sixteen deterministic, not previously tuned
seeded 9-edge guarded parity graphs, seeds **100–115**, each under the
contradictory units `x=1, y=1`. These are intentionally small UNSAT
synthetic controls, **not independent industrial benchmarks**. On every
case all variants proved UNSAT:

| Metric | All certified | Selected certified |
| --- | ---: | ---: |
| Faster end-to-end than plain | **0/16** | **0/16** |
| Mean per-instance runtime ratio / plain | **28.92× slower** | **26.33× slower** |

The ratios are averages of per-case median ratios, not aggregate
wall-clock speedups. They can move with hardware and measurement
conditions. The qualitative failure is very large on these instances.

## What this rules out, and what it does not

**Falsified here:** The WU-008 proof-work reduction alone translates
to an end-to-end gain for short, one-shot runs of these small CNFs.
Even a reduction in DPLL nodes from seven to one does not rescue the
expensive staging process. It would be misleading to claim Witnora
became a faster SAT solver based on proof-scan counts.

**Not ruled out:** Large native-XNF conflicts, low-cost incremental
parity-module updates, repeated assumption queries reusing certified
lemmas, proof lemmas learned during CDCL (rather than precomputed),
and genuinely hard benchmarks on which parity propagation dominates
search. Those require a different experimental setup and an optimized
reference solver; they are not demonstrated wins.

**Next proposed test WU-010:** Make the same preprocessing reusable
across *many distinct SAT queries* on the same formula. Measure an
actual break-even query count, plus the cost of updating constraints,
and compare against strong existing XOR module implementations. If no
repeat-use regime wins with the full cost included, stop developing
this static selection strategy and seek a cheaper online feature.

## Reproduction

`rust/witnora-ve/src/bin/wu009_search_integration.rs`
reuses narrow WU-008 helpers. The implementation has 4 tests of its own
plus the included WU-008 / WU-006 tests; a full-crate check is required.

```sh
cd rust/witnora-ve
cargo test --release --bin wu009_search_integration
cargo run --release --quiet --bin wu009_search_integration
cargo test --release --all-targets --quiet
```
