# HV-006 — Predeclared ten-circuit partition-overhead screening

Date: 2026-11-10. Classification: **reproducible known-method regression
identified in published hardware designs; no new Witnora algorithm or
scientific breakthrough**.

## Preregistered design and provenance

The ten pairs and all 20 source SHA-256 hashes were frozen and committed
**before** solving in `docs/HV006_PREDECLARED_DEVELOPMENT_COHORT.md`, commit
`66acf8020ddb49bd9c3cf7c1f53b156e0358163e`. The corpus is the
published `lsils/sim-LSV_exp` snapshot
`071c4a9998eb5660c8f955c29e905315bdad2da2`. It contains processed
IWLS'05 logic designs, not evidence of a manufactured-chip tapeout.

Reference `benchmarks_ifraig-s/NAME.aig` and further-optimized
`benchmarks_dc2syn2/NAME.aig` pairs all have **matching positional inputs
and outputs and zero latches**. These are combinational equivalence
checks, not unbounded sequential safety checks. The three frozen HV-003
holdouts `tv80`, `spi`, `systemcaes` were **not tested**; the five earlier
pilot designs were also excluded.

Pinned ABC `berkeley-abc/abc` revision
`25d4ee221b2a9ab5124f3a222bcdf6f922d3d8a3` built with
`make ABC_USE_NO_READLINE=1 -j4`. Each predeclared pair was run sequentially
once with **both** `cec -n -C 10000 -T 9 REF OPT` and
`cec -n -p -C 10000 -T 9 REF OPT`, each guarded by
`timeout -k 1s 14s`. `-p` is **ABC's existing automatic partitioner**;
`-C 10000` fixes the default conflict limit. ABC's `-T` is approximate,
and measured external process wall time includes startup and I/O.

The reported statuses are the *actual ABC native conclusions*. Both
UNDECIDED and hard cutoff are censored, not design inequivalence. No
external ABC-to-DRAT proof was produced for these additional source pairs.

## Predeclared ten-pair outcomes

Each value is a **single measured run** on a shared, non-isolated machine;
times are not statistically controlled. The ABC PART column's integer is
the number of partition verification tasks reported by ABC.

| Design | Unpartitioned ABC status / wall s | Partitioned ABC status / wall s | PART count | Observation |
| --- | --- | --- | ---: | --- |
| `iwls05_i2c` | equivalent / 0.28 | equivalent / 0.25 | 1 | indistinguishable at this scale |
| `ss_pcm` | equivalent / 0.23 | equivalent / 0.23 | 1 | control |
| `systemcdes` | equivalent / 0.39 | equivalent / 0.40 | 1 | control |
| `ac97_ctrl` | equivalent / 1.06 | equivalent / 0.49 | 9 | partition favorable |
| `DMA` | equivalent / 4.10 | equivalent / 1.94 | 16 | partition favorable |
| `DSP` | equivalent / 8.93 | equivalent / 12.80 | 101 | **partition unfavorable** |
| `des_perf` | equivalent / 10.15 | equivalent / 4.95 | 18 | partition favorable |
| `wb_conmax` | equivalent / 3.08 | equivalent / 1.93 | 14 | partition favorable |
| `ethernet` | equivalent / 3.66 | equivalent / 1.44 | 41 | partition favorable |
| `vga_lcd` | **external cutoff / 14.20** (exit 124) | equivalent / 4.24 | 70 | partition made verification finish |

This is **10/10 correct native ABC equivalence conclusions with
partitioning**, versus **9/10 with default unpartitioned settings within
the external guard**; the 10th is censored rather than wrong. It is not a
Witnora speedup. The small and nonrandom development cohort cannot support
broad solver-ranking claims.

### Post-screen DSP replication

After identifying DSP as a slowdown, we performed an explicitly
**post-hoc diagnostic replication** in alternating run order, unchanged
inputs and settings, to check that the adverse result was not a one-off.
The initial screening values are included in the summary statistics:

| Mode | Initial + three additional process-wall times (s) | Median (s) |
| --- | --- | ---: |
| Unpartitioned | 8.93, 9.90, 9.38, 9.04 | **9.21** |
| Partitioned (101 parts) | 12.80, 12.83, 12.69, 13.34 | **12.815** |

All eight runs returned **equivalent**. In this exploratory group,
partitioning was approximately **39% slower** by the median-ratio metric.
The runs were sequential and unisolated, so this is consistency evidence,
not a formal statistical confidence interval.

## A structural diagnostic, not a new theory

We reran the existing **ABC** partitioning mode to collect each
`Verifying part ... PI ... And ... Lev` report. The *sum of the reported
per-part AND counts* is compared with the sum of archived reference and
candidate AIG AND-gate counts. The ratio is a **rough aggregate workload
indicator**: ABC internally transforms logic, and this is **not** a formal
count of uniquely duplicated gates or proof of exact shared-cone overlap.

| Design | Source reference+candidate ANDs | Sum of ABC partition ANDs | Ratio | Number of parts |
| --- | ---: | ---: | ---: | ---: |
| `iwls05_i2c` | 1,988 | 2,307 | 1.16 | 1 |
| `ss_pcm` | 802 | 829 | 1.03 | 1 |
| `systemcdes` | 5,443 | 5,938 | 1.09 | 1 |
| `ac97_ctrl` | 24,948 | 31,332 | 1.26 | 9 |
| `DMA` | 42,919 | 60,256 | 1.40 | 16 |
| `DSP` | 83,404 | **514,432** | **6.17** | 101 |
| `des_perf` | 163,301 | 159,044 | 0.97 | 18 |
| `wb_conmax` | 86,685 | 94,737 | 1.09 | 14 |
| `ethernet` | 142,125 | 194,879 | 1.37 | 41 |
| `vga_lcd` | 215,213 | 329,392 | 1.53 | 70 |

**Interpretation:** On this small development sample, the one circuit
with a sustained partition slowdown (DSP) also showed dramatically
greater *aggregate per-part workload* relative to original size. This is
an observed association, **not** a validation of a predictive metric.
Simple output count or number of partitions is insufficient: 70 parts
helped VGA while 101 hurt DSP. We did not pre-register this ratio, and it
was inspected *after* the DSP regression was identified. The diagnostic
is **exploratory/hypothesis-generating**, not a holdout success.

## Prior-art firewall

These ideas are well established, not alien mathematics or original
Witnora discoveries:

- Mukherjee et al., *Automatic partitioning for efficient combinational
  verification*, ASP-DAC 2000,
  https://doi.org/10.1109/ASPDAC.2000.835072: automates partitioning and
  uses heuristics for a computationally hard partition-selection problem.
- Zheng et al., *Efficient Equivalence Checking Using Output Grouping and
  Circuit SAT Solver*, 2005,
  https://www.jcad.cn/en/article/id/617833e4-d478-4357-a82d-cb09b8d505fa:
  output grouping and reuse of learned information are known.
- *Combinational Equivalence Checking Using Incremental SAT Solving,
  Output Ordering, and Resets*, ASP-DAC 2007,
  https://www.cecs.uci.edu/~papers/aspdac07/pdf/p938_9C-3.pdf:
  explicitly analyzes overlaps between SAT problems due to shared logic.
- Mishchenko et al., *Improvements to Combinational Equivalence Checking*,
  ICCAD 2006, https://doi.org/10.1145/1233501.1233679; and Zhu et al.,
  *Miter-Aware LUT Mapping*, 2026, https://arxiv.org/abs/2607.07164.

**Research decision:** do not patent, publish, or claim as new merely
using output-grouping, overlap, or ABC's existing `-p` switch. The ratio
above is not a previously unknown mathematical invariant. Before
implementing any new Rust solver pass, identify what existing overlap-
aware partition heuristics fail to capture and prove a difference on a
predeclared unseen development cohort, with independently checked
certificates. Do not spend the three frozen holdouts merely tuning a
known partition threshold.

## Boundary

HV-006 found a **reproducible engineering weakness of one built-in ABC
mode on one public design**, and a suggestive diagnostic. It did not
establish an absolute algorithmic breakthrough, a novel optimality
criterion, an independently certified RISC proof, or full-chip RTL safety.
