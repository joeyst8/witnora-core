# PR #119 — Noisy Tseitin Source-Subset G5 Prototype

Run: https://github.com/joeyst8/witnora-core/actions/runs/41502688735
Code: `scripts/experiment_noisy_tseitin_source_subset.py`
Universal soundness proof: `formal/Witnora/SourceSubsetG5.lean`
Raw measurements: `research/PR119_NOISY_TSEITIN_SUBSET_RESULT.json`

## Formal milestone

A generic Lean 4 theorem proves that if every clause of an extracted subset is present in the original source, and a kernel-checked G5 contradiction proof passes for that subset, the full original CNF is UNSAT. The CI job compiled this theorem and checked a **concrete source CNF with non-affine guarded noise** and its extracted G5 trace. This is a sound clause-monotonicity bridge, not a novel mathematical result. It does not universally refine all of Python or parse arbitrary original DIMACS source text into Lean.

## Falsification results (development cases)

Cubic graph generator: Hamiltonian cycle plus a disjoint random perfect matching. Each vertex imposes a 3-variable XOR. A single odd parity charge makes the XOR subsystem inconsistent. Noise clauses add a fresh *positive guard literal* to otherwise random literals; setting this guard true makes the noise satisfiable, preserving equivalence to the core.

The generator uses graph sizes 16, 32 and 48, seeds 11 and 29, and 0 or 2 guarded noise clauses per vertex (12 UNSAT cases). MiniSat22 and CaDiCaL195 receive the exact same full normalized source CNF, with bounded worker time.

- Native exact-source-subset/G5 UNSAT candidates: **12/12**.
- Independent MiniSat UNSAT: **12/12**; CaDiCaL UNSAT: **12/12**.
- Timeouts: **0** for either solver.
- Satisfiable consistency control and one-clause-deleted XOR encoding: **both SAT** by MiniSat, **both diagnostic-only** in the subset G5 pipeline.
- Native end-to-end proof pipeline beats MiniSat worker time in **4/12** cases and CaDiCaL in **2/12** cases.

| Vertices | Native G5+subset median (ms) | MiniSat worker median (ms) | CaDiCaL worker median (ms) |
| --- | ---: | ---: | ---: |
| 16 | 7.02 | 0.32 | 0.38 |
| 32 | 26.68 | 9.66 | 4.41 |
| 48 | **34.60** | 119.14 | 36.30 |

These are **four samples per graph size**, not a statistically robust speed ranking. Native pipeline timing includes XOR extraction, certificate construction and independent Python check, but **not Lean kernel proof generation/compilation**. Solver worker timing includes solver startup and solve inside the subprocess, excluding interprocess launch time. Full proof-producing comparisons would need a comparable proof checker on the baseline. The Lean instance here is a small smoke test and cannot be extrapolated to all 12 instances.

## Prior art / status

Tseitin CNFs, Gaussian elimination for XOR, and the general source-subset implication are established. CryptoMiniSat implements Gaussian elimination as part of SAT solving, so comparing only to MiniSat/CaDiCaL cannot establish algorithmic novelty or world-changing performance.

**Decision:** Retain the verified source-subset bridge in the draft as a valid proof-composition component. Treat the 48-vertex timing signal as a *hypothesis only*. Pre-register fresh, larger, structurally distinct holdout graphs, add robust solver baselines (especially XOR-aware CryptoMiniSat if available), and charge full proof-generation plus kernel-check costs before proposing publication.
