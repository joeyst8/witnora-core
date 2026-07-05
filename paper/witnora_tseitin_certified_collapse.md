# Certified Collapse of Tseitin Formulas via XOR Detection and Sparse Elimination

## Abstract

Witnora-Core is a certified collapse-path engine for CNF SAT formulas. This
systems note reports a bounded diagnostic result on official CNFgen-generated
Tseitin formulas. Witnora-Core detects exact XOR structure already encoded in
the CNF, records deterministic sparse/min-fill XOR elimination traces, exports
DRAT proofs, and checks those proofs with real `drat-trim` against
`original.dimacs`. In v0.9.8, seven recorded official CNFgen Tseitin rows are
externally verified, including `tseitin_20 c=2`. The earlier v0.8.4 diagnostic
reported `NO_COLLAPSE_FOUND` for the same Tseitin family rows. The result is
limited to exact-pattern XOR extraction, a bounded diagnostic matrix, and
externally checked proof artifacts; it is not a competitiveness claim and does
not address parity formulas or broad XOR extraction.

## 1. Introduction

Witnora-Core studies a narrow question: can a deterministic, replayable
collapse engine turn selected CNF formulas into certified SAT or UNSAT results
without using an external SAT solver for solving? Earlier releases established a
collapse-path framework, certificate bundles, an independent raw checker,
public result categories, benchmark artifacts, and DRAT export for supported
UNSAT paths.

The v0.8.4 official CNFgen diagnostic showed a clear gap: the Tseitin rows in
the recorded matrix remained `NO_COLLAPSE_FOUND`. The v0.9 series added exact
CNF XOR extraction and a bounded XOR-to-DRAT proof bridge. The final v0.9.8
diagnostic records the before/after result: the selected official Tseitin rows
move from no-collapse to externally checked DRAT proofs under the recorded
configuration.

This note is a short systems report. It makes row-level claims about a
reproducible artifact, not broad claims about SAT solving.

## 2. Background

### CNF SAT

A CNF formula is a conjunction of clauses, where each clause is a disjunction of
literals. A SAT certificate is an assignment satisfying the original formula. An
UNSAT certificate requires evidence that no assignment satisfies the original
formula.

### Collapse Paths

Witnora-Core represents computation as a collapse path: a deterministic sequence
of simplification, decomposition, restricted solving, reconstruction, and
verification steps. A collapse path is accepted only when it can be replayed and
checked against the original input.

### Tseitin Formulas

Tseitin formulas encode parity constraints over graph-like structure into CNF.
They are useful here because their algebraic structure is explicit enough for an
exact XOR detector to identify, while still being invisible to the earlier
treewidth-focused route under the recorded diagnostic.

### XOR and Affine Structure

An XOR equation over GF(2) has the form
`x1 xor x2 xor ... xor xk = b`. Witnora-Core v0.9.8 detects only exact full-CNF
encodings of such equations up to the configured arity cap. It does not perform
heuristic XOR mining.

### DRAT Proof Checking

DRAT proof checking validates clausal proof artifacts. Witnora-Core treats
native XOR inconsistency as an internal trace and counts original-CNF UNSAT as
externally certified only when `proof.drat` is accepted by real `drat-trim`
against `original.dimacs`.

## 3. Witnora-Core Architecture

### Deterministic Collapse Grammar

The core collapse grammar includes unit propagation, pure literal elimination,
subsumption, blocked clause elimination, component decomposition, bounded
treewidth solving, 2-SAT solving, and exact XOR reasoning for explicitly
supported inputs.

### Certificate Bundles

Witnora certificate bundles store `original.dimacs`, normalized formulas,
collapse paths, reconstruction traces, result metadata, proof traces, DRAT
status, and hashes. Timing is not part of the certificate hash.

### Independent Checker

The independent raw checker parses raw DIMACS, recomputes supported
transformations from raw clauses, checks SAT assignments against the original
formula, replays native XOR traces, and verifies that public categories match
the proof metadata. It does not replace `drat-trim` for DRAT proof validation.

### Public Result Categories

Public reports separate logical result, discovery route, and certification
level. The key categories used in this note are:

- `UNSAT_DRAT_EXPORTED_VERIFIED`: `proof.drat` was verified by real
  `drat-trim` against `original.dimacs`.
- `UNSAT_XOR_NATIVE_ONLY`: a native XOR contradiction exists, but no external
  original-CNF DRAT proof is claimed.
- `NO_COLLAPSE_FOUND`: Witnora did not find a collapse under the recorded
  grammar and parameters.

## 4. XOR Collapse Layer

### Exact CNF XOR Extraction

For variables `V = {x1, ..., xk}` and RHS `b`, the full CNF encoding of an XOR
equation contains one clause for each assignment to `V` whose parity is not `b`.
Witnora detects such encodings only when the exact source clauses are present.
Source clauses are retained in the CNF.

### Sidecar Distinction

Sidecar XOR equations define a combined problem: `CNF and XOR-sidecar`. They are
not claimed to be implied by the original CNF. This note concerns detected-CNF
XOR equations whose source clauses are already in `original.dimacs`.

### Gaussian Elimination

Gaussian elimination over GF(2) finds native XOR contradictions when the
detected equations are inconsistent. Free variables are handled
deterministically in SAT cases.

### Deterministic Sparse/Min-Fill Elimination

The sparse/min-fill order is a deterministic heuristic used to reduce peak row
width during XOR elimination. The order and row-operation trace are recorded in
the certificate and independently replayed. It is not claimed to be optimal.

## 5. Certification Model

### SAT Assignment Verification

SAT results are certified by reconstructing an assignment and checking it
against the original CNF and any active XOR equations.

### Native XOR Trace Replay

A native XOR trace records GF(2) row operations. The independent checker accepts
the native contradiction only when replay reaches `0 = 1`.

### DRAT Export

For detected-CNF XOR contradictions, Witnora emits a clausal proof guided by
the recorded XOR trace. The proof base is the original CNF, not a sidecar or
modified formula.

### drat-trim Verification

The certification authority for externally checked UNSAT rows is real
`drat-trim`. Witnora reports `UNSAT_DRAT_EXPORTED_VERIFIED` only when
`drat-trim` accepts `proof.drat` against `original.dimacs`.

## 6. Experimental Setup

- Witnora tag: `v0.9.8`
- Witnora commit: `27e1876b5d815e3f3ba21392395b0e0e9dbcd025`
- CNF generator: official CNFgen `0.9.5`
- CNFgen path used:
  `C:\Users\maham\AppData\Local\hermes\hermes-agent\venv\Scripts\cnfgen.exe`
- Proof checker:
  `C:\Users\maham\AppData\Local\Temp\witnora-drat-trim-real\drat-trim\drat-trim.exe`
- Source archive SHA256:
  `26557CD73DC45DF60EF5E056699AFC34E3402645DE60EFE050C5CE2ADADC267F`
- Diagnostic artifact SHA256:
  `4702299E28CDB4E3B16B0CD1CBFE9BA96018E625C0E8864A1C0476C2AEC3FA2C`
- Clean extraction tests: 188 passing

The v0.8.4 baseline reported the official Tseitin diagnostic rows as
`NO_COLLAPSE_FOUND`. The v0.9.8 matrix uses `--detect-xor`,
`--detect-xor-max-k 6`, `--xor-elim-order sparse-min-fill`, `--xor-drat`, and
real `drat-trim`.

## 7. Results

### Table 1. v0.8.4 vs v0.9.8 Tseitin Results

| instance | c | v0.8.4 public category | v0.9.8 public category | detected XOR equations | max XOR arity | peak row width | proof clauses | proof bytes | drat-trim runtime | cap profile |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| tseitin_10 | 2 | NO_COLLAPSE_FOUND | UNSAT_DRAT_EXPORTED_VERIFIED | 10 | 4 | 6 | 575 | 12381 | 0.073599 | default |
| tseitin_10 | 3 | NO_COLLAPSE_FOUND | UNSAT_DRAT_EXPORTED_VERIFIED | 10 | 4 | 6 | 575 | 12381 | 0.072742 | default |
| tseitin_10 | 4 | NO_COLLAPSE_FOUND | UNSAT_DRAT_EXPORTED_VERIFIED | 10 | 4 | 6 | 575 | 12381 | 0.072092 | default |
| tseitin_15 | 2 | NO_COLLAPSE_FOUND | UNSAT_DRAT_EXPORTED_VERIFIED | 15 | 4 | 8 | 3999 | 124485 | 0.090604 | default |
| tseitin_15 | 3 | NO_COLLAPSE_FOUND | UNSAT_DRAT_EXPORTED_VERIFIED | 15 | 4 | 8 | 3999 | 124485 | 0.092360 | default |
| tseitin_15 | 4 | NO_COLLAPSE_FOUND | UNSAT_DRAT_EXPORTED_VERIFIED | 15 | 4 | 8 | 3999 | 124485 | 0.093661 | default |
| tseitin_20 | 2 | NO_COLLAPSE_FOUND | UNSAT_DRAT_EXPORTED_VERIFIED | 20 | 4 | 10 | 7775 | 277861 | 0.121430 | medium-v098 |

### Table 2. Gaussian vs Sparse/Min-Fill

| instance | order | peak width | public category | proof clauses | proof bytes | drat-trim runtime |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| tseitin_15 | Gaussian | 14 | UNSAT_XOR_NATIVE_ONLY | 0 | 0 | not run |
| tseitin_15 | sparse/min-fill | 8 | UNSAT_DRAT_EXPORTED_VERIFIED | 3999 | 124485 | approximately 0.091s |

### Table 3. Cap Sensitivity

| instance | c | profile | row cap | outcome | proof clauses | proof bytes | drat-trim runtime | note |
| --- | ---: | --- | ---: | --- | ---: | ---: | ---: | --- |
| tseitin_20 | 2 | default | 8 | UNSAT_XOR_NATIVE_ONLY | 0 | 0 | not run | row width 10 exceeds cap 8 |
| tseitin_20 | 2 | medium-v098 | 10 | UNSAT_DRAT_EXPORTED_VERIFIED | 7775 | 277861 | approximately 0.121s | verified against original.dimacs |

### Table 4. Reproducibility Artifacts

| artifact | value |
| --- | --- |
| source archive | `witnora-core-v0.9.8.zip` |
| source SHA256 | `26557CD73DC45DF60EF5E056699AFC34E3402645DE60EFE050C5CE2ADADC267F` |
| diagnostic artifact | `witnora-core-v0.9.8-full-tseitin-minfill-diagnostic.zip` |
| diagnostic SHA256 | `4702299E28CDB4E3B16B0CD1CBFE9BA96018E625C0E8864A1C0476C2AEC3FA2C` |
| tag | `v0.9.8` |
| commit | `27e1876b5d815e3f3ba21392395b0e0e9dbcd025` |
| tests | 188 passing |
| real drat-trim | used for proof verification |

## 8. Theorem and Proof Notes

### Exact XOR Pattern Soundness

If a set of CNF clauses exactly equals the forbidden-assignment CNF encoding of
an XOR equation `E`, then every assignment satisfying those clauses satisfies
`E`. Adding `E` as an implied constraint while retaining the source clauses is
sound for SAT witnesses and for native XOR reasoning.

### XOR Elimination Trace Soundness

A recorded GF(2) row-operation trace is sound if every row is obtained by
XOR-combining previous or source rows and the final row is `0 = 1`. This
establishes native XOR inconsistency of the detected equation system.

### DRAT Certification Boundary

Native XOR inconsistency is not, by itself, an external proof of original CNF
UNSAT. Witnora counts UNSAT as externally certified only when `proof.drat` is
verified by real `drat-trim` against `original.dimacs`.

### Sparse/Min-Fill Determinism

Sparse/min-fill is a deterministic heuristic order recorded in the certificate
and independently replayed. It is not claimed to be optimal.

## 9. Limitations

- Exact XOR patterns only.
- Detection cap `k <= 6` in this diagnostic.
- Tseitin diagnostic rows only.
- No parity result is claimed.
- No industrial benchmark result is claimed.
- No SAT solver competitiveness result is claimed.
- No full DRAT/RAT/LRAT/FRAT support is claimed.

## 10. Related Work and Positioning

Witnora-Core is positioned among SAT preprocessing, certified solving, XOR-aware
reasoning, and proof logging. SAT preprocessors commonly simplify formulas
before solving; Witnora records a replayable collapse path and public category
for each result. XOR-aware SAT systems use algebraic structure to improve
reasoning; Witnora's v0.9.8 route is narrower and accepts only exact CNF XOR
encodings. DRAT proof logging supplies externally checkable UNSAT artifacts;
Witnora uses real `drat-trim` as the authority for counted externally verified
UNSAT rows.

The contribution reported here is the integration of exact-pattern XOR
detection, deterministic sparse/min-fill trace recording, and externally checked
DRAT proof export in a reproducible systems artifact.

## 11. Reproducibility

The reproducibility package records the source archive, diagnostic artifact,
commands, expected category counts, proof locations, drat-trim logs, and
independent checker output locations. The key command is:

```powershell
$env:WITNORA_DRAT_TRIM='C:\Users\maham\AppData\Local\Temp\witnora-drat-trim-real\drat-trim\drat-trim.exe'
python -m witnora_core.xor_drat_diagnostic --matrix-preset full-tseitin-v098 --detect-xor-max-k 6 --xor-drat --elim-orders sparse-min-fill --profiles default medium-v098 --drat-trim 'C:\Users\maham\AppData\Local\Temp\witnora-drat-trim-real\drat-trim\drat-trim.exe' --cnfgen-path 'C:\Users\maham\AppData\Local\hermes\hermes-agent\venv\Scripts\cnfgen.exe' --out-root outputs\v0.9.8-full-tseitin-minfill-diagnostic --zip witnora-core-v0.9.8-full-tseitin-minfill-diagnostic.zip
```

Expected best-matrix public category counts:

- `UNSAT_DRAT_EXPORTED_VERIFIED`: 7
- `UNSAT_XOR_NATIVE_ONLY`: 0
- `NO_COLLAPSE_FOUND`: 0
- `TIMEOUT`: 0
- `ERROR`: 0

## 12. Conclusion

The v0.9.8 artifact establishes a bounded certified systems result: selected
official CNFgen Tseitin diagnostic rows that were previously no-collapse are
externally DRAT-verified after exact CNF XOR extraction and deterministic
sparse/min-fill proof export. The result is intentionally narrow, but it is
reproducible, externally checked, and separated from native-only or skipped
cases by public result categories.
