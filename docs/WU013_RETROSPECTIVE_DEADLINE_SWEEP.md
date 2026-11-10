# WU-013 — deadline sensitivity of apparent random XNF hardness cliff

**Status:** completed *retrospective* diagnostic on an independently published
solver timing corpus; no solver was rerun. We cannot infer behavior beyond the
original 180-second censoring limit.

## Question

WU-012 observed that, at the original **180-second** limit, jointly unsolved
unplanted random 2-XNF problems jump from 0/20 at `n=33` to 16/20 at `n=34`
and 20/20 at all `n=35..40`. Is the apparent boundary stable when the
available computational time changes?

This is a necessary falsification check before treating the observed step as
anything more fundamental than a fixed-budget measurement effect. It is not
evidence for or against polynomial-time SAT or an XNF lower bound.

## Peer-reviewed context and source integrity

The native-XNF solver Xorcle and its LRUP(⊕) proof logging are described in
Beame & Sun, *Extending CDCL to Disjunctions of Parity Equations* (SAT 2026),
<https://doi.org/10.4230/LIPIcs.SAT.2026.5>. Published independent runtime
data are from Mate Soos' <https://msoos.github.io/xnf-tests/>.

The exporter validates, by SHA-256:

- `msoos/xnf-tests` commit `0a65a2cffce0587a105ceba942d993ec3ba94fe3`,
  `data.sqlite`: `0b2ea5305e1cd72453ac757dcbee1555919201454f0105db6d588e24307d9e31`.
- `j-danner/2xnf_sat_solving` commit
  `d31f12e0d15dfdb95663c53f4fbc2993e2ffa01b`,
  `benchmark/rand/rand.zip`:
  `65bf5f6312e9a3fda39c64a58cc3fd1898540fa9f15c4733fc629a8530fc628a`;
  `benchmark/rand/rand_sat.zip`:
  `b3dbeaecd148645e55f24f4619c25796a531bfd0c341b2f9d3d14d14a829ae2e`.

The source ZIPs supply original XNF headers for variable count `n`; the
independent SQLite supplies each solver's original time and timeout. The
read-only exporter matches by exact `(family, instance)` key; Rust rejects
duplicate keys, inconsistent headers/limits, missing solved timings, and
any departure from 20 instances at each `n=21..40` in each family.

## Method

For each published run, and for replay budget `T` within the original
180-second deadline, consider it solved iff **the original run solved and
its observed time was at most T**. Original failures remain unsolved at all
shorter budgets. This permits a strictly descriptive replay on
`T ∈ {1,3,10,30,60,120,180}` seconds. It **does not** create new timings,
re-sample runtime noise, or establish outcomes for `T>180`.

Define `jointly_unsolved(T) = !cms_solved_by(T) && !xorcle_solved_by(T)`.
For each family, the reported boundary is the **first** `n` with at least
10/20 jointly unsolved instances. This is a fixed descriptive threshold,
not an estimated asymptotic singularity.

## Results: the observed boundary moves with the time limit

| Replayed T (s) | First n with >=10/20 joint failures: unplanted | First n with >=10/20 joint failures: planted | Joint failures across 400 unplanted | Joint failures across 400 planted |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 28 | 29 | 265 | 218 |
| 3 | 29 | 32 | 236 | 181 |
| 10 | 31 | 32 | 200 | 153 |
| 30 | 32 | 34 | 175 | 121 |
| 60 | 33 | 36 | 156 | 96 |
| 120 | 34 | 37 | 142 | 76 |
| 180 | 34 | 37 | 136 | 68 |

The unplanted median joint-timeout boundary shifts by **six variables**
between 1 and 180 seconds. The planted boundary shifts by **eight**.
Consequently, treating the earlier n≈34 step as an intrinsic formula-size
phase transition would be unsound. There is a steep *finite-budget solver
performance* transition, but it depends strongly on the deadline.

## Complementarity check, all 400 instances per family

| T (s) | Unplanted CMS / Xorcle / union solved | Planted CMS / Xorcle / union solved |
| ---: | --- | --- |
| 1 | 135 / 40 / 135 | 180 / 72 / 182 |
| 3 | 164 / 60 / 164 | 218 / 90 / 219 |
| 10 | 200 / 80 / 200 | 246 / 115 / 247 |
| 30 | 225 / 120 / 225 | 279 / 144 / 279 |
| 60 | 244 / 120 / 244 | 304 / 156 / 304 |
| 120 | 258 / 140 / 258 | 324 / 167 / 324 |
| 180 | 264 / 140 / 264 | 332 / 172 / 332 |

At T=180, **Xorcle contributes no uniquely solved instance in either random
family**: the union coverage equals improved CryptoMiniSat's coverage.
At short budgets, planted cases offer 1–2 Xorcle-only faster solves; those
advantages disappear by T=30. This is true only of these source families
and time budgets, not of all XNF problems: WU-011 found the opposite
winning regime for Ascon r3 instances.

## Reproduce

```sh
python3 scripts/wu013_export_deadline_xnf.py \
  /path/to/xnf-tests/data.sqlite \
  /path/to/2xnf_sat_solving/benchmark/rand/rand.zip \
  /path/to/2xnf_sat_solving/benchmark/rand/rand_sat.zip \
  | cargo run --release --manifest-path rust/witnora-ve/Cargo.toml --bin wu013_deadline_censoring

cargo test --release --manifest-path rust/witnora-ve/Cargo.toml --bin wu013_deadline_censoring
cargo test --release --manifest-path rust/witnora-ve/Cargo.toml --all-targets
```

The Rust binary additionally reports the full family-by-n table for every
budget, so every aggregation can be independently checked. No upstream
dataset or zip is committed into Witnora.

## What remains genuinely unknown

This experiment cannot resolve whether the n≈34–40 performance transition
reflects a solver-specific exponential scaling regime, interactions with
planted-vs-unsat generation, or a property of the particular sampled seeds.
To advance beyond retrospective diagnostics, WU-014 should:

1. Reproduce generation from upstream code where available, pin new seeds,
   and release independently generated n=30..43 formulas. Match the
   original XNF clause/lineral distribution and record how planted instances
   were constructed; do not compare unmatched distributions casually.
2. Execute at least two independent original solvers under fixed compute
   budgets of 30, 180 and >180 seconds on the new corpus, repeat timing
   where possible, and validate SAT models / UNSAT proofs.
3. Measure actual end-to-end wall time, solver-specific success sets and
   certificate overhead. A proposed Witnora method only graduates to a
   solver feature if it wins out-of-sample after all costs and verification.

No proof of a mathematical phase transition, general SAT speedup, or
structural explanation has been established.
