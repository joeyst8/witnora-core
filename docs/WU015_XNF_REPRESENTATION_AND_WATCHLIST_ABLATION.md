# WU-015 — Xorcle representation cost versus search behavior

**Status:** two independent 8-input controlled ablations completed (80 native
solver calls); **no new algorithmic acceleration demonstrated**.

## Motivation and prior art

WU-014 found that the published Xorcle native 2-XNF implementation sometimes
times out on newly seeded dense random 2-XNF even where the independently
built CryptoMiniSat CNF-XOR pipeline gives checked answers. That observation
does not contradict Beame–Sun's results on their *selected* suites and does
not establish a broad solver ranking. We need to identify a concrete,
measurable mechanism before proposing a novel Witnora transformation.

Source: Beame and Sun, *Extending CDCL to Disjunctions of Parity Equations*,
SAT 2026, <https://doi.org/10.4230/LIPIcs.SAT.2026.5>. All five flags below
are **existing published Xorcle options**. No option is a Witnora discovery.

## Fixed experimental design

- Xorcle source pinned at `af93ea646a4237958e9925bc684dcd545e68de30`
  and the release executable built in WU-014; no changes to solver source.
- Generated dense-support 2-XNF from the WU-014 Rust generator; `3n` 2-lineral
  clauses, random nonempty parity supports, planted/unplanted balance.
- Calibration: first eight easy WU-014 inputs, `n=21,22`, base `910002`.
- Fresh replication: **eight new, previously unseen seeds** generated with
  base `910015`, again `n=21,22`, two seeds per family per size. The
  replication manifest is committed for regeneration, SHA256
  `fc21d3db10ae065035e0eea3bb0023fb97a57f95e9801bbabb9078a68b9ee756`.
- Five Xorcle command configurations on every instance, single serial run
  each, **3.5s wall-clock budget** each. Command order rotates between
  instances to reduce fixed-order bias; this is not randomized multi-run
  variance analysis. Right-censor timed-out cases.
- Every reported SAT model validated independently against original XNF
  clauses. UNSAT statuses in the per-run CSVs are *not* universally proof
  checked; one newly seeded n21 UNSAT case was additionally proven and
  independently checked (below).
- Capture Xorcle's existing `c Conflicts`, `c Propagations`,
  `c Attempted propagations`, `c Watch updates`, and decision counters from
  normal completed-run output. A timeout provides no end-of-run counters;
  never treat those values as zero.

Commands tested (baseline options are the program's defaults):

| Name | Xorcle override |
| --- | --- |
| `default` | none (dense, cyclic, compaction on) |
| `watchlist` | `--selection=leading_term_watchlist` |
| `sparse` | `--equation-repr=sparse` |
| `sparse_watchlist` | sparse + leading-term watchlist |
| `no_compaction` | `--compact=false` |

## Observed outcomes

| Config | Calibration solved / 8 | Fresh replicate solved / 8 | Total solved / 16 |
| --- | ---: | ---: | ---: |
| Default dense | 8 | 8 | **16** |
| Leading-term watchlist dense | 8 | 8 | **16** |
| Dense, no compaction | 8 | 8 | **16** |
| Sparse | 5 | 4 | **9** |
| Sparse + watchlist | 5 | 6 | **11** |

Unsolved trials were **timeouts**, not proof of unsatisfiability or errors.
All 40 solver records in each corpus passed the harness status validation;
all returned SAT models were checked against the original input clauses.

The best way to compare speed is to pair the **same instance**, avoiding
non-comparable means over different timeout-surviving subsets:

| Comparison | Completed paired instances | Geometric wall-time ratio | Identical conflict + attempted-propagation counters |
| --- | ---: | ---: | ---: |
| Watchlist dense / default dense | 16 | 0.998× | 0 / 16 |
| Dense without compaction / default dense | 16 | 1.312× | 2 / 16 |
| Sparse / default dense | 9 | **4.797×** | **9 / 9** |
| Sparse+watchlist / dense watchlist | 11 | **4.248×** | **11 / 11** |

The sparse-vs-dense pairs have exactly matching **conflict** and **attempted
propagation** counts on *every one of their 20 jointly completed trials*.
The observed penalty is therefore **consistent with representation cost,
not more work in those two counters**. Equality of aggregates does not
prove the entire branching sequence was identical, and the paired ratios
exclude timeouts, so neither result is a population-wide speed ratio.

One raw example, new-seed-independent calibration input unplanted n21
seed `90195223218`: default dense ran in `0.406s` with `1,917`
conflicts and `2,212,873` attempted propagations; sparse took `1.968s`
with the **same two counts**. Its `14,118` successful propagations imply
~157 clause-propagation attempts per successful propagation. The official
counter increments when a clause reaches `unit_propagate_one_clause` and
does **not** measure wall time per call. Non-propagating attempts can be
necessary watch checks; this statistic is not a measurement of removable
redundancy.

On one fresh replication input, unplanted n21 seed `90195223231`, native
Xorcle `--compact=false --proof=/tmp/wu015_holdout_21.lrup` generated an
UNSAT proof. The independently run upstream checker
`tools/check_lrup_parity.py` accepted it:
`OK: lines=1942 learned=1942 deletions=0 clauses_final=2005`.
This is a **single** certified UNSAT validation, not a claim that all WU-015
UNSAT records were certified.

## Interpretation and falsification gate

1. On this **dense** random parity family, swapping to the published sparse
   representation alone is not promising: fewer instances finish, and
   matched searches take substantially longer at the same attempt/conflict
   counts. That is an empirical **negative control**, not a general theorem
   about sparse XOR or other input distributions.
2. Published watchlist selection performs near parity with the default in
   aggregate in this small calibration and replication; it does *not*
   establish a speedup. Removing compaction raises paired runtime here.
3. The unresolved issue is why ~millions of clause-propagator calls arise
   when ~thousands of propagations succeed. A new proposal must first show,
   under instrumentation, how many such calls are required and where CPU
   time goes. Simple counters are insufficient to attribute a bottleneck.
4. **WU-016 gate:** take an *instrumented build of the pinned source* (clearly
   separate from untouched baseline), measure CPU distribution in
   `unit_propagate_one_clause`, GF(2) reductions, selector bookkeeping, and
   compaction. Only then specify a mathematically sound, certificate-friendly
   attempt-elision or incremental state-change mechanism. Compare any such
   mechanism against default and the existing watchlist on **new held-out
   seeds**, including true proof generation/checking costs. Reject it if
   there is no end-to-end verified improvement.

## Reproduce

From Witnora root, with the original WU-014 generator and pinned published
Xorcle binary available:

```sh
rust/witnora-ve/target/release/wu014_generate_xnf \
  /tmp/wu015-heldout 21 22 2 910015

python3 scripts/wu015_xorcle_ablation.py \
  --instances /tmp/wu015-heldout --xorcle /path/to/xorcle \
  --results /tmp/wu015-heldout.csv --max-cases 8 --timeout 3.5

python3 -m unittest -v scripts/test_wu015_xorcle_ablation.py
```

Complete solver results and the replication manifest live under
`research_data/wu015/`; the eight input formulas are deterministically
regenerable. This study does not imply P=NP, universal SAT speedup, a new
complexity lower bound, or a new proof system.
