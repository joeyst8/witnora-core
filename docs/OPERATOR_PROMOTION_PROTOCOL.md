# Witnora research operator promotion protocol

This file defines a **claim boundary**, not a novelty announcement.

## States

1. `NO_SUPPORTED_OPERATOR_DISCOVERED`: the proposed family was not found
   in the supplied formula.
2. `RESEARCH_CANDIDATE_ONLY`: a candidate was found but the exact original
   source document were not supplied.
3. `SOURCE_BOUND_LEAN_PROOF_REJECTED`: the independent source-bound Lean
   gate failed or its attestation was incomplete.
4. `PROOF_VERIFIED_PER_INSTANCE_BENCHMARK_PENDING`: actual Lean execution
   checked the original document, canonicalization and the discovered spoke
   contradiction directly (an optional G5 certificate is also checked when provided).
   This proves **only the checked instance**, not the proposed general
   transformation, novelty, or superiority.

No state above automatically promotes an operator into the trusted library.

## Evidence required before future promotion

- **Soundness**: a kernel-checked *universal* preservation/soundness theorem
  for the proposed operation **and** source-bound checks on actual outputs.
- **Scope**: explicit domain of supported input formulas, rejection behavior
  outside that domain, and tests challenging that boundary.
- **Generality**: a parameterized family or independent test families, with
  examples beyond discovery seeds.
- **Performance**: reproducible experiments against at least an appropriate
  general SAT solver and a specialized baseline; include hardware details,
  preprocessing, certificate construction/check time and failure rates.
- **Novelty**: independent literature/prior-art review. The parity-spoke
  candidate is standard GF(2) elimination and **does not satisfy this**.
- **Reproducibility**: frozen benchmark instances, scripts, version pins,
  raw measurements and a stable evidence digest.

A positive benchmark or a forged JSON field must never substitute for Lean
acceptance. Equally, Lean acceptance alone does not establish a performance
advantage. Research claims must preserve both distinctions.

## Current implementation

- `witnora_core/spoke_discovery.py`: implied two-variable XOR discovery.
- `witnora_core/operator_promotion.py`: recomputes discovery, verifies
  source/canonical correspondence, then invokes the actual source-bound
  `verify_discovered_spoke_with_lean` gate; an optionally supplied G5
  certificate must independently pass its own Lean gate.
- `tests/test_operator_promotion.py`: missing provenance, fake status and
  fail-closed regression tests.
- `scripts/benchmark_spoke_collapse.py`: first exploratory comparison,
  not proof of superiority.

## Known open work

The general spoke contradiction theorem and a source-bound theorem connecting
four checked patterns in an arbitrary CNF are built in Lean. The executable
`SpokeDiscoverySpec.discoverFrom` filter also has universal output-soundness
and exact filter-membership theorems. The finite reference enumerator
`SpokeDiscoverySpec.allProposals` ranges over endpoint IDs, intermediate IDs
and all Boolean labels, and its coverage proof establishes that any proposal
within the supplied ID domain is included. `tests/test_spoke_discovery_reference.py`
compares Python output with an independently written exhaustive enumerator
on bounded randomized inputs. The production spoke gate additionally checks
exact Python binary-equation extraction against the executable Lean
`BinaryXorDiscovery.extract` specification for inputs with at most 24
variables. Lean proves this binary specification's complete pair/RHS
coverage and source-CNF soundness. These are checked-output guarantees,
not universal CPython execution refinement. The production
gate checks concrete discovered instances with this theorem; **universal
correctness and completeness of the Python detector's proposal enumeration** remains unproved. Universal Python interpreter
refinement and independent novelty audit also remain open.

## Complete path-refinement checkpoint

`SpokePathDiscovery.extract` enumerates every three-variable path and pair of parity labels from the finite domain. Lean proves exact filter membership and that each accepted path's two binary equations hold in all source-CNF models. The production spoke proof gate compares the complete Python `extract_spoke_paths` result against this executable Lean specification with a closed `by decide` obligation. The strongest spoke status now fails closed when the formula contains more than **6** distinct variables (the finite path enumeration has cubic variable growth) or Lean rejects any equality. The previous 24-variable binary-extraction limit is therefore superseded for this combined status. The independent test oracle covers randomized complete-path membership, but a universal proof about CPython execution and the entire graph-to-conflict selection remains open. This stage does **not** establish novelty, speed, or formal Python-language semantics.

## Indexed path scaling checkpoint

The source-bound spoke gate now uses the universal `SpokePathIndexed.checkExact_mem_iff` theorem: the reported path set and every indexed join of the previously checked binary equations have identical membership. Lean's closed executable check rejects spurious paths, missing paths, or duplicate reported paths. The direct cubic finite `SpokePathDiscovery.extract` remains a separate reference theorem, but is no longer evaluated in production for each input. The operative bound is the prior **24-variable binary extraction cap**, not 6. This is a set-level exactness result; path order is intentionally irrelevant, and a universal CPython execution refinement remains unproved.

## Source-indexed binary extraction checkpoint

`BinaryXorIndexed` derives candidate pairs from length-two source clauses and verifies exact opposite-polarity clause patterns for each right-hand side. The Lean `checkExact_mem_iff` theorem makes the accepted Python equation set complete relative to these source-derived candidates; `checkExact_sound` proves each accepted equation holds in every source CNF model. The production gate requires this closed Lean check along with exact indexed path joins and original-document UNSAT. The old 24-variable all-pairs limit has been removed; resource exhaustion or a Lean rejection still fails closed. This is for the *exact two-clause* binary XOR extraction contract: it is deliberately narrower than arbitrary logical implication or G5 clause-subsumption extraction. These results do not constitute a universal proof of CPython interpreter semantics.

## First real kernel-gate scaling baseline (2026-10-30)

The GitHub Actions artifact from commit `29cd28f` records actual Lean process timings, including source parsing, indexed binary and path checks, and the original-document UNSAT theorem. Environment: Linux Azure x86_64 GitHub runner. This is **one run per size**, not a statistically robust performance comparison.

| Spokes | Variables | Clauses | Paths | Gate time | Verified |
|---:|---:|---:|---:|---:|:---:|
| 3 | 5 | 12 | 9 | 1.362 s | yes |
| 5 | 7 | 20 | 25 | 2.803 s | yes |
| 9 | 11 | 36 | 81 | 11.929 s | yes |
| 25 | 27 | 100 | 625 | 45.055 s | **no: 45-second timeout** |

Artifact: [CI run 41116642578](https://github.com/joeyst8/witnora-core/actions/runs/41116642578). The test harness intentionally recorded the 27-variable rejection as a measurement instead of awarding verification. Deduplicating indexed edge joins is an experimental optimization after this baseline, **not yet validated by this table**. Any later table must include its own commit, run ID, timeout, and pass/fail.

## Indexed path deduplication follow-up (2026-10-30)

The `a712c6e` CI benchmark compares the same real source-bound proof process against baseline `29cd28f`. This is a single-run comparison on Azure-hosted Linux, not a variance-controlled speed claim.

| Variables | Baseline | Deduplicated join check | Change | Lean verified |
|---:|---:|---:|---:|:---:|
| 5 | 1.362s | 0.660s | ~2.1× faster | yes |
| 7 | 2.803s | 1.318s | ~2.1× faster | yes |
| 11 | 11.929s | 6.505s | ~1.8× faster | yes |
| 27 | 45s timeout | 45s timeout | not established | **no** |

Evidence: [optimized CI run 41117541879](https://github.com/joeyst8/witnora-core/actions/runs/41117541879). The kernel-checked set-membership theorem is now phrased against `uniqueJoins` (all indexed joins with duplicates removed). No unsafe assumptions were introduced. The remaining bottleneck is the quadratic-or-worse Lean reduction of candidate-set membership, plus possible certificate size effects. A scalable indexed lookup/normalized sorted-vector checker with a proved set-equivalence lemma is the next meaningful improvement. Until then, large source-bound spoke certificates may time out and **must not** receive verified status.

## Sorted-certificate research result (2026-10-30)

The new `SpokePathSorted.checkSorted` uses structurally recursive, kernel-evaluable sorted normalization. Lean proves `checkSorted_implies_exact`: any accepted sorted certificate necessarily passes the prior exact-set checker. The converse (full equivalence) is **not proved**. Direct finite adversarial examples are kernel-checked.

A real source-bound runtime benchmark on commit `bf4ad54` showed a regression relative to the deduplicated indexed baseline:

| Variables | Indexed default | Experimental sorted | Verified? |
|---:|---:|---:|:---:|
| 5 | 0.660s | 1.312s | yes |
| 7 | 1.318s | 2.603s | yes |
| 11 | 6.505s | 9.137s | yes |
| 27 | 45s timeout | 45s timeout | no |

Evidence: [sorted-checker CI run 41119320261](https://github.com/joeyst8/witnora-core/actions/runs/41119320261). Consequently the **production gate stays on** `SpokePathIndexed.checkExact` with deduplicated joins. The sorted variant is retained only as formally proved experimental code. It is not advertised as a performance improvement. A different indexed lookup representation and a true full equivalence theorem are required before promoting a replacement.

## General odd-cycle discovery research checkpoint

`witnora_core/cycle_discovery.py` now proposes arbitrary closed XOR-walk contradictions using a deterministic graph search over exact source binary patterns. It detects an inconsistent **three-edge triangle**, a case requiring only three variables and outside the current four-edge, two-middle spoke grammar. This is a genuinely broader *implemented detector scope*, **not** a new mathematical theory: parity-inconsistent cycles are a classical GF(2) graph-consistency technique.

`formal/Witnora/CycleParity.lean` contains the universal `closedWalk_unsat` theorem: every step backed by a complete source-CNF pattern, together with return to the start and odd edge parity, makes the original CNF UNSAT. `witnora_core/lean_cycle_gate.py` generates a closed source-bound ASCII DIMACS claim and grants `LEAN_SOURCE_CYCLE_UNSAT_VERIFIED` only after an actual Lean process accepts it. The runtime CI includes both a positive odd triangle and a clause-removal rejection case. Randomized tests compare discovery against a separate exhaustive Boolean oracle. **This operator is experimental, not automatically promoted**, and its performance/novelty versus standard parity union-find or Gaussian elimination has not been established.

## Cycle source-bound assessment integration

`assess_odd_cycle_operator` is now a distinct public research assessment
entry point, with the same fail-closed provenance policy as the spoke gate.
It recomputes the discovered odd walk from the supplied formula, validates
the original ASCII DIMACS source against the formula's normalized clauses
(including exact tokens and decimal spellings), and checks the odd-walk
UNSAT theorem in a fresh Lean process. An optional G5 certificate must
also pass source-bound Lean verification when supplied. Success returns
`PROOF_VERIFIED_PER_INSTANCE_BENCHMARK_PENDING`, with proof-source digests,
and **never** `promoted: true`.

The CI exercises this whole entry point against a three-edge contradiction
and an altered source-document header. The negative case must be rejected.
This does not prove universal CPython refinement, or superiority to
parity union-find / Gaussian elimination. Scientific benchmarking,
coverage of difficult non-XOR instances, and independently confirmed
novelty remain outstanding.

## First cycle-discovery comparative benchmark protocol

The reproducible exploratory harness `scripts/benchmark_cycle_discovery.py`
compares four algorithms on the **same generated CNF instances**:

- Witnora's Python exact-pattern extraction plus graph-walk contradiction detector.
- A separate parity union-find implementation on the generating XOR edges.
- An independent GF(2) bit-mask Gaussian elimination on those edges.
- Glucose3 through pinned `python-sat==1.8.dev24` on the complete CNF.

Families include consistent and inconsistent XOR cycles, denser graphs, and
a deliberately non-XOR UNSAT instance containing contradictory unit clauses.
The last family is a designed *coverage failure* for the XOR-only algorithms,
not a bug to disguise. GF(2) baselines receive the generating equation list,
while Witnora must extract those equations from CNF, so direct timings
include different preprocessing and should not be marketed as equivalent
end-to-end solves.

The CI emits per-case records with seed, SHA-256 of the canonical DIMACS
source, counts, algorithm, median milliseconds over three runs, and actual
SAT oracle truth. The benchmark reports `lean_checked = 0`: these timings
**exclude** the per-instance Lean source-proof gate, which is verified by
separate real-Lean CI tests. They are single-run, uncalibrated Python/Glucose
measurements, not evidence of a competitive performance advantage.
Reproduction command:

```sh
PYTHONPATH=. python scripts/benchmark_cycle_discovery.py --sizes 8 24 64 --repeats 3 --seed 63063 --output cycle-benchmark.csv
```

The independent test `tests/test_cycle_benchmark.py` compares the parity
union-find and GF(2) solvers to exhaustive assignments on random small
graphs. Publication-quality comparison still requires repeated independent
runners, memory measurements, larger adversarial cases, certificate
generation/check time, and state-of-the-art specialized solvers.

## Parity-component structural compression: first formal milestone

`ParityCompression.reconstruct_preserves_edges` is a universally quantified
Lean theorem. Given a verified root label and Boolean parity offset for each
vertex, if every represented binary-XOR edge connects the same root and its
offset parity matches the edge constraint, **every choice of Boolean root
values reconstructs a valuation satisfying all represented edges**.

`witnora_core/parity_compression.py` produces a deterministic, explicitly
**unverified** component/root/offset candidate from exact binary XOR-CNF
patterns. It rejects inconsistent graphs; property tests enumerate *every*
root assignment on randomized small consistent graphs. Components can encode
`n` represented vertices by `k` root choices (with `n-k` derived variables)
but no general formula compression or runtime speedup is established.

**Important mathematical boundary:** the theorem proves one-directional
soundness of the reconstructed assignment for the *extracted XOR edges*. It
does not yet establish the reverse mapping of every original CNF model to
root values, equivalence of arbitrary residual CNF clauses after substitution,
or a source-bound per-instance Lean check of the Python offset map. Those
are the next proof obligations before any replacement of production G5/G14
formula handling. This is classical parity-component substitution, not
independently novel mathematics.

## Bidirectional parity-root residual correspondence

The next formal bridge is now in Lean:

- `ParityCompression.source_model_reconstructs` obtains each original
  variable from its chosen component root and parity offset, **provided**
  that a supplied root-to-variable path is checked against the original
  source CNF and has the asserted endpoint and parity.
- `ParityCompression.source_iff_root_residual` establishes equivalence of
  source satisfiability and satisfiability under root-substituted
  assignments, under these same source-backed path hypotheses.
- `ParityResidual.residual_semantics` proves exact literal-by-literal
  semantics for an arbitrary CNF, including non-XOR residual clauses.
- `ParityResidual.source_iff_rewritten_residual` composes the two results
  into an equisatisfiability theorem for the complete rewritten CNF.

Python `compress_binary_xor_components` now emits root-path witnesses.
`substitute_residual_formula` constructs a canonicalized root-substituted
residual and independent randomized tests compare all root assignments to
their reconstructed original assignments. The derivation is **experimental**:
the Lean theorem is universal **conditional on verified source paths**, but
the exact Python-output path mapping and post-substitution normalization
are not yet fed into a complete source-bound Lean certificate checker.
Nothing here authorizes full-G5/G14 trusted replacement until that gate
is in place. No general algorithmic advantage is claimed.

## First full source-bound parity-residual certificate (2026-10-30)

`verify_parity_compression_with_lean` now independently recomputes and
checks the complete certificate for supported ASCII DIMACS inputs:

1. The original text, signed token stream, decimal spellings, raw clauses,
   and canonical Python CNF must pass the existing normalization Lean gate.
2. Python emits component roots, offsets, all root-to-vertex paths, and
   a literal-rewritten residual formula.
3. The generated Lean proof checks **every** emitted path against source-CNF
   binary XOR patterns, verifies exact path endpoints and parity offsets,
   invokes `ParityResidual.source_iff_rewritten_residual`, and checks
   exact equality of the unnormalized rewritten CNF to Lean's substitution.
4. A separate normalization Lean gate checks the final canonical Python
   residual. The result is fail-closed on any rejection or timeout.

A real GitHub Actions check succeeded for a graph with two consistent XOR
edges and an additional non-XOR residual clause; a malformed original
DIMACS header was rejected. This grants the narrow
`LEAN_SOURCE_PARITY_RESIDUAL_EQUIVALENT` status for that instance only.
The production G5/G14 solvers still use their existing approved paths:
this new compression is **not** automatically substituted into them.
Full CPython execution refinement, scalability on larger proof witnesses,
and a competitive performance advantage remain unproved.
