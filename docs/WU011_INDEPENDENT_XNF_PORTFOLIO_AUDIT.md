# WU-011 — An external XNF benchmark reveals a round-dependent solver reversal

**Status:** exploratory analysis of *published per-instance solver runs*;
independent source files inspected; 5-fold retrospective selection gate
implemented in Rust. **No new SAT algorithm, no new solver execution,
no new proof-system result, and no Witnora solver speedup.**

## Sources, exact snapshot and validity boundary

Primary data: Mate Soos's publicly posted
[XNF solver evaluation](https://msoos.github.io/xnf-tests/), generated
September 13, 2026. Its repository is
[`msoos/xnf-tests`](https://github.com/msoos/xnf-tests), pinned here to
commit `0a65a2cffce0587a105ceba942d993ec3ba94fe3`.

Dataset: `data.sqlite`, SHA-256
`0b2ea5305e1cd72453ac757dcbee1555919201454f0105db6d588e24307d9e31`.
It holds **7,530 recorded solver runs** across **1,695 distinct instances**
in 13 benchmark families. The primary website reports per-family
numbers and describes the versions, configurations, input encodings,
timeout (180 s), hardware (AMD EPYC 7763), resource limits (15 GB),
SAT model checking, and UNSAT proof checking.

Establishment of the method is **not novel**: Beame and Sun,
*Extending CDCL to Disjunctions of Parity Equations*, SAT 2026,
[DOI 10.4230/LIPIcs.SAT.2026.5](https://doi.org/10.4230/LIPIcs.SAT.2026.5),
introduced Xorcle and LRUP(⊕). The source benchmark compares Xorcle
with CryptoMiniSat, Xorricane and Bosphorus, adjusting CryptoMiniSat's
Gaussian limits and including newer revisions. We do not construe a
published solver-runtime replay as new original SAT performance data.

## Research question: does the family total hide opposite winners?

WU-009/010 found that expensive *static* proof-lemma selection on
synthetic CNF lost even when DPLL scans fell. WU-011 stops generalizing
from that small prototype and asks whether existing optimized solvers
already dominate in **different identifiable structural regimes**.
If so, a potential future system must target the shared hard residue,
not merely replicate a known XOR inference or claim parity is ignored.

The `2xnf-ascon` family has 400 instances from Ascon-128, grouped by
the **number of rounds**. We paired exactly one `cms-improved` record
with one `xorcle` record by `(family, instance)`, never by filename
ordering or runtime. Both solvers' SAT/UNSAT statuses agree on every
jointly solved pair. The published benchmark provides these fields
and the *pre-solve* directory suffix `r2`, `r3` or `r4`.

### Matched outcomes by Ascon rounds

| Rounds | Instances | Improved CryptoMiniSat solved | Xorcle solved | CMS-only | Xorcle-only | Neither |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 20 | 20 | 20 | 0 | 0 | 0 |
| **3** | 200 | 122 | **189** | 0 | **67** | 11 |
| **4** | 180 | **176** | 77 | **99** | 0 | 4 |

The round-three and round-four *coverage relationships actually
reverse*: all 122 round-three cases solved by improved CMS are also
solved by Xorcle; all 77 round-four cases solved by Xorcle are also
solved by improved CMS. This is a **finite observation on one public
benchmark**, not a claim about all Ascon formulas or solver generations.

PAR2 treats an unsolved run as twice its 180-second timeout. Source
SQLite computation reproduces the published global PAR2 values:

| Solver | Solved overall | Overall PAR2 (s) | Round-3 PAR2 (s) | Round-4 PAR2 (s) |
| --- | ---: | ---: | ---: | ---: |
| Improved CryptoMiniSat | 1,314/1,695 | 92.565 | 159.770 | **30.176** |
| Xorcle | 919/1,695 | 173.717 | **26.535** | 235.206 |

The unconditional whole-family ranking obscures the regime reversal.

## An executable *retrospective portfolio* falsification

The selector is explicitly cheap: read the publicly assigned benchmark
family and, only for `2xnf-ascon`, the existing Ascon round count. No
runtime feature, solved label, graph-wide SAT inference or formula
assignment search enters its decision.

We evaluated these **counterfactual routing policies** using the
already recorded solver runtimes:

1. **CMS always:** use `cms-improved` on all 1,695 instances.
2. **Xorcle always:** use `xorcle` on all 1,695.
3. **Post-hoc round-3 rule:** choose Xorcle for `2xnf-ascon/r3`, and CMS
   otherwise. This was *discovered after looking at the data*.
4. **Family-only five-fold selector:** FNV-1a hash `(family,instance)`
   to a fixed fold `0..4`; train the lowest training PAR2 solver per
   family on the other four folds and evaluate on the fifth.
5. **Family-plus-round five-fold selector:** identical procedure, except
   `2xnf-ascon/r2`, `/r3` and `/r4` are separate training strata.
6. **Unattainable per-instance oracle:** given the future outcome, always
   select the lower-PAR2 record; this is an optimistic upper bound on
   the value of routing only these *two* solvers, not a real algorithm.

| Offline evaluation | Solved | PAR2 (s) | Xorcle-selected instances |
| --- | ---: | ---: | ---: |
| Improved CryptoMiniSat always | 1,314 | 92.565221 | 0 |
| Xorcle always | 919 | 173.716879 | 1,695 |
| Post-hoc 3-round rule | **1,381** | **76.844271** | 200 |
| 5-fold, family only (round feature removed) | 1,314 | 92.519740 | 40 |
| 5-fold, family + Ascon rounds | **1,381** | **76.798791** | 240 |
| *Hindsight* oracle (not deployable) | 1,382 | 76.597304 | 365 |

On this corpus, the five-fold round-aware gate gains 67 solved
instances versus always using improved CMS, or **3.95 percentage
points** of the 1,695-instance benchmark; its reported retrospective
PAR2 improves about **17.0%**. It is only one solve short of the
two-solver hindsight coverage ceiling; the other uniquely Xorcle-solved
instance occurs in the unrelated `ascon` family.

**The ablation matters:** removing just the Ascon-round feature from
the otherwise identical per-family CV removes all 67 added solved
cases. The simple round split is a valuable empirical discriminator
in *this* benchmark; “globally apply parity processing” is a poor
description of the data.

### Selection bias / what has not been established

The round feature and the family choice were noticed by examining the
**full dataset**, including future fold members. Five-fold evaluation
separates each fold's *fitted winner* from its test rows, but **does
not undo this exploratory feature-selection leakage**. There is no
newly generated Ascon corpus or independent prospective validation.
Therefore **do not** market 1,381/1,695 as a new independently
replicated result, a measured portfolio executable, or a generalizable
deployment guarantee. It is a reproducible **retrospective replay** of
one public benchmark. The solver binaries, encodings and platform are
also those chosen by its original maintainer; relative performance
may change on another revision, encoding or hardware.

## Hard intersection: where new science could matter

An optimistic two-solver oracle covers **1,382/1,695**, leaving
**313 benchmark instances** that neither improved CMS nor Xorcle
solved within 180 seconds. Of these, **204** belong to the two
random-2-XNF families (136 in mixed `2xnf-rand`; 68 in guaranteed
satisfiable `2xnf-rand_sat`). Those alone constitute **65.2%** of
the shared unsolved residue.

**Priority for WU-012:** study the *313 jointly unsolved instances*,
especially these 204 random-2-XNF cases, using source features that
are actually cheap to compute: variable-to-lineral incidence, small
GF(2) rank profiles, and observed per-instance solver activity where
published logs permit it. Ask whether a certified, non-exponential
feature predicts **additional solved instances or time savings beyond
both existing solvers**. Create a truly independent benchmark split
before any claim of generalization. Do not relabel existing Gaussian
closure, size thresholds, or family metadata as a new SAT theorem.

## Exact code and reproduction

The data are intentionally **not copied** into Witnora's repository;
fetch the pinned upstream source. The small Python bridge performs
only read-only SQLite extraction and schema checks; the substantive
ranking, five-fold training and censoring-aware scoring are Rust.

- `scripts/wu011_export_xnf_portfolio.py` — joins external benchmark
  records, checks 1,695 paired keys, writes tab-separated data to stdout.
- `rust/witnora-ve/src/bin/wu011_xnf_portfolio.rs` — checks status
  disagreements, duplicate IDs, malformed timeouts and Ascon strata;
  computes overlaps, PAR2, fold-independent routing and oracle limits.

```sh
git clone https://github.com/msoos/xnf-tests.git
cd xnf-tests
git switch --detach 0a65a2cffce0587a105ceba942d993ec3ba94fe3
sha256sum data.sqlite

cd /path/to/witnora-core/rust/witnora-ve
cargo test --release --bin wu011_xnf_portfolio
python3 ../../scripts/wu011_export_xnf_portfolio.py /path/to/xnf-tests/data.sqlite \
  | cargo run --release --quiet --bin wu011_xnf_portfolio
cargo test --release --all-targets --quiet
```

The three tests in the Rust binary cover correct schema parsing and
round routing, rejection of malformed/contradictory records, and
determinism of the hash-fold selector. The original benchmark remains
the authority for how the solver runs were made.
