# HV-002 — Nontrivial multiplier-equivalence admission

Date: 2026-11-10. Status: **benchmark admission passed; algorithmic breakthrough NOT demonstrated**.

## Why this experiment exists

HV-001 and a further **12 preselected** hardware-derived miters from the
flattened `Tractables/cnfs` HWMCC'24 collection were all resolved by Kissat
4.0.4 preprocessing with **0 decisions and 0 conflicts** (the new screening
cases required 0.04–0.21 process seconds each). The variant labeling of the
flattened collection remains ambiguous. These are regression/correctness
controls, not a challenging workload for claiming research progress. The
12 input names, SHA-256 hashes, solver results and provenance appear in
`research/results/hv002_miter_admission.json`.

We therefore constructed a *separate, explicitly synthetic* hardware-design
equivalence family in Rust. This is not an industrial chip design or a
replacement for the upstream `cnf/opt` HWMCC miters. It is a controlled
screening tool where nontrivial search and independent certificates are
observed, and its limits are recorded rather than hidden.

## Design, public prior art, and semantics

`research/hv002_multiplier_miter.rs` generates unsigned `n`-bit multiplier
CNFs. Primary inputs and individual AND partial products are shared. The
**reference** sums shifted partial-product rows through repeated ripple-carry
addition; the **candidate** reduces three rows to two via carry-save full
adders before a final ripple-carry addition. The asserted final CNF clause
requires **at least one output bit to differ**. Therefore:

- **UNSAT** proves the two *encoded combinational* circuits agree on all
  shared primary inputs, subject to the correctness of the CNF construction.
- **SAT** provides a distinguishable input for the intentionally faulty
  `stuck-zero` mode, in which the candidate's `a[0] & b[0]` partial-product
  gate is forced to zero (a realistic stuck-at-zero gate fault).

An arithmetic invariant provides an independent specification: ripple add
preserves the sum of its operands modulo `2^(2n)`; 3:2 carry save preserves
`A+B+C = sum + (shifted_carry)` modulo `2^(2n)` for each bit. Thus both
implement the same sum of shifted rows, namely `a*b`, for equivalent mode.
The invariant itself is elementary and **not novel**.

**Prior-art firewall:** Järvisalo, *Equivalence checking hardware multiplier
designs* (SAT Competition 2007), already tests different multiplier
architectures as UNSAT CNFs:
https://www.cs.helsinki.fi/u/mjarvisa/papers/jarvisalo.sat07benchmarks.pdf.
Our generated family is *different in topology and deliberately small*,
but not a new problem class or algorithm. Structural congruence closure,
XOR extraction, and SAT sweeping are also established (Biere et al., SAT
2024, https://doi.org/10.4230/LIPIcs.SAT.2024.6). Do not market this as
novel SAT mathematics or as an independent industrial holdout.

## Admission results (single exploratory runs)

Kissat 4.0.4 at `8af8e56f174b778aef3aa45af9f739b2a5f492c2`;
Rust 1.99.1 (2026-10-13). Timings are rough solver-reported process times,
not isolated repetitions. `UNKNOWN` means **resource cutoff**, not SAT or
UNSAT. Formal statuses are separate from performance evidence.

| Width | Vars | Clauses | Default Kissat | Conflicts | Decisions | Process / cutoff | DRAT independent check |
| ---: | ---: | ---: | --- | ---: | ---: | --- | --- |
| 2 | 22 | 60 | UNSAT | 0 | 0 | <0.01 s | not run |
| 3 | 67 | 205 | UNSAT | 51 | 53 | <0.01 s | not run |
| 4 | 134 | 424 | UNSAT | 292 | 470 | 0.02 s | not run |
| 5 | 228 | 735 | UNSAT | 1,498 | 2,476 | 0.04 s | not run |
| 6 | 339 | 1,102 | UNSAT | 6,668 | 10,870 | 0.25 s (no proof) | **VERIFIED**; proof run 0.43 s + checker 0.255 s |
| 7 | 480 | 1,571 | UNSAT | 34,844 | 52,670 | 1.16 s (proof run) | **VERIFIED**; checker 1.457 s |
| 8 | 649 | 2,135 | UNSAT | 130,641 | 202,416 | 5.32 s (no proof); 5.49 s with proof | **VERIFIED**; checker 6.620 s |
| 9 | 820 | 2,703 | UNKNOWN | 361,420 | 585,366 | 20 s cutoff | not applicable |
| 10 | 1,035 | 3,422 | UNKNOWN | 81,709 | 168,491 | 4 s cutoff | not applicable |

Widths 8 and 10 were also `UNKNOWN` at initial 4-second cutoffs; width 8
subsequently solved at ~5.32 seconds. Do not confuse censored cutoffs with
an intrinsic complexity result.

The independent DRAT checker `marijnheule/drat-trim` commit
`2e3b2dc0ecf938addbd779d42877b6ed69d9a985` reported **`s VERIFIED`**
on original generated CNFs and Kissat proofs for widths 6, 7, and 8.
Proofs and generated CNFs were not committed; their SHA-256 identifiers
are in the JSON result record.

### Fault detection and independent witness validation

Every generated `stuck-zero` case at widths 2–8 and 10 returned SAT in
initial screening. `research/hv002_check_witness.rs` independently parses
the complete solver assignment, checks **every original DIMACS clause**, and
computes the expected product using native integer arithmetic (not the
generator's circuit). Validated witness examples:

- Width 6: `a=63`, `b=63`; reference `3969`, candidate `3968`; **1,105/1,105** clauses satisfied.
- Width 8: `a=255`, `b=255`; reference `65025`, candidate `65024`; **2,138/2,138** clauses satisfied.

This is an intentionally easy-to-detect fault, **not** evidence of a strong
bug-finding algorithm. It proves the SAT path and an independent
primary-input/original-clause witness check are functioning.

### Known-method ablation, not a Witnora win

The same equivalence CNFs, with the existing Kissat switches:

| Width | Default conflicts | `--congruence=false` conflicts | `--congruencexors=false` conflicts |
| ---: | ---: | ---: | ---: |
| 6 | 6,668 | 8,480 | 6,510 |
| 7 | 34,844 | 31,047 | 32,855 |
| 8 | 130,641 | 124,945 | 127,492 |

This shows that even removing the **already published** XOR/congruence
preprocessing can reduce conflicts on these encodings. Conflicts are not
total verified wall-time or a hardware performance win. Strong future
baselines must include ablations and multiple seeds/runs where applicable.

## Reproduction

```sh
rustc --edition=2021 -O research/hv002_multiplier_miter.rs -o /tmp/hv002-gen
rustc --edition=2021 -O research/hv002_check_witness.rs -o /tmp/hv002-check
/tmp/hv002-gen --width 8 --mode equivalent --out /tmp/hv002-8.cnf
kissat --time=30 -n /tmp/hv002-8.cnf /tmp/hv002-8.drat
drat-trim /tmp/hv002-8.cnf /tmp/hv002-8.drat
/tmp/hv002-gen --width 8 --mode stuck-zero --out /tmp/hv002-bug.cnf
kissat /tmp/hv002-bug.cnf > /tmp/hv002-bug-model.txt
/tmp/hv002-check /tmp/hv002-bug.cnf /tmp/hv002-bug-model.txt
```

`kissat` normally returns status code 20 for UNSAT and 10 for SAT. Those
are not command failures. The `--time` flags set the solver's seconds limit.

## Scientifically honest next gate

1. Retrieve **labeled** optimized (`cnf/opt`) and isomorphic (`cnf/iso`)
   production-derived miter pairs from the upstream dataset; benchmark the
   *same* logical verification task. Our synthetic multiplier instances
   only establish that the harness can exercise nontrivial search.
2. Freeze widths **12, 14, 16** as *synthetic holdout* before proposing or
   tuning a Witnora solver change; they remain unrun here. A separate
   industrial holdout remains mandatory.
3. Profile retained XOR/ITE or interaction features *after* strong existing
   preprocessing on admitted hard cases. Candidate hypothesis: a
   cost-sensitive **residual** feature can choose parity inference with
   a favorable *proof-inclusive* total cost. No implementation or novel
   mathematical result has yet been established.
4. If feature matches known SAT sweeping, Gauss elimination, gate congruence,
   or LUT mapping, mark it **replication**. An advancement requires
   independently checked equivalence/bug witnesses and a controlled,
   meaningful unseen-case advantage, not anecdotal shorter solve times.

There is no Witnora-versus-Kissat speedup claim in HV-002.
