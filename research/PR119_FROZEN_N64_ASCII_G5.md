# PR119: frozen noisy Tseitin n64, original ASCII DIMACS -> Lean-checked UNSAT

**Status: KERNEL-CHECKED CONCRETE SOURCE UNSAT PROOF.** CI [#41506306283](https://github.com/joeyst8/witnora-core/actions/runs/41506306283) and job `125486396391` completed successfully on 2026-11-02.

## Exact tested case

- Original frozen holdout key: `vertices=64, seed=47, noise_per_vertex=1, odd=True`.
- Original frozen source hash: `0eec2fad66e671abfa9c03901c05295adc3923f4cb1c2030afb85f87354c3d9d`. The Python proof generator **checks this hash before generating** any Lean proof.
- 97 variables: 96 cubic-graph edge variables and one positive noise guard. 320 source clauses: 256 exact XOR-encoding clauses plus 64 guarded non-affine clauses.
- Source bytes are explicit ASCII DIMACS, with independent document/token-stream and canonicalization checks in the Lean theorem.
- Every clause used in the source-subset contradiction is checked to occur in the original canonical source. The extracted G5 row operations form a checked contradiction, yielding `¬ ∃ a, signedCNFHolds raw a`.
- Full generated Lean proposition is archived verbatim in `research/PR119_FROZEN_N64_ASCII_G5.lean` (164648 characters).

## Timed kernel verification

On the same successful CI run, time between start and completion of the `lake env lean` proof step:

| Vertices | CI proof-step wall time | Status |
|---:|---:|---|
| 16 | 19 s | success |
| 32 | 67 s | success |
| **64** | **210 s** | **success** |

These timings reflect GitHub Actions step timestamps rather than an independently calibrated benchmark. They are **not included** in the earlier native-only Witnora vs CryptoMiniSat solver wall-time comparison.

## Meaning and explicit limitations

- This is the **first exact frozen 64-vertex holdout instance upgraded to per-instance Lean verification**; remaining **11 of 12** held-out cases still have only Python-native independent checks. Do not relabel historic raw dataset; link it with this new proof record instead.
- The soundness of the generic source-subset theorem is Lean-checked, and the concrete source-to-proof instantiation is kernel-checked. This does **not** prove Python-to-Lean refinement for all inputs, nor full TC-063 G14 residual/branch composition, nor SAT algorithmic novelty.
- Proving an instance UNSAT is a meaningful formal correctness milestone, but the 210-second kernel cost is not yet competitive with the native or CryptoMiniSat runtime. Further scale requires a more compact or more efficient proof-checking representation.

Related files: `formal/Witnora/SourceSubsetG5.lean`, `scripts/lean_noisy_tseitin_scale.py`, `.github/workflows/noisy-tseitin-lean-scale.yml`, frozen raw benchmark `research/PR119_NOISY_TSEITIN_FROZEN_HOLDOUT_RESULT.json`.
