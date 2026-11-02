# PR119 n16 literal ASCII source-subset G5 Lean scale

- Exact CI run [#41505288687](https://github.com/joeyst8/witnora-core/actions/runs/41505288687), Lean 4.19. **PASSED** universal source-subset theorem build and complete generated literal ASCII source / source-clause inclusion / G5 contradiction proof at **16 vertices**.
- Input: `make_case(16, seed=307, noise_per_vertex=2, odd=True)`; cubic Tseitin 24 edge variables + one fresh noise guard, 96 source clauses (64 parity-encoding + 32 guarded noise); this is a concrete UNSAT source with non-affine clauses.
- The generated complete Lean source is preserved as `research/PR119_NOISY_TSEITIN_N16_ASCII_G5.lean`, 46408 UTF-16 code units in JS rendering (ASCII input; check exact bytes in file). Lean compiled the complete proposition under a **180-second** hard shell limit.
- Independent full-document parse proof plus exact subset clause membership and contradiction inference were all checked for this concrete instance; the theorem is already universal over source CNFs.
- **No claim yet** that 32, 64, 96 or 128-vertex instances are kernel checked. Python-to-Lean refinement remains separate. Any large benchmark timing that excludes kernel check is labelled NOT_LEAN_VERIFIED.

Next scaling gate: n32 with 240-second hard limit; if it times out, treat as scaling blocker, not a math failure.
