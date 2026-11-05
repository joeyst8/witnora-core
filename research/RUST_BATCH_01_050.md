# Rust migration batch 01 — 50 source files

Batch starts at **48/560** CI-verified Python source files. The target is
**98/560** verified counterparts, not 50 edited files or 50 stubs. R-070 is
the first candidate, with 49 additional computational modules queued below.
Their order is provisional and can be rearranged to share Rust primitives.

## Acceptance contract

1. Implement an actual native kernel callable from the existing package.
2. Preserve the Python reference and add exact differential tests, including
   seeded random and adversarial controls suitable for the function.
3. Run compiled Rust tests and the extension's Python/native comparisons in
   GitHub Actions; do not count skipped tests as verification.
4. Mark each entry `parallel_reference` only after successful native CI and
   record the run. A partially moved module stays `partial_native_verified`.
5. Do not modify or retire the Lean trust boundary, claim a SAT breakthrough,
   or delete Python until the relevant downstream proof and release gates pass.

The 50-file target is a **batch goal, not a claim of completed migration**.
Track the exact verified count in `python_to_rust_manifest.json`.

## Batch queue

| # | Python source | State at batch creation |
|---:|---|---|
| 1 | `witnora_core/satlib_fingerprint.py` | native CI pending (R-070) |
| 2 | `witnora_core/operator_counterexamples.py` | queued |
| 3 | `witnora_core/spoke_collapse.py` | queued |
| 4 | `witnora_core/crc_independence_audit.py` | queued |
| 5 | `witnora_core/crc_conditional_independence.py` | queued |
| 6 | `witnora_core/crc_structural_independence.py` | queued |
| 7 | `witnora_core/parity_compression.py` | queued |
| 8 | `witnora_core/geometry_aware_parity.py` | queued |
| 9 | `witnora_core/separator_conditioned_solve.py` | queued |
| 10 | `witnora_core/aux_violation_tensors.py` | queued |
| 11 | `witnora_core/expression_conjecture_search.py` | queued |
| 12 | `witnora_core/verified_compression_pipeline.py` | queued |
| 13 | `witnora_core/crc_variable_elimination.py` | queued |
| 14 | `witnora_core/double_kempe_lab.py` | queued |
| 15 | `witnora_core/claim_boundary.py` | queued |
| 16 | `witnora_core/dsatur_adversarial_lab.py` | queued |
| 17 | `witnora_core/crc_orbit_oracle.py` | queued |
| 18 | `witnora_core/graph_conjecture_lab.py` | queued |
| 19 | `witnora_core/crc_defect_oracle.py` | queued |
| 20 | `witnora_core/conditional_graph_conjectures.py` | queued |
| 21 | `witnora_core/constraint_geometry.py` | queued |
| 22 | `witnora_core/crc_shannon_oracle.py` | queued |
| 23 | `witnora_core/ood_sat_families.py` | queued |
| 24 | `witnora_core/kempe_repair_lab.py` | queued |
| 25 | `witnora_core/crc_conflict_oracle.py` | queued |
| 26 | `witnora_core/color_selector_lab.py` | queued |
| 27 | `witnora_core/families.py` | queued |
| 28 | `witnora_core/crc_separator_discovery.py` | queued |
| 29 | `witnora_core/compare.py` | queued |
| 30 | `witnora_core/color_repair_lab.py` | queued |
| 31 | `witnora_core/anf_separator_conditioning.py` | queued |
| 32 | `witnora_core/structured_coloring_study.py` | queued |
| 33 | `witnora_core/experimental_operator_search.py` | queued |
| 34 | `witnora_core/crc_cutset_count.py` | queued |
| 35 | `witnora_core/anf_structured_counter.py` | queued |
| 36 | `witnora_core/rup_witness_import.py` | queued |
| 37 | `witnora_core/operator_promotion.py` | queued |
| 38 | `witnora_core/violation_image_anf.py` | queued |
| 39 | `witnora_core/exact_tensor_counting.py` | queued |
| 40 | `witnora_core/nonedge_matching_bound.py` | queued |
| 41 | `witnora_core/benchmark_artifact.py` | queued |
| 42 | `witnora_core/treewidth_audit.py` | queued |
| 43 | `witnora_core/paper_hardening.py` | queued |
| 44 | `witnora_core/partial_replay.py` | queued |
| 45 | `witnora_core/cnfgen_matrix.py` | queued |
| 46 | `witnora_core/xor.py` | queued |
| 47 | `witnora_core/tc063_theorem_hardening.py` | queued; proof-sensitive |
| 48 | `witnora_core/xor_diagnostic.py` | queued |
| 49 | `witnora_core/reproducibility_package.py` | queued |
| 50 | `witnora_core/obstruction_dual.py` | queued |

Prioritize coherent dependencies (CNF/XOR and CRC families, graph/coloring,
operator laboratories, evidence/reporting), and split proof-sensitive modules
into separate proof obligations. The batch does not authorize bypassing
required Lean or external-baseline checks.
