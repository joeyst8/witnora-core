# HV-004 — Independent SAT-solver and proof-inclusive circuit benchmark

Date: 2026-11-10. Status: **known-method baseline strengthened; no Witnora
algorithm or breakthrough established**. This extends HV-003 on the *same*
five public optimized-circuit miter CNFs, without opening the three frozen
holdouts `tv80`, `spi`, or `systemcaes`.

## Question and novelty firewall

Does the apparent difficulty of the published hardware miters survive a
second state-of-the-art generic CDCL SAT solver, with independently verified
UNSAT evidence? In HV-003, Kissat 4.0.4 stopped at 10 seconds on AES, PCI,
and RISC, whereas ABC native combinational equivalence checking proved all
five source-AIG pairs. **An unexplained solver timeout is not a research gap.**

CaDiCaL is a published preexisting CDCL solver, not Witnora; its use here is
strictly a baseline. Prior literature also already covers clausal congruence
closure, XOR handling, SAT sweeping, miter-aware structural mapping and
circuit-native SAT. We made no implementation change to those algorithms.

## Reproducibility and limits

- Exact miter CNF SHA-256 hashes and hardware source lineage are pinned in
  `research/results/hv003_published_circuit_miters.json`; all cases are
  combinational AIG pairs from `lsils/sim-LSV_exp` at commit
  `071c4a9998eb5660c8f955c29e905315bdad2da2`.
- CaDiCaL **3.0.1**, official repository `arminbiere/cadical`, revision
  `c60730422e758ef1cebe7aeddf2dda31c996bf04`, built with default
  `./configure && make -j4`; binary SHA-256
  `5f83c321328714cc35d0dcecd8ad86d28d4b849a76c1a1308b5e9ef55feecb4e`.
  Standard command: `cadical -t 10 -n FILE.cnf`, protected by a 14-second
  external process kill as a guard. CaDiCaL `-t` is an internal wall-clock
  time limit; the wrapper and startup may add time. Exit 20 means UNSAT;
  exit 0 with no SAT/UNSAT answer means unknown at timeout.
- Source-to-CNF translation is the same AIGER pipeline pinned in HV-003.
- Single preliminary runs on a shared, non-isolated host. Do **not** infer a
  statistically significant runtime or winner ranking from these seconds.
- All UNSAT claims below are about the generated CNFs. ABC separately checked
  equivalence at the AIG level; the toolchain is not formally verified.

### 10-second generic SAT baseline comparison

| Circuit | Kissat 10-second status; conflicts (HV-003) | CaDiCaL 10-second status | CaDiCaL conflicts / decisions | CaDiCaL reported real seconds |
| --- | --- | --- | ---: | ---: |
| DES | UNSAT; 265,696 | **UNSAT** | 232,723 / 698,555 | 6.33 |
| USB | UNSAT; 59,451 | **UNSAT** | 35,969 / 1,063,930 | 2.15 |
| AES | UNKNOWN; 129,984 | **UNSAT** | 138,415 / 776,879 | 8.64 |
| PCI | UNKNOWN; 494,178 | **UNSAT** | 412,183 / 7,287,985 | 7.00 |
| RISC | UNKNOWN; 25,664 | **UNKNOWN** | 34,715 / 8,968,481 | 10.00 cutoff |

This shows a second standard solver handled AES and PCI at the 10-second
cutoff. Importantly, generic solver conflict counts and variable-elimination
statistics depend on engine internals; comparing counts between solvers is
not a like-for-like complexity measure.

### Kissat 20-second cutoff sensitivity test

We reran the same original default CNFs under **Kissat 4.0.4** with
`--time=20 -n`, without any algorithm, encoding, or parameter tuning:

| Circuit | Result at 20-second cutoff | Conflicts | Decisions | Reported process seconds |
| --- | --- | ---: | ---: | ---: |
| AES | **UNSAT** | 189,703 | 1,692,967 | 13.41 |
| PCI | **UNSAT** | 638,780 | 4,474,615 | 9.16 |
| RISC | UNKNOWN | 96,729 | 16,199,662 | 20.00 cutoff |

PCI resolving in about 9.16 seconds even though the earlier 10-second run
was UNKNOWN illustrates uncontrolled timing and run-to-run variation. For AES
the longer 20-second budget changes UNKNOWN to UNSAT. These are **not**
contradictions and cannot support a stable solver speedup percentage.

### RISC 30-second generic-solver sensitivity gate

The same pinned RISC CNF was then run with `cadical -t 30 -n` and
`kissat --time=30 -n`, each under a separate 39-second external kill guard.
Neither reached a SAT/UNSAT answer:

| Solver | Result | Conflicts | Decisions | Reported duration |
| --- | --- | ---: | ---: | ---: |
| CaDiCaL 3.0.1 | UNKNOWN, cutoff | 231,682 | 23,097,630 | 30.00 real s |
| Kissat 4.0.4 | UNKNOWN, cutoff | 284,993 | 22,122,510 | 30.01 process s |

ABC's separate circuit-level CEC of the *AIG pair* was equivalent at 30.51
reported seconds under an approximate internal time limit. That is not a
certified equal-resource race; it does show **RISC remains a legitimate
stress case for these default generic CNF settings even with a longer
cutoff**, rather than merely a ten-second threshold artifact.

### Independent UNSAT certificates for two new solved cases

We repeated CaDiCaL with an explicit **ASCII DRAT** proof stream
(`cadical -t 20 --binary=false -n FILE.cnf PROOF.drat`) and passed that
file plus the *unaltered original miter CNF* to
`marijnheule/drat-trim` at pinned revision
`2e3b2dc0ecf938addbd779d42877b6ed69d9a985`. Both returned
**`s VERIFIED`** (exit 0):

| Circuit | Proof-run solver seconds | DRAT checker seconds | Total solver + checker | Original CNF SHA-256 | Proof SHA-256 |
| --- | ---: | ---: | ---: | --- | --- |
| AES | 8.85 | 5.412 | ~14.26 s | `24771e66a765e2ef0c67f06b317556cff3191b16db878dea18486fe4cb594fc0` | `dd1fc6732d245a63a0652faf9e926dfa1cf0ce55d28d2531692dc819e538bd73` |
| PCI | 7.30 | 5.298 | ~12.60 s | `caeba6d7f9c0e802ce2f5bece7b985e5880e1d29bc47dd333cbf0ac01e57f638` | `08472a8244745f4e826b442721a49ad47dba2870a5da00c579b5f0a7253dd2f7` |

The approximate sums exclude CNF generation, process setup and input
loading in the checker; they are **not** complete end-to-end workflow times.
Raw proof files (approximately 31 MB for AES and 81 MB for PCI) are
reproducible but intentionally not committed. HV-003 also independently
verified DES and USB using Kissat DRAT. RISC has **no CNF UNSAT certificate**
from this stage, even though native ABC CEC reported equivalent.

## What this tells Witnora

1. AES and PCI at a 10-second cutoff were **solver-specific unresolved
   cases**, not a demonstrated fundamental limitation or new research gap.
2. RISC remains a *candidate* stress case for generic CNF SAT at 30 seconds;
   ABC CEC already proved its source pair in approximately 30.51 seconds
   using a different native verification method and an approximate internal
   timeout. No one has shown a Witnora algorithm beating this.
3. A proof-producing solver's raw SAT-search time can substantially
   understate certified verification cost. The independent checker alone
   added approximately 5.3-5.4 seconds on AES and PCI.
4. **Next falsifiable hypothesis:** can a Rust preprocessing method detect
   *residual cross-design functional constraints after established ABC/Kissat/
   CaDiCaL simplification* that make the RISC-like cases hard, and generate a
   separately checkable proof or witness while improving total verified
   elapsed time? Its nearest predecessors are SAT sweeping, circuit-native
   incremental SAT and miter-aware LUT mapping. A source-level distinct
   operation and same-task proof-inclusive speedup on frozen holdouts are
   required before any novelty claim.

No new algorithm, new theorem, industrial full-chip certification, or
P-versus-NP result follows from HV-004. This is an **adversarial baseline
finding** that prevents a misleading claimed breakthrough.
