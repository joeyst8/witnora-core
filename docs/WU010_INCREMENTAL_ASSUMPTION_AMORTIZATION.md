# WU-010 — Reusable certified parity deductions across distinct SAT queries

**Status:** completed controlled negative experiment with real repeated
DPLL search. Neither eager certification nor WU-008's cost-sensitive
selection wins end-to-end in the tested 1–512-query regime.

## Why this question matters

WU-009 showed strong *search-work* reductions in some cases but a large
wall-clock loss after discovery, proof checking, and CNF expansion. A
plausible escape route is to certify the parity conclusions **once**
and reuse them whenever the source formula is solved under different
assumptions. Standard incremental SAT and XOR solvers already reuse
learned information; this experiment does not claim that reuse is new.

Established context: Beame & Sun, *Extending CDCL to Disjunctions of
Parity Equations*, [SAT 2026](https://doi.org/10.4230/LIPIcs.SAT.2026.5),
present CDCL(⊕) and LRUP(⊕) in Xorcle. Laitinen, Junttila and Niemelä,
*Extending Clause Learning SAT Solvers with Complete Parity Reasoning*,
[arXiv:1207.0988](https://arxiv.org/abs/1207.0988), already integrate
incremental Gauss–Jordan parity reasoning into DPLL(XOR). WU-010
does not invent a new inference rule or a new incremental solver.

### Hypothesis

Given a formula `F` and `Q` *distinct* assumption queries `A_i`, does

`certify(F) + sum_i DPLL(F + certified + A_i)`

become faster than

`prepare_plain(F) + sum_i DPLL(F + A_i)`

for a sufficiently large tested `Q`? The two augmented alternatives
are `all` certified units plus final hyperplanes, and `selected`
proof-cost-aware deletion plus the same final hyperplanes.

## Protocol and soundness

- For each synthetic source XNF fixture, translate only local bounded
  XNF constraints into exactly equivalent CNF. Prepare and certify
  intermediate and final deductions **once per session**.
- Use 512 deterministic **unique** queries consisting of three signed
  unit assumptions on distinct variables, selected from up to 14 source
  variables. A seeded shuffle fixes a single query order for all modes.
  This is enumeration of small query variants, not enumeration of full
  Boolean assignments to decide the original SAT problem.
- Evaluate prefix counts `Q ∈ {1, 8, 32, 128, 512}` with the *same query
  bank* for plain, all-certified and selected-certified strategies.
- For each query, run a fresh instrumented DPLL on the prepared CNF
  with the additional three units. The cached parity lemmas are reused
  unchanged; the solver does **not** retain variable assignments or
  learn CDCL clauses across calls.
- All modes pay the same per-query CNF cloning and unit-insertion
  overhead. The full-session clock **includes the one-time certificate
  computation**, local XNF/CNF conversion, per-query setup, search and
  result construction. Generating the fixed query bank itself is
  outside the measurement for every strategy.
- Every selected parity unit and final hyperplane inherits WU-009's
  staged XNF RUP(⊕) certification, plus the independent Boolean CNF
  RUP cross-check in that binary. Across four fixtures × 512 queries,
  all three modes return exactly the same SAT/UNSAT answer; all 512
  queries per fixture are distinct.

This is a **repeated-solve-with-shared-preprocessing** experiment,
not a fully incremental solver with watched literals, learned-clause
retention, activation literals, or persistent CDCL state.

## Observations

One local Rust release-mode run. Each cell is the median of seven
measurement batches after three warmup sessions; shorter sessions
use more repetitions per batch. Results are microseconds for the
**complete session**, not per query.

| Formula | Queries | Plain (µs) | All certified (µs) | Selected certified (µs) | End-to-end winner |
| --- | ---: | ---: | ---: | ---: | --- |
| Four-edge path, no leaves | 1 | 1.4 | 22.4 | 23.5 | Plain |
| Four-edge path, no leaves | 128 | 110.1 | 143.7 | 156.2 | Plain |
| Four-edge path, no leaves | 512 | **431.2** | 519.7 | 522.1 | Plain |
| Four-edge path + 8 leaves | 1 | 4.6 | 211.4 | 191.0 | Plain |
| Four-edge path + 8 leaves | 128 | **333.0** | 577.5 | 559.1 | Plain |
| Four-edge path + 8 leaves | 512 | **1526.4** | 1775.5 | 1763.9 | Plain |
| Seeded graph #17 | 1 | 3.5 | 94.3 | 84.9 | Plain |
| Seeded graph #17 | 128 | **209.5** | 373.7 | 351.1 | Plain |
| Seeded graph #17 | 512 | **865.2** | 1290.8 | 1142.3 | Plain |
| Seeded graph #121 | 1 | 3.0 | 93.1 | 82.8 | Plain |
| Seeded graph #121 | 128 | **205.1** | 397.1 | 350.0 | Plain |
| Seeded graph #121 | 512 | **866.2** | 1300.3 | 1134.2 | Plain |

At the omitted tested 8- and 32-query prefixes, plain was also
fastest on all four fixtures. **No measured break-even point through
512 queries.** This does not prove that none exists for an arbitrarily
large number of queries, different query distributions, or a different
solver architecture.

### Why amortization is not enough here

Some augmented variants consistently visit fewer clauses under DPLL:

- Four-edge path + leaves, 512 queries: **221,099 plain clause scans
  versus 106,858 with all certified parity lemmas**; yet total runtime
  is **1526.4 versus 1775.5 µs**, respectively.
- Seeded graph #17, 512 queries: **146,360 plain clause scans versus
  118,699 all-certified scans**, but runtime grows from **865.2 to
  1290.8 µs**.
- The selected approach can scan *more* clauses than plain (seed #17:
  153,107 scans), despite a correct preservation of the target affine
  intersection. Its added clauses affect the chosen decision order and
  the cost of traversing each CNF clause.

These metrics expose the key methodological trap: scans are not equal
to instructions, memory traffic, or end-to-end CPU time. Adding
short CNF consequences can change decision ordering, make each
propagation pass more expensive, and incur per-query cloning costs.
The verifier and affine-selection work are still paid at least once.

## Decision and next research target

**Reject a general claim that static parity-lemma reuse is enough to
recover the WU-009 loss in this DPLL+CNF setting.** In fact, the
all-certified approach often lowers scans without lowering time;
selecting lemmas by proof relevance is not a reliable predictor of
their downstream search value. Neither observation is a broad theorem.

The next meaningful gate is to instrument **native XOR-aware CDCL with
watched propagation**, then compare an *online* parity-utility signal
against a zero-overhead baseline and established Gauss–Jordan/Xorcle
approaches on genuinely independent, difficult instances. If that
integration is not available, the honest boundary is that WU-010
contains **no demonstrated practical solver advance**.

## Reproduction

Implementation: `rust/witnora-ve/src/bin/wu010_incremental_amortization.rs`
with three narrow `pub(crate)` visibility changes in WU-009.

```sh
cd rust/witnora-ve
cargo test --release --bin wu010_incremental_amortization
cargo run --release --quiet --bin wu010_incremental_amortization
cargo test --release --all-targets --quiet
```
