# HV-009 — Predeclared word-level array pilot (before execution)

**Protocol freeze date:** 2026-11-10. **Status at this commit:** selected tasks **NOT YET RUN**. This record must precede any checker run on the selected tasks. These are **development admission cases**, not generalization holdouts and not a claim of Witnora novelty.

## Goal and stop condition

Can the existing public Cerbtora 2.0.0 + Bitwuzla 0.6.1 *independently accept* a simple witness consisting of the original stateful, array-bearing chip design itself for two published HWMCC'24-related BTOR2 files? This tests whether the **original safety property is already 1-inductive**, not whether a new solver can discover an invariant. Failure to accept means **not 1-inductive under this proposed witness or another checker issue**, **not** that the design is unsafe. UNKNOWN/timeout must remain UNKNOWN.

If the original as witness is rejected for both, **do not rewrite tasks or change thresholds** to obtain a pass. Record the failure and move to established certifying witness production from the literature. No proposal of new heuristic follows from a toy/one-pass result.

## Pinned provenance

Corpus: https://gitlab.com/sosy-lab/research/data/word-level-hwmc-benchmarks/ at Git commit `e19d110544fe7481763894f479b223aaa95fa582`; public `array/btor2/hku-array/` subgroup from HWMCC 2024 / HKU circuit designs; two task metadata files both specify `expected_verdict: true`, property `unreach-call.prp`. These expected labels are **source metadata**, not independently established here. Per-source task licenses apply. Original BTOR2 headers attribute Yosys conversion and https://doi.org/10.5281/zenodo.14156844.

**Predeclared pair, no additions after runs:**

| Task | Size (bytes) | SHA-256 |
| --- | ---: | --- |
| `processed_hl_arr_access_32_arr.btor2` | 12369 | `93fb87c152dc8b7fc3e709f1d56a6ab1178ac782340a1b84b86ee69f8fa40c49` |
| `processed_hl_arr_access_128_arr.btor2` | 13083 | `e1576463aa86a252d947d110f2daf6b54417c2cb3a7c4dfb871fe9ac5b33861b` |

Checker: https://github.com/Froleyks/cerbtora commit `983a21c440f8e4f25b1e8be8bd759332fee21e88`, binary version 2.0.0. BTOR2 parser dependency `hwmcc/btor2tools` checkout `e6941e37e056084ab6e51c5c1eee6233089a330d`. SMT backend: https://github.com/bitwuzla/bitwuzla commit `9bb73b69611d85fd04c20b3bd72f6dbe9bd9dc43`, binary version 0.6.1. This build uses bundled CaDiCaL 1.7.4 fallback. Build configured `-DTOOLS=ON -DSTATIC=OFF -DCMAKE_BUILD_TYPE=Release` with locally installed CMake 3.31.6, Meson 1.8.2, Ninja 1.11.1.4 and compiler GCC 14.2.0.

## Frozen pilot procedure

1. Reject input file if its SHA-256 differs. Keep originals unchanged.
2. For each of two files, run exactly one positive/negative admission attempt: `TIME=20 SPACE=2048 <cerbtora-install>/bin/check <original.btor2> <same original.btor2>`; the second argument is an intentionally **weak, putative witness** (property as its own invariant), not a known correct certificate. The official Cerbtora CLI emits five SAT obligations; its pass proves 1-inductiveness under source assumptions; its fail is **not a refutation of safety**.
3. Capture process exit code, each named obligation status, elapsed wall time if available, tool versions, and full source identity. Use stdout/stderr to distinguish a successful witness, failed induction, parser/runtime error and guard termination. Do not conflate incomplete checks with UNSAT.
4. Run a known-positive external tool-chain control first: published `examples/model.btor2` with `examples/witness.btor2` should return valid; known negative `model.btor2` used as witness must be rejected. These existing HV-008 fixtures do not count as cohort outcomes.
5. If the first attempt returns valid, recheck with `SEQUENTIAL=true` as a workflow sanity control; if rejected, record why and do not secretly tune.
6. No timing, SOTA or novelty claim from two intentionally nonrandom examples; these are research admission controls only. No algorithm tuning on the older frozen `tv80`, `spi`, `systemcaes` holdouts.

## Next admission step after this pilot

Find or reproduce an established **certificate-producing** BTOR2 model checker, ideally the 2026 published k-induction prototype or a cross-tool witness from a public artifact. Only then predeclare nontrivial solved-set and total **solve + certificate emission + independent checking** benchmarks (including unmodified array semantics), preserve a separate final holdout and do a new prior-art novelty audit.
