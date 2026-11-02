# PR119 n32 original ASCII source-subset G5 Lean check

CI [#41505705633](https://github.com/joeyst8/witnora-core/actions/runs/41505705633) **PASSED** both n16 and n32 real literal source-to-G5 Lean checks. All propositions were compiled from generated file by `lake env lean`; there is no unverified Python UNSAT assumption used in the Lean proof.

- n32 configuration: `make_case(32, seed=307, noise_per_vertex=2, odd=True)`, 48 edge vars + one guard, 128 exact XOR CNF clauses + 64 guarded non-affine clauses = **192 source clauses**.
- Generated n32 proof source is preserved in `research/PR119_NOISY_TSEITIN_N32_ASCII_G5.lean` (95373 source characters). The Lean workflow allowed at most 240 seconds for the complete n32 check.
- Universal source-subset G5 theorem was already verified and remains unchanged; this is per-instance source bytes, parse, clause-subset membership and contradiction verification.
- **Next:** frozen holdout n64 seed47 noise1 original source hash `0eec2fad66e671abfa9c03901c05295adc3923f4cb1c2030afb85f87354c3d9d`. A passing n64 checker would upgrade one of the 12 large native-only results to per-instance Lean acceptance. Other 11 remain native-only until checked.
- No claim of new SAT math, general speedup, or full TC-063 theorem.
