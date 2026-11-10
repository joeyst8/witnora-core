# HV-001 — Certified chip-equivalence benchmark entry

Status: **baseline screening performed; no Witnora speedup demonstrated**.
Date: 2026-11-10. This is an empirical research record, not an RTL
verification product or a mathematical breakthrough.

## The application and exact claim

For combinational circuits with aligned inputs and outputs, define the miter

`M(x) = OR_i(C_reference_i(x) XOR C_candidate_i(x))`.

`SAT(M)` produces a distinguishing input; `UNSAT(M)` establishes combinational
equivalence under the assumptions used to construct the miter. The CNF encoding
and its interpretation must be independently audited before treating it as a
claim about source RTL. In particular, a combinational equivalence result on
normalized HWMCC transition circuits is **not** by itself an unbounded
sequential safety proof.

The **real-world target** is checking whether optimized hardware retains the
function of a reference design, and finding a counterexample when it does not.

## Public corpus and controls

1. Primary benchmark: *CNF Encoded Isomorphic and Optimized Miters from
   Hardware Model Checking Competition 2024 Models* (Biere, Fazekas, Fleury,
   Froleyks, 2025), https://doi.org/10.5281/zenodo.15207209. It includes
   318 original HWMCC'24 models, with combinational isomorphic and optimized
   miter encodings. The complete archive is 3.0 GB; do not present its raw
   file count as evidence of difficulty.
2. Staged source: `Tractables/cnfs`, commit
   `de4731f68e5a5bb6629269b3be1d19b44e812763`, `hwmcc/` collection.
   This repository documents its HWMCC collection as CC BY 4.0 and identifies
   the upstream Zenodo dataset. We selected six individual `.cnf.xz` files
   via a sparse checkout instead of downloading the complete corpus.
   **Provenance limitation:** its `process_zip_cnf` importer flattens source
   paths to basenames and skips subsequent duplicate names. Therefore the
   flattened staged files do **not** identify whether they came from the
   upstream `iso` or `opt` directory. Treat this screening set as
   *variant-unknown* and retrieve exact upstream `opt` and `iso` paths before
   making a difficulty or performance claim.
3. Independent controls: compare optimized versus isomorphic miters when the
   source provenance can be recovered. Keep known-equivalent UNSAT instances
   distinct from deliberately mutated *non-equivalent* SAT circuits. A bug
   witness must be simulated against the actual reference and candidate
   circuits, not merely accepted by a SAT exit code.

## Initial baseline — six hardware-derived miters

Baseline: Kissat 4.0.4, source commit
`8af8e56f174b778aef3aa45af9f739b2a5f492c2`, built with default
`./configure; make -C build -j4`. Each file was run using
`kissat --time=30 -n FILE.cnf.xz`; reported process-time is from the solver,
not a controlled, isolated hardware benchmark. Values are preliminary and
should not be used to claim a statistically significant performance delta.

| Hardware-derived file | Vars | Clauses | Kissat result | Process s | Conflicts / decisions | Independent DRAT |
| --- | ---: | ---: | --- | ---: | ---: | --- |
| `ILA_AES_START_ENCRYPT_problem` | 12,554 | 38,299 | UNSAT | 0.04 | 0 / 0 | VERIFIED |
| `picorv32-check-p09` | 22,020 | 72,911 | UNSAT | 0.07 | 0 / 0 | VERIFIED |
| `VexRiscv-regch0-20-p1` | 20,612 | 67,744 | UNSAT | 0.05 | 0 / 0 | VERIFIED |
| `ILA_Piccolo_BEQ_sanity` | 111,195 | 355,366 | UNSAT | 0.26 | 0 / 0 | not run |
| `ILA_Ridecore_XOR_sanity` | 467,972 | 1,589,284 | UNSAT | 1.76 | 0 / 0 | not run |
| `ILA_Flute_XORI_sanity` | 1,293,848 | 4,238,108 | UNSAT | 6.81 | 0 / 0 | not run |

The independent checker used `marijnheule/drat-trim` commit
`2e3b2dc0ecf938addbd779d42877b6ed69d9a985` compiled with
`gcc -D_GNU_SOURCE drat-trim.c -std=c99 -O2 -o drat-trim` (the repository's
default `make` failed on `getc_unlocked` under this environment's C99
declarations). For the first three cases, Kissat was rerun with a proof output
argument, the `.cnf.xz` input was decompressed, and `drat-trim CNF PROOF`
returned **`s VERIFIED`**. The verifier reported 0.143, 0.226, and 0.237
seconds respectively. Full input/proof digests are in
`research/results/hv001_chip_miter_baseline.json`; raw proofs are not checked
into the repository.

**Interpretation:** Kissat's congruence/preprocessing already proves these
six miters without search. They serve as correctness and regression controls,
**not** a useful performance success story for a new parity method. We have
not run a Witnora implementation on these inputs and have no measured Witnora
advantage.

## Research hypothesis that remains open

On *hard optimized* equivalence miters, can a **source-checkable,
proof-preserving XOR-aware partition or inference step** reduce total
time-to-verified-answer, including its extraction/encoding/verification cost,
relative to well-tuned modern CDCL and circuit-aware verification baselines?

This hypothesis must be distinguished from existing research on clausal
congruence closure and miter-aware mapping, including the 2026 paper
*Miter-Aware LUT Mapping: Aligning Structure and Solvability for Efficient Logic
Equivalence Checking*, https://arxiv.org/abs/2607.07164. Neither XOR extraction
nor Gaussian-guided XOR modeling is presumed novel.

## Next admissions and stop conditions

1. Recover clearly labeled **optimized** HWMCC miter CNFs, plus their
   isomorphic controls. Select a frozen development set by documented
   instance hashes and a disjoint holdout. Preserve source and tool versions.
2. Run default Kissat and CaDiCaL (and applicable circuit-aware EQY/ABC
   baselines for the *same verification task*) under identical time/memory
   constraints; capture preprocessing, proof-checking time, and RAM. Do not
   compare combinational miter timings against sequential IC3 results as if
   they solved the same property.
3. Profile XOR-equivalent gate patterns *after* strong baseline
   preprocessing. A zero-conflict instance is a regression control. Only
   pursue a structural hypothesis where measurable nontrivial work remains.
4. Build the substantive Witnora path in **Rust**. Require exact source
   semantics, independent SAT counterexample checking or independently
   checked UNSAT proof, and fail-closed unsupported modes. Charge all
   preprocessing and certificate work to elapsed time.
5. Predeclare success: correctness on every accepted case, reproducible
   improvements in verified solved count or PAR-2 on **unseen optimized
   miters**, and a controlled ablation explaining the improvement. Otherwise
   record a negative result and move on.

## Boundary

No result here establishes a new SAT algorithm, a practical speedup,
equivalence of the original RTL without checking the CNF translation, full
sequential hardware safety, or implications for `P` versus `NP`.
