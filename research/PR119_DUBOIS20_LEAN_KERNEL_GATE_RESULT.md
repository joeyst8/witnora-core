# PR #119: Dubois20 has a kernel-checked indexed XOR refutation of the embedded CNF

Date: 2026-11-02. Status: **PASSED for the explicit Lean formula; source-text refinement remains open**.

## Actual checked claim

`theory/Dubois20SourceUnsat.lean` defines a concrete 160-clause Boolean
formula `Witnora.Dubois20.sourceCNF : BitVec 60 → Prop`. Original DIMACS
variable `i` is represented by `bits.getLsbD (i-1)`; negative literals use
Boolean negation. The file proves:

```lean
theorem source_unsat (bits : BitVec 60) : ¬ sourceCNF bits
```

The code exposes **40 four-clause source groups**, each checked equivalent
to its exact three-variable XOR row by eight finite Boolean cases.
`source_iff_certificate` assembles all 40 local equivalences for the entire
160-clause formula. `certificate_inconsistent` replays 39 small indexed XOR
operations (`traceStep40` through `traceStep78`), each justified by finite
Boolean case splits on at most five input variables. The final trace row has
an empty variable set but RHS `true`, so its asserted equality is `false = true`.

The trace is independently archived in
`research/PR119_DUBOIS20_GF2_39_STEP_TRACE.json` and references the 40
source-equation IDs in
`research/PR119_DUBOIS20_SOURCE_XOR_CERTIFICATE.json`.

| Measure | Checked value |
|---|---:|
| Embedded original signed clauses | 160 |
| Source clause-to-XOR equivalences | 40 |
| Indexed row-XOR derivation steps | 39 |
| Maximum derived row width | 4 |
| Maximum combined input variables per step | 5 |
| Last row | ID 78, empty LHS, RHS 1 |

## Actual Lean CI result and axiom boundary

- Official Lean 4 toolchain: `leanprover/lean4:v4.35.0`, pinned in `lean-toolchain`.
- Successful GitHub Actions run:
  <https://github.com/joeyst8/witnora-core/actions/runs/41486322179>
- Successful source proof commit:
  `20a0eedde2b545f6e6793aaa736706a06768fc96`.
- `lean theory/Dubois20SourceUnsat.lean`: **exit 0**.
- `#print axioms Witnora.Dubois20.source_unsat`: **`[propext]` only**.
- No `sorryAx`, `native_decide` axiom, `bv_decide` native axiom, or
  trusted solver UNSAT verdict is used to establish the theorem.

The early implementation used `bv_decide` and produced native-computation
axioms in Lean 4.35.0; that candidate was rejected for this track. A
single large AC simplification was also rejected after exceeding its proof
elaboration budget. These failed approaches remain visible in the PR history.
The *accepted* proof instead checks 39 width-at-most-four steps.

## Extra source-to-Lean correspondence regression

`tests/test_dubois_lean_bridge.py` independently checks the archived source
row truth tables and that all 160 exact signed clauses, 40 parity rows, the
entire source conjunction, and the 39 indexed trace data appear in the
concrete Lean definitions unchanged. Three tests pass offline. The isolated
CI workflow runs these three Python tests *and* the Lean compiler.

This guard is useful, but the Python regression is **not a Lean theorem**.
The archived source has decompressed DIMACS SHA-256
`82059aba0e5773644b386eb6bcbe53680655390cb041873a3cb3e93f7bd896a7`,
previously checked against the official historical archive. Lean does not
yet parse the original DIMACS byte stream, authenticate this hash, or prove
that the Python reader and emitter refine the Lean source representation.
Those remain explicit trust-boundary obligations.

## Scientific interpretation

This is a **real, limited formal-verification milestone** for Track A:
the embedded exact signed-clause refutation is checked with only the usual
Lean `propext` axiom. It is **not** a new general theorem, not a universal
indexed-certificate checker, and not the end-to-end TC-063 result.

It also does **not** reverse the prior preregistered 0/4 applicability
finding for Witnora's specialized symbolic SAT operator. The 39-step
short proof is a checkable certificate result, not a solver speedup.

The next correctness gate is a verified original-DIMACS text parser plus
signed-literal serialization refinement: the parsed clause list must equal
what `sourceCNF` denotes. After that, generalize the 39-step construction
into a reusable indexed-XOR trace checker whose soundness is proved once.

Reproduce:

```sh
python -m unittest tests.test_dubois_lean_bridge -v
lean theory/Dubois20SourceUnsat.lean
```
