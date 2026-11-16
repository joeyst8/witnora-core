# HV-005 — Partitioning versus FRAIG on real circuit-equivalence workloads

Date: 2026-11-10. Status: **important negative result for a prospective new
Witnora mechanism**. Known ABC automatic output partitioning is sufficient
to solve the previously resistant RISC benchmark in about 4–5 seconds.
No Witnora solver or new proof method was implemented.

## Question

HV-003 and HV-004 established five public combinational optimized-circuit
equivalence tasks. RISC took approximately 30.51 seconds in native ABC CEC
without automatic partitioning, while generic Kissat and CaDiCaL were both
UNKNOWN at 30 seconds on the derived miter CNF. Does the difficulty persist
when we ablate established **FRAIG/SAT sweeping** and **multi-output
partitioning** rather than proposing novel parity inference?

**Preexisting method firewall.** ABC's own `cec -h` documents:

- `-p`: automatic partitioning (default off);
- `-s`: toggle SAT-only versus FRAIG+SAT (default FRAIG+SAT);
- `-C`: SAT conflict limit (default 10,000);
- `-T`: *approximate* runtime limit (default 20 seconds);
- `-n`: match primary input/output interfaces by order instead of name.

These methods **are not Witnora inventions**. The earlier literature includes
Mishchenko, Chatterjee and Brayton, *Improvements to Combinational
Equivalence Checking*, ICCAD 2006,
https://people.eecs.berkeley.edu/~alanmi/publications/2006/iccad06_cec;
ABC's established SAT sweeping/FRAIG framework,
https://www-cad.eecs.berkeley.edu/~alanmi/abc/abc.htm; and the later 2026
paper *Miter-Aware LUT Mapping*, https://arxiv.org/abs/2607.07164.

## Exact setup

- Hardware source: `lsils/sim-LSV_exp` reference and optimized AIG pairs,
  commit `071c4a9998eb5660c8f955c29e905315bdad2da2`. Both circuits of
  each pair have identical positional I/O and no latches. Exact source and
  normalized file hashes: `research/results/hv003_published_circuit_miters.json`.
- ABC: `berkeley-abc/abc` revision
  `25d4ee221b2a9ab5124f3a222bcdf6f922d3d8a3`.
- RISC primary experiment: `abc -c 'cec -n -T 35 REF OPT'` versus
  `abc -c 'cec -n -p -T 35 REF OPT'`, with a 50-second outer guard. Two
  consecutive independent reruns of each mode, on the same shared host.
- SAT-only isolation: `cec -n -s -C 1000000 -T 25 REF OPT`
  (unpartitioned; outer kill guard 32 seconds) versus
  `cec -n -p -s -C 1000000 -T 30 REF OPT` (partitioned; outer guard 40s).
  Distinguish **no answer by outer guard** from UNSAT/proven equivalent.
- Four other hardware pairs: `cec -n -p -T 35 REF OPT`, each once, with a
  40-second outer guard. Compare only informally with HV-003 default CEC
  reported times; process wall and tool self-reported times differ.
- Every completed native ABC trial reported **`Networks are equivalent`**.
  This is source-circuit checking by ABC, but **no independent external
  proof** was produced. Earlier independent DRAT checks certify the CNF
  equivalents of AES/PCI/DES/USB, **not RISC**.

## Main result: RISC 2 × 2 ablation

The first two rows have two timed reruns; the SAT-only rows are additional
single diagnostic trials. All elapsed times below are approximate measured
outer process wall seconds (not isolated benchmark timings).

| Built-in ABC mode | Automatic partitioning | FRAIG stage | Outcome | Elapsed wall seconds |
| --- | --- | --- | --- | ---: |
| Default CEC, repetition 1 | no | on | **Equivalent** | 26.52 |
| Default CEC, repetition 2 | no | on | **Equivalent** | 27.68 |
| `-p`, repetition 1 | yes, 31 parts | on | **Equivalent** | 4.85 |
| `-p`, repetition 2 | yes, 31 parts | on | **Equivalent** | 4.41 |
| `-s -C 1000000`, unpartitioned | no | off, SAT only | **No conclusive answer captured** before 32-second outer guard | at least 30, at most 32 |
| `-p -s -C 1000000` | yes, 31 parts | off, SAT only | **Equivalent** | 4.70 |

An earlier separate 31-part run finished in ~5.30 seconds, also equivalent.
Default `cec` had separately reported 30.51 seconds in HV-003. Comparing the
paired exploratory reruns, built-in partitioning took approximately **one
sixth** the time of unpartitioned FRAIG+SAT. *This is an existing ABC option,
not a new Witnora speedup.*

The SAT-only unpartitioned mode with the default 10,000-conflict cap returned
`Networks are undecided (SAT solver timed out)`, sometimes well before the
wall-clock limit. We explicitly raised `-C` for the main SAT-only isolation;
otherwise one can mistakenly confuse conflict exhaustion with elapsed time.
The unpartitioned raised-cap RISC run lacked a conclusive terminal result
before its external guard and was *not* classified as proof of inequivalence.

**Causal interpretation limited to this configuration:** the 31-way
partitioned SAT-only run proved RISC without FRAIG. This establishes that
ABC's automatic output decomposition alone can remove the observed
RISC bottleneck under the tested parameters. It does **not** establish
that partitioning is universally superior, optimal, or novel.

## Counterexamples to universal partitioning benefit

The same `-p` switch on four additional source pairs yielded:

| Hardware | Unpartitioned ABC CEC reported s in HV-003 | Partitioned ABC wall s in HV-005 | Partitions | CEC outcome |
| --- | ---: | ---: | ---: | --- |
| DES | 0.43 | 0.71 | 1 | Equivalent |
| USB | 2.62 | 1.05 | 8 | Equivalent |
| AES | 4.41 | 4.99 | 2 | Equivalent |
| PCI | 3.48 | 2.28 | 16 | Equivalent |

Not all instances benefit: DES and AES were modestly slower under this
comparison; USB and PCI were faster. These are single-run comparisons with
different timing sources, not a statistical effect size.

### SAT-only controls (without partitioning)

- AES with `-s -C 1000000 -T 20`: **Equivalent after SAT** in ~14.97
  process wall seconds, compared with ~4.41 reported ABC FRAIG+SAT seconds.
- PCI with identical SAT-only options: no conclusive answer before the
  28-second external guard (exit 124).
- RISC with a 25-second approximate `-T` and 1,000,000-conflict cap: no
  conclusive answer captured before its 32-second external guard. The tool
  call did not retain a final exit code, so record **guarded inconclusive**.

These controls establish that disabling FRAIG can matter on unpartitioned
networks, while partitioned RISC solved with FRAIG disabled. They do not
separate all possible internal heuristics or certify an exact runtime gain.

## Scientific conclusion and next gate

HV-005 is a scientifically useful **negative discovery** about our prior
hypothesis: the apparent RISC SAT bottleneck is substantially relieved by
an existing automatic output partitioner; no new Witnora mathematics is
required to explain this example.

The **next** predeclared research question is therefore narrower:

> After established ABC FRAIG + output partitioning and modern CDCL,
> can any source-checkable *cross-partition* interaction measure identify
> cases where existing partitions lose essential functional relations,
> and can a genuinely distinct sound method reduce **proof-inclusive**
> time on unseen real hardware designs?

Before attempting that, compare with prior output-cone partitioning,
adaptive SAT sweeping, miter-aware LUT mapping and certificate composition.
Do not build a new implementation that merely turns on `-p` or reimplements
FRAIG. The three frozen holdouts (`tv80`, `spi`, `systemcaes`) remain
**unrun and unused for tuning** at the close of this experiment.

**No original algorithm, independent certificate for RISC, full RTL-level
industrial certification, or complexity-theory breakthrough is claimed.**
