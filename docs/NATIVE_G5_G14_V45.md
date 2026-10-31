# Native Python G5 traces inside Python-generated G14 (v45)

Draft PR #46. Successful CI: https://github.com/joeyst8/witnora-core/actions/runs/41240954712

## Verified pipeline

The Python emitter constructs an UNSAT CNF of eight guarded clauses from actual `_guarded_xor_equation` calls on two-variable parity constraints with both RHS values. The selector `x1` chooses the two guarded branches. In each branch, Python's actual `_component_dicts` and `_condition_by_separator` produce the residual four-clause contradiction encoding `x2 XOR x3 = 0` AND `x2 XOR x3 = 1`.

Instead of synthesizing a unit G5 proof, the emitter now calls **`operator_genesis.build_affine_residue_certificate`**, which uses the actual native exact-CNF extraction and GF(2) elimination trace. It requires `AFFINE_RESIDUE_UNSAT_NATIVE_CERTIFIED` and `AFFINE_RESIDUE_CERTIFICATE_VERIFIED`, obtains the actual initial-row and `row_operations` trace, and compiles references through the existing `lean_g5_gate._compile_dag` helper.

The emitted Lean source checks the actual source DIMACS bytes, raw token stream, branch enumeration, exact Python-proposed residual components, selected branches, and the real native G5 rows/compiled operations. `G14ConcreteBridge.checked_ascii_dimacs_g14_unsat` derives UNSAT of the source signed CNF.

Lean's named UNSAT theorem depends only on `[propext, Classical.choice, Quot.sound]`. CI passed without `sorry`, user axioms, unsafe declarations or native evaluation. Measured Lean run: **0.53 seconds**, peak resident memory **327,840 KiB**.

## Boundary

This is an actual native trace on a bounded specially constructed G14 instance. Lean validates its mathematical meaning, but the Python-to-Lean emitter and runtime are not universally refined. It is neither TC-063 nor a general performance result; the proof does not imply original P-vs-NP claims.

Next: multiple structured UNSAT G14 cases with varying branches/components and authentic native G5 traces; independent adversarial changes and source-hash binding; then progressively replace fixtures with target TC-063 data.
