# General-CNF CDCL → Lean RUP bridge (beyond TC-063)

Checkpoint: 2026-11-03 UTC. Draft PR #121, branch
`formal/g14-python-seen-enqueue-v121`.

## Proven universal soundness, no TC-063 family assumption

`formal/Witnora/GeneralRUP.lean` defines a proof-carrying **RUP-subset**
verifier. For each proposed clause `C`, its independent Lean checker starts
with the negation of every literal in `C`; it then checks an explicit list
of unit-propagation claims. A claimed forced unit is accepted only if a
currently present clause contains it and every other literal in that clause
is false under previously accepted assumptions. The final witness must
falsify one present clause. If every RUP addition is checked and the empty
clause is eventually present, `signedRup_unsat` proves **UNSAT for every
assignment to the original signed CNF**.

The RUP soundness theorem is universal in the number of variables, original
clauses and proof steps. Its axiom audit reports only
`[propext, Quot.sound]`—no `sorry`, project axiom, Python implementation
assumption, or exhaustive whole-CNF SAT search.

`formal/Witnora/GeneralRUPAscii.lean` further verifies the supported
**actual ASCII DIMACS input byte list** using `DIMACSDocument` and
`DIMACSTokens`, then connects those parsed clauses to the checked RUP
refutation. It returns both a source-document identity fact and an UNSAT
theorem. A changed header clause count is rejected.

## Real external CDCL proof, not an invented Witnora trace

`witnora_core/rup_witness_import.py` accepts a genuine DRUP trace produced
by **Glucose3** (through pinned `python-sat==1.8.dev24`), independently
recomputes a unit-propagation witness for each addition, and emits an
explicit `RupStep`. It rejects any uncheckable addition. It can ignore DRUP
deletion hints **safely** because retaining a superset of previously proved
clauses cannot invalidate a RUP inference; the Lean checker still rechecks
every remaining addition from the full active database. Solver verdicts,
proof text and Python witness elaboration are *untrusted inputs*.

The `scripts/generate_glucose_drup_rup_lean.py` acceptance gate used
**real solver-generated** refutations of three non-affine pigeonhole CNFs:

| Instance | Original variable count | External proof | Final verifier |
|---|---:|---|---|
| PHP(3,2) | 6 | Glucose3 DRUP | Lean accepted |
| PHP(4,3) | 12 | Glucose3 DRUP | Lean accepted |
| PHP(5,4) | 20 | Glucose3 DRUP | Lean accepted |

The smallest proof was additionally tied to an independently checked ASCII
DIMACS byte document, with a negative tampered-header check. The universal
`GeneralRUPAscii.checkAsciiRup_sound` theorem applies to all supported
source inputs even though the *concrete example* covers only PHP(3,2).

`tests/test_glucose_drup_import.py` covers the real 3/2 and 4/3 proofs,
forged unit witness, missing original source, immediate invalid proof and
logically safe deletion omission. A separate generated proof converted from
Witnora's ordinary resolution trace includes forged RUP witness rejection.
The targeted CI for all three independent Glucose examples and source
binding passed:

https://github.com/joeyst8/witnora-core/actions/runs/41599953956

The official PySAT solver API documents that its Glucose implementation
supports `with_proof=True` and `get_proof()` producing DRUP clauses:
https://pysathq.github.io/docs/api/solvers.html .

## Research boundary and scaling challenge

- **Verification is not discovery**: Glucose searched for the refutations;
  Witnora has not outperformed it. A valid external proof does not prove a
  new SAT-solving algorithm or P=NP.
- This first Lean checker accepts RUP **additions with explicit unit witnesses**.
  It does not accept general RAT additions, LRAT hints, FRAT, or arbitrary
  solver proof formats.
- The proof database and unit search currently use lists. Even though the
  theorem is universal, runtime and memory can grow steeply. There is no
  proven linear proof-checking bound.
- The source byte theorem covers the executable Lean ASCII DIMACS parser's
  supported grammar, not every possible DIMACS dialect.
- External solver proof SHA-256 is logged for provenance, but SHA-256 itself
  is not a cryptographic assumption of the Lean soundness theorem.
- Proof-producer CPython refinement is not universally established;
  **soundness survives a buggy producer** because Lean independently checks
  output.

## Next bigger-fish gates

1. A **frozen PHP(3,2)-to-PHP(6,5) timing ladder**, with Glucose solving,
   proof line count, RUP witness elaboration time and native replay reported
   separately from Lean checks (one-run diagnostic; no speed claim).
2. A more efficient **array-indexed clause database and watched-literal unit
   propagation**, with a semantics-preserving Lean refinement theorem.
3. A real LRAT/RAT importer or proof bridge for CDCL engines whose output
   is not all RUP; failures must remain failures.
4. Held-out, source-bound industrial non-affine benchmarks and random 3-SAT
   no-separator controls against baseline Glucose/Kissat/CaDiCaL. Measure
   preprocessing plus solver plus proof production plus Lean verification.
5. Use those results to develop **new Witnora transformations that shrink
   hard proof search**, each with validated SAT model lifting and UNSAT proof
   lifting. A better checker alone does not make SAT solving faster.

This is a firm mathematical trust advance, **not** yet a solver-performance
breakthrough.


## 2026-11-03 frozen CDCL proof-size ladder (single CI sample)

The new bounded CI diagnostic runs the same pinned Glucose3→DRUP→native RUP
witness elaboration/replay over a growing family. **Only PHP(3,2), PHP(4,3)
and PHP(5,4) underwent the separate Lean acceptance gate**; PHP(6,5) was
native checked in this initial measurement, not yet Lean checked.

| Instance | Variables / source clauses | DRUP lines / RUP additions | Propagated units | Solver + proof | Witness annotation | Native replay | Status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| PHP(3,2) | 6 / 9 | 2 / 2 | 11 | 0.352 ms | 0.139 ms | 0.041 ms | Lean checked separately |
| PHP(4,3) | 12 / 22 | 7 / 7 | 68 | 0.163 ms | 1.115 ms | 0.201 ms | Lean checked separately |
| PHP(5,4) | 20 / 45 | 57 / 28 | 379 | 0.275 ms | 13.263 ms | 1.469 ms | Lean checked separately |
| PHP(6,5) | 30 / 81 | 235 / 140 | 2,530 | 0.922 ms | 251.766 ms | 16.527 ms | Native-only, Lean pending |

Single un-warmed GitHub runner measurement; timings include local Python
representation overhead and are **not** comparative throughput evidence.
The importer deliberately retains 29 and 95 DRUP deletion hints at 5/4 and
6/5 respectively. Native annotation increases much faster than input size,
indicating a concrete quadratic-or-worse bottleneck in current repeated full
clause scans and list-based proof database. No complexity bound is claimed.

Successful CI job: https://github.com/joeyst8/witnora-core/actions/runs/41600247380 .
Next gate: dense random 3-CNF controls and a watch/indexed propagation
implementation that retains the same Lean-checked theorem, with independent
source-bound SAT/UNSAT controls and trace-length measurements.


## 2026-11-03 dense random 3-CNF without small variable separators

The next test family is **not** a pigeonhole, affine-XOR, or
separator-decomposition construction. A fixed-seed sampler chooses distinct
three-literal clauses and rejects samples unless **every variable pair
co-occurs** in at least one clause. Its primal variable-interaction graph
is therefore complete, with no nontrivial small variable separator.

| Candidate | Source clauses | Genuine Glucose DRUP | Lean UNSAT gate | Planted SAT control |
|---|---:|---|---|---|
| Random 3-CNF, 8 variables | 54 | Imported and replayed | Passed; ASCII-bound source and modified-header rejection | Lean proved all-true assignment |
| Random 3-CNF, 10 variables | 66 | Imported and replayed | Passed | Lean proved all-true assignment |
| Random 3-CNF, 12 variables | 84 | Imported and replayed | Passed | Lean proved all-true assignment |

The SAT controls come from a separate generator that ensures each clause
contains a positive literal. They also have complete primal graphs.
Glucose independently reports SAT, and Lean verifies the explicit model.
The native tests check deterministic clause generation, the complete-primal
predicate, and missing-source rejection. Successful general-resolution
CI: https://github.com/joeyst8/witnora-core/actions/runs/41601167317 .

**Limitations:** These remain modest random test instances, selected using
solver results and bounded proof length. They do not prove complete proof
import for every CDCL run, RAT support, or industrial-scale performance.


## 2026-11-03 opt-in indexed propagation: validated A/B experiment

`witnora_core/rup_indexed_propagation.py` adds a second, **untrusted** RUP
witness producer. Each addition builds literal-to-clause occurrence lists
and maintains a work queue and unsatisfied-literal counts. An assignment
updates only its affected clauses, avoiding the reference implementation's
complete database sort/scan at every propagated unit.

`annotate_drup(..., indexed_propagation=True)` is opt-in. A 300-case
small random differential test compared conflict reachability to the
reference implementation. The actual Glucose PHP(5,4) and PHP(6,5) traces
produced the same *added clauses*, independently replayable witnesses, and
no rejected RUP step. The generated indexed PHP(5,4) refutation additionally
passed the **existing Lean RUP checker**, so the optimization has not
changed the proof authority.

| Instance | Reference Python annotation | Indexed Python annotation | Single-run improvement | Indexed units |
|---|---:|---:|---:|---:|
| PHP(3,2) | 0.140 ms | 0.100 ms | 1.40× | 10 |
| PHP(4,3) | 1.134 ms | 0.523 ms | 2.17× | 64 |
| PHP(5,4) | 13.052 ms | 3.356 ms | 3.89× | 363 |
| PHP(6,5) | 259.882 ms | 43.006 ms | 6.04× | 2,434 |

The A/B run and every source/proof/native/Lean test completed successfully:
https://github.com/joeyst8/witnora-core/actions/runs/41601552613 .
These numbers use one shared CI runner, with sequential order and no
repeated confidence intervals. They demonstrate a speedup in **Python
witness production**, not in Lean's still-list-scanning RUP verification
or the solver itself. PHP(6,5) remains native-replayed, not Lean-gated.

Next performance milestone: **proof row IDs and reason indices in Lean**,
with a universal theorem that every indexed unit reason and indexed
contradiction points to a present clause. That would remove the verifier's
repeated existential row search while preserving soundness. Then stress
larger non-affine and industrial instances, handle unsupported RAT proof
steps explicitly, and benchmark total wall time against CDCL/DRAT checkers.
