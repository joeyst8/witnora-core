# TC-063 live research ledger

Last verified: 2026-11-03 UTC (draft PR #121, branch `formal/g14-python-seen-enqueue-v121`).

## Important identity: TC-063 is a theorem, not a named benchmark

The repository README names TC-063 the **Bounded Separator-Affine Collapse Theorem** restricted to SAF(c,r). No uniquely identified original “TC-063 DIMACS input file” or full authentic certificate bundle was found in the repository inspection or prior project context. The concrete instance below is **deliberately synthetic**, not the original target theorem or a field benchmark.

## Verified pipeline to date

1. `TC063SourceVertexCuts.lean`: a closed checker reconstructs source primal adjacency from exact signed CNF clauses, canonicalizes the variable universe, rejects invalid zero literals, and proves sound and complete two-cut claims relative to the verified G14 finite DFS component count.
2. `TC063AsciiSourceVertexCuts.lean`: the independent DIMACS document parser and exact signed-token stream checker tie the above graph proof to the source ASCII byte sequence. Python's adjacency, clause segmentation, and selected token stream are not trusted by Lean.
3. `TC063AsciiCutG14Composition.lean`: composes a verified genuine two-cut with checked conditioned G14 partitions and G5 contradiction certificates on every enumerated separator assignment. The result is source-CNF UNSAT **when its explicit premises pass**.
4. `TC063AsciiTwoCutSmoke.lean` plus `fixtures/tc063_ascii_two_cut_unsat_smoke.cnf`: fully executable, kernel-checked *concrete* witness. The source graph is a 4-cycle with genuine cuts (1,3) and (2,4); the independent units x2 and ¬x2 give a closed G5 certificate in every branch of (1,3). The smoke intentionally uses the entire conditioned residual as a one-component exact partition. It tests the architecture, not decomposition speed or novelty.
5. `scripts/generate_tc063_ascii_smoke_identity_lean.py`: reads the committed .cnf bytes and emits an additional Lean equality check against the proof's source-byte literal. This prevents unnoticed fixture/proof drift.

Targeted CI: https://github.com/joeyst8/witnora-core/actions/runs/41583294191 (green). Other branch graph and Python differential checks are retained. No `sorry`, `axiom`, `unsafe`, or `native_decide` proof-hole declarations are admitted by the targeted scan.

## Still open — no unwarranted generality

- **TC-063 family completeness.** `TC063CompletenessReduction.lean` states an explicit `AffineG5Complete r` obligation. `TC063CanonicalAffineBridge.lean` reduces that further to the missing universal bridge
  `∀ cnf, CertifiedAffine r cnf → CanonicalAffineWitness r cnf`. The latter is an explicit *assumption* in the current family-completeness theorem and is **not proved**.
- **Python refinement.** Neither the full CPython parser/normalizer nor every low-link and certificate-emitter run is universally shown to produce Lean-accepted output. Differential cases are finite and diagnostic.
- **Certificate production for a nontrivial complete SAF member.** The smoke uses contradictory units, a trivial G5 core, and a single residual component. It is not an authentic TC-063 benchmark or a scaling demonstration.
- **Asymptotic/complexity discovery.** No general SAT polynomial-time guarantee, P≟NP result, or new complexity class separation has been established.

## Next experiment and exact proof target

Attack the canonical-witness implication directly:

```lean
∀ (r : Nat) (cnf : Witnora.Concrete.CNF),
  Witnora.SemanticSAF.CertifiedAffine r cnf →
  Witnora.TC063CanonicalAffineBridge.CanonicalAffineWitness r cnf
```

Audit the definitions of `CertifiedAffine` and `CanonicalAffineWitness` before attempting the implication. Test small counterexamples involving duplicate variables (mod-2 cancellation), unsorted row coefficients, incomplete variable coverage, empty and redundant rows, and variable-index bounds. If the statement is false as written, record the minimal counterexample and strengthen the certified-affine representation contract rather than silently assuming the missing property.

This ledger is the durable progress record for subsequent work; keep draft PR #121 linked to it.
