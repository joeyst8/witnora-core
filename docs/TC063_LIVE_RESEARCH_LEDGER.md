# TC-063 live research ledger

Last audited: 2026-11-03 UTC (draft PR #121, branch `formal/g14-python-seen-enqueue-v121`).

## Critical status correction: restricted-family TC-063 logical theorem IS PROVED

A source-code audit on 2026-11-03 found that the universal normalization and G5-completeness gaps listed in the previous version of this ledger had **already been closed** in imported Lean modules. The previous assessment incorrectly treated a theorem from `TC063CanonicalAffineBridge.lean` (conditional) as the project's strongest result, overlooking the subsequent unconditional restricted-family theorem in `TC063CanonicalBound.lean`. Do not re-open these obligations without a counterexample or a revised domain specification.

### Exact proved statement

`formal/Witnora/TC063CanonicalBound.lean:502`:

```lean
theorem tc063_restricted_family_unsat_iff_checked_cover
    (c r : Nat) (raw : List (List Int))
    (hFamily : Family c r raw) :
    (¬ ∃ a, Witnora.SignedSerialization.signedCNFHolds raw a) ↔
      ∃ cert : CoverData, cert.accepts c raw = true
```

For **every** `c`, `r`, and signed CNF `raw` in the explicitly defined restricted `Family c r`, source UNSAT is equivalent to an accepted finite G14/G5 branch-cover certificate. There is **no remaining assumed `AffineG5Complete r` premise** in this theorem.

Audited independent green CI: https://github.com/joeyst8/witnora-core/actions/runs/41583294191 (job `lean`, complete and successful). The `#print axioms` output for this theorem and the universal canonical-witness theorem reports **[propext, Classical.choice, Quot.sound]** only (standard Lean logical principles; no project-specific axioms or `sorry`).

### Proof closure chain

1. `TC063PatternPermutation.checkSemanticExactAffine_sortAffineRows` (line 436) proves that the actual exact affine CNF extraction checker **reaccepts every previously accepted row system** after sorting variables; the row validator already guarantees positive, duplicate-free supports.
2. `TC063CanonicalBound.checkSemanticExactAffine_boundedCanonRows` (line 363) proves acceptance is also preserved by explicit finite-bound canonicalization.
3. `TC063CanonicalBound.certifiedAffine_has_canonicalWitness` (line 467) constructs a bound, canonical rows, and covered finite variable schedule for **every** `CertifiedAffine r cnf`; the once-missing `CertifiedAffine → CanonicalAffineWitness` implication is universally proved.
4. `TC063CanonicalBound.certifiedAffine_g5_complete` (line 486) establishes `AffineG5Complete r`, discharging the earlier conditional theorem.
5. `TC063CanonicalBound.tc063_restricted_family_cover_complete` (line 494) and `tc063_restricted_family_unsat_iff_checked_cover` (line 502) compose G5 and the G14 branch model-gluing argument to produce the family-level result.

**Scope:** `Family c r raw` in `SemanticSAF.lean:101` demands an existing duplicate-free separator of length at most `c`, exhaustive conditioned branches, checker-approved exact independent residual partitions, and for each component a `CertifiedAffine r` witness accepted by `checkSemanticExactAffine`. This is a substantial, explicit **promise/restricted class**. The theorem does not establish that an arbitrary CNF belongs to this family or that constructing its witnesses is cheap. `Classical.choice` may be used for existential certificate selection; it is not a polynomial-time algorithm.

## Concrete pipeline verified so far

1. `TC063SourceVertexCuts.lean`: source primal adjacency reconstructed from signed clauses; two-cut claims checked against G14 DFS component count.
2. `TC063AsciiSourceVertexCuts.lean`: signed DIMACS token stream tied to actual source ASCII bytes through independently checked parsing and graph reconstruction.
3. `TC063AsciiCutG14Composition.lean`: sound source-CNF UNSAT composition from passed two-cut, residual partitions, and checked G5 certificates.
4. `TC063AsciiTwoCutSmoke.lean` and `fixtures/tc063_ascii_two_cut_unsat_smoke.cnf`: genuine 4-cycle two-cut synthetic fixture; x2 and ¬x2 contradiction produces concrete accepted G5 certificates. **This is a smoke test, not an original TC-063 benchmark**, structural speedup, or substantive hard instance.
5. `scripts/generate_tc063_ascii_smoke_identity_lean.py`: Lean-checks that the committed DIMACS bytes equal those used by the concrete proof.
6. `TC063CanonicalSortAudit.lean`: tiny interface audit for already-proved sorting and canonical-witness implications. `scripts/generate_python_canonical_sort_differential_lean.py`: 48 Python-generated randomized affine cases checked against Lean's source extraction and normalization before/after sorting (**passed** targeted CI https://github.com/joeyst8/witnora-core/actions/runs/41585442371; all generated extraction/sorting examples were accepted by Lean).

## 2026-11-03 operational test: nontrivial overlapping affine UNSAT

Committed `fixtures/tc063_three_row_affine_unsat.cnf`, a ten-clause DIMACS document encoding:

- `x1 ⊕ x2 ⊕ x3 = 0`
- `x2 ⊕ x3 ⊕ x4 = 0`
- `x1 ⊕ x4 = 1`

All 16 Boolean assignments were independently enumerated: each two-equation subsystem has exactly four satisfying assignments, whereas all three together have none. The contradiction requires combining three overlapping rows, not detecting opposite unit clauses.

`tests/test_lean_g5_wire_real.py` now builds a certificate through the **actual production Python extractor and GF(2) indexed-operation emitter**, verifies the original DIMACS byte document, signed tokens, decimal spellings, canonical source clauses, and G5 contradiction against the **actual Lean executable checks**, with no mocked subprocess. The targeted GitHub Actions `Production G5 numeric-wire gate unit and real Lean smoke tests` step passed on the new fixture (PR #121, workflow runs https://github.com/joeyst8/witnora-core/actions/runs/41588336876 and https://github.com/joeyst8/witnora-core/actions/runs/41588553259).

A real *negative* case holds the same certificate, clauses, token stream, and spellings but tampers with the source header from `p cnf 4 10` to `p cnf 4 9`. The test asserts `NOT_LEAN_VERIFIED` and `CNF_NORMALIZATION_REJECTED` and passed in the same real Lean test step. This detects source-document provenance corruption. The test is finite end-to-end validation, not universal Python refinement or a runtime bound.

## 2026-11-03 sparse high-ID cycle stress baseline

Added `test_sparse_cycle_long_refutations_across_large_variable_ids` to `tests/test_lean_g5_wire_real.py`. Each instance is a minimally inconsistent XOR cycle: `x_i ⊕ x_(i+1) = 0` for each adjacent pair, plus `x_1 ⊕ x_n = 1`. Each has exactly `n` two-variable equations and `2n` canonical CNF clauses; removing any equation makes it satisfiable. The test uses actual Python equation extraction, Gaussian elimination, indexed-DAG operations and the *bound-independent* `checkWireSparseG5` Lean gate. A parity-flipped SAT twin at every size must not be classified as UNSAT.

All three UNSAT certificates were **Lean-accepted** in the real CI invocation. Timings from the successful GitHub Actions log (one run, including independent Lean CNF normalization and numeric-wire verification; not a warmed performance benchmark):

| Cycle equations / variables | Max variable ID | CNF clauses | Indexed XOR operations | Python certificate generation | Full Lean gate |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 8 | 8 | 16 | 8 | 1.1 ms | 1,269.2 ms |
| 16 | 1,048,592 | 32 | 16 | 1.5 ms | 2,853.6 ms |
| 32 | 16,777,248 | 64 | 32 | 2.8 ms | 9,584.0 ms |

Green job: https://github.com/joeyst8/witnora-core/actions/runs/41593864870 (the `lean` job, including the real Lean tests). The test does **not** show linear gate scaling: as row count increases 4×, this cold CI sample's gate time increases ~7.6×. It does show the checker can handle sparse IDs over 16 million without allocating a dense ID array. To make a statistical speed claim, repeat timings, benchmark against external SAT solvers, and separate startup, CNF normalization, operation decoding, and sparse contradiction-checking costs.

## What remains open (separate from the restricted logical theorem)

- **Full CPython refinement**: no universal proof that every execution of Python parsing, normalization, extraction, separator selection, G5 emission, and serialized DIMACS/certificate operations exactly refines the verified Lean meanings. Finite differential testing and narrow operation bridges do not establish this.
- **Efficient constructive witness generation and certificate size**: the existence theorem does not bound extraction time, certificate length, separator discovery, or prove polynomial worst-case performance.
- **Independent adversarial/benchmark validation**: test nontrivial large `Family c r` members and nonmembers, witness-construction overhead, real external SAT solvers, malicious certificates and source mutations.
- **General-domain expansion**: prove, or falsify with a counterexample, a larger structural family in which cheap exact affine extraction and small separator covers arise. No extension to arbitrary SAT has been proved.
- **Original TC-063 instance identity**: no canonical original source document or benchmark certificate was identified in the repo audit; do not conflate the synthetic fixture with an external named instance.

## Track B is active: verified-path separator discovery

**Track A's restricted-family logical theorem is complete**, while Python refinement and runtime complexity remain separate open tasks. Track B's first prototype now uses actual indexed G5 row operations to reconstruct edge-lineage paths and rank their two boundary endpoints as **diagnostic** G14 separator candidates.

See [`docs/TC063_TRACK_B_BOUNDARY_PATH.md`](TC063_TRACK_B_BOUNDARY_PATH.md) for the full invariant proposal, the 144-trial cycle study, numerical comparisons against older heuristics, explicit wheel/cube false positives, and the signed-source Lean validation. The source-bound G5-to-G14 candidate checks passed at https://github.com/joeyst8/witnora-core/actions/runs/41595717841.

Next: a universal Lean proof of the mod-2 provenance-boundary identity, followed by adversarial graph controls and total pipeline runtime comparisons. The path heuristic is **not** a verified cut classifier; exact G14 validation remains mandatory.

No P-versus-NP result, general SAT polynomial-time algorithm, or breakthrough complexity separation has been claimed.


## 2026-11-03 domain expansion: arbitrary-CNF UNSAT proof checking

The user explicitly reprioritized the larger challenges: arbitrary CNFs,
non-affine residuals, no small separators, performance and industrial-scale
relevance. Rather than extend the restricted `Family c r` claim beyond its
premises, a **separate universal proof-checker family** has now been implemented
in the same draft PR:

1. `GeneralResolution.lean`: universally sound binary resolution checker
   from arbitrary signed clauses; every step must name two present clauses,
   correctly oriented pivot and exact computed resolvent.
2. `GeneralResolutionIndexed.lean`: compact zero-based DAG-index format,
   reconstructed and independently checked in Lean.
3. `GeneralResolutionStream.lean`: direct indexed streaming verification
   without expanding the entire by-value certificate; universal UNSAT theorem.
4. `GeneralResolutionAscii.lean`: actual supported ASCII DIMACS byte document
   parsed and connected to the signed clauses and streaming refutation; source-
   byte identity and UNSAT are conjoined by a universal theorem.

All four main theorem `#print axioms` outputs are **[propext, Quot.sound]**,
with no project axioms, `sorry` or SAT-verdict assumption. The final
source-bound CI passed all five native adversarial tests and Lean verified
the non-affine pigeonhole(3,2) refutation in by-value, indexed, streaming and
source-ASCII forms. It also verified rejection of a tampered DIMACS clause
count: https://github.com/joeyst8/witnora-core/actions/runs/41598267471 .

[Full audited milestone and next experimental program](GENERAL_SAT_RESOLUTION_BRIDGE.md).

**Non-claim:** the Python proof producer is an intentionally tiny saturation
algorithm, not competitive CDCL; proof search can take exponential resources.
The direct streaming proof database remains a list, so total checking is not
yet proven linear or near-linear. No arbitrary-size CDCL DRAT/LRAT import,
benchmark speedup, polynomial-time construction, or P-versus-NP conclusion is
established. The next *bigger-fish* gate is sound CDCL proof import with source
identity, then frozen hard non-affine and no-separator benchmarks against real
industrial solvers.


## 2026-11-03 universal CDCL/RUP bridge and measured limitation

An independent pinned Glucose3 CDCL solver now emits genuine DRUP proofs for
non-affine PHP(3,2), PHP(4,3), PHP(5,4). Untrusted Python elaboration turns
addition lines into explicit propagation witnesses; Lean rechecks every
inference using the general arbitrary-CNF `GeneralRUP.signedRup_unsat`
theorem, with a separate ASCII-source-bound theorem
`GeneralRUPAscii.checkAsciiRup_sound`. The Lean axiom audit reports only
`[propext, Quot.sound]`. Unsupported RAT-only steps are not silently
accepted; ignoring deletion hints is sound because the checker keeps the
previously proved clauses. The accepted CDCL smoke gate and tampered-DIMACS
rejection are in https://github.com/joeyst8/witnora-core/actions/runs/41599953956 .

The frozen PHP size ladder additionally generated and *natively replayed*
PHP(6,5) (30 variables, 81 source clauses, 140 added RUP clauses and 2,530
propagated units). Its single-run annotation time was 251.766 ms against
13.263 ms at PHP(5,4) (28 additions, 379 units); PHP(6,5) has **not**
been Lean checked yet. See the source and full table at
[General CDCL/RUP bridge](GENERAL_RUP_CDCL_BRIDGE.md) and successful
https://github.com/joeyst8/witnora-core/actions/runs/41600247380 .

This extends **sound verification** to arbitrary CNF, not efficient
proof construction, fast industrial SAT, or any polynomial-time bound.


## 2026-11-03 dense random 3-CNF and indexed-RUP speed experiment

Extending the universal CNF checker beyond affine/separator/pigeonhole
families, independent Glucose refutations of **dense random 3-CNFs**
(8/54, 10/66, 12/84 variables/clauses) passed Lean. Every variable pair
co-occurs in a clause (complete primal graph; no small variable separator).
Separate planted-SAT formulas with the same complete-primal property were
verified using explicit all-true assignments in Lean. The 8-variable UNSAT
proof was also bound to exact DIMACS ASCII bytes and a tampered header was
rejected. Successful https://github.com/joeyst8/witnora-core/actions/runs/41601167317 .

A new **opt-in indexed** Python witness generator uses literal occurrence
lists and an incremental queue. A native 300-instance differential test,
Glucose PHP(5,4) and PHP(6,5) native replays, and a Lean kernel acceptance
of the indexed PHP(5,4) proof all passed. Frozen one-run PHP(6,5)
annotation decreased from **259.882 ms** (reference) to **43.006 ms**
(indexed), a **6.04×** speedup in Python annotation only. Successful
https://github.com/joeyst8/witnora-core/actions/runs/41601552613 .

The existing Lean checker still scans lists; the Python indexed generator
has not made verification or solving polynomial-time, and PHP(6,5) is not
Lean-accepted yet. Full details in
[General CDCL/RUP bridge](GENERAL_RUP_CDCL_BRIDGE.md). Next: verified
row-index reason certificates, industrial proof formats and held-out
performance analysis, without inflating TC-063 restricted-family claims.


## 2026-11-03 indexed RUP reason theorem closed (arbitrary CNF)

`GeneralRUPIndexed.lean` universally proves that explicitly checked
zero-based unit-reason and conflict row IDs preserve RUP soundness. Its
`signedIndexedRup_unsat` theorem has axiom audit
`[propext, Quot.sound]`, no project-specific axioms or `sorry`.
`GeneralRUPIndexedAscii.lean` binds the exact supported DIMACS source
bytes and signed clauses to this indexed proof, also with only standard
axioms. Untrusted Python row-reference annotation was tested against real
Glucose DRUP: indexed PHP(3,2), PHP(4,3), PHP(5,4), and dense random
3-CNF (8 variables, 54 clauses) proofs were **Lean accepted**. Modified
source header and forged/future row ID examples were rejected. The complete
new gate is green: https://github.com/joeyst8/witnora-core/actions/runs/41602608726 .

This closes the next *soundness* milestone, **not** the industrial speed
milestone: Lean still uses list indexing/append, so an Array-backed
implementation with a proved reference correspondence is next. See
[the universal CDCL/RUP research report](GENERAL_RUP_CDCL_BRIDGE.md).


## 2026-11-03 OpenAI ETH-style clause-violation parity experiment (CI green)

Pivoting from physical/quark analogies, we inspected OpenAI's October 2026
ETH research and isolated a mathematically relevant transfer: parity sketches
of the **source CNF clause-violation vector**. This is distinct from ordinary
G5 affine XOR reconstruction and does not require small source separators.

The new finite experimental module
`witnora_core/eth_clause_violation_parity.py` greedily selects 2–5
clause sparse rows, with full 2^n enumeration; the independent verifier
checks source SHA-256 and both directions on every enumerated assignment.
The six existing deterministic complete-primal dense 3-CNFs yielded short
exact sketches: UNSAT 8/54 → 6 rows, 10/66 → 7 rows, 12/84 → 9 rows;
planted-SAT counterparts → 6, 9, 9 rows respectively. Distinct source
model counts are 0/0/0 for UNSAT and 1/1/5 for planted SAT. These counts
were reproduced locally in an independent exhaustive run.

The Lean module `ClauseViolationParity.lean` states and proves the
universal source-model ⇒ all parity-checks property. A generator emits
actual signed-source-bound finite Lean examples that check both
directions on the 8-variable source controls. The workflow was updated
to run the universal Lean build, Python exhaustive/tamper tests, and
generated Lean reductions. **The full workflow passed**: universal theorem axiom audit showed only
`[propext, Quot.sound]`, both 8-variable source-bound Lean equivalence
examples kernel-checked, six Python exhaustive/tamper cases passed, and
all existing resolution/RUP regressions passed:
https://github.com/joeyst8/witnora-core/actions/runs/41606445630 .

The reverse direction for arbitrary parity rows is false (two violated
clauses can cancel); exactness currently rests on exponential finite
enumeration. No new polynomial, subexponential, industrial SAT, or P=NP
claim is made. The mathematically difficult missing step is a
**non-enumerative** exact sparse-check construction and an efficient
exact polynomial/tensor contraction/counting procedure.

Full source, method, proof boundary and measurements:
[OpenAI ETH clause-violation parity bridge](OPENAI_ETH_CLAUSE_PARITY_BRIDGE.md).
