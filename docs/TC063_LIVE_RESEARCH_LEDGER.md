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

## Next milestone

**Track A is logically closed for the restricted theorem**. Run and maintain the full green CI gate on current head, audit the trust boundary and exact executable checker acceptance for real serialized certificates, and test hard instances before announcing operational completeness. **Then** move to Track B structural discovery, as the user requested. Retain this audit and links in draft PR #121; avoid repeating proofs already present in `TC063PatternPermutation` and `TC063CanonicalBound`.

No P-versus-NP result, general SAT polynomial-time algorithm, or breakthrough complexity separation has been claimed.
