# Witnora-Core v0.0.1 Release Notes

## Theorem Implemented

Witnora-Core v0.0.1 implements the Witnora 2-SAT Collapse Theorem v1 prototype for a fixed constant `c`.

The implementation applies a deterministic simplifier `S` with:

- Unit Propagation
- Pure Literal Elimination
- Subsumption
- Blocked Clause Elimination
- Component Decomposition

After simplification, each incidence-graph component is solved independently by one of:

- internal 2-SAT SCC solving for 2-CNF components;
- exact bounded-width elimination-order search over the primal graph for `c <= 4`;
- variable elimination along a verified elimination order.

SAT results reconstruct a witness for the original CNF and verify that assignment against the original formula. UNSAT results are produced through replayable transformations and a final checkable conflict or 2-SAT SCC contradiction. If no permitted collapse path is found, the solver returns only `NO_COLLAPSE_FOUND_UNDER_CURRENT_GRAMMAR_AND_C`.

## Tests Passed

The v0.0.1 test suite passed with 19 tests.

Required pass markers:

- `BCE_RECONSTRUCTION_PASS`
- `TREEWIDTH_COLLAPSE_PASS`
- `RECONSTRUCTION_PASS`
- `UNSAT_PASS`
- `NO_COLLAPSE_PASS`
- `DETERMINISM_PASS`
- `COMPONENT_SOLVE_PASS`
- `COMPONENT_NO_COLLAPSE_PASS`
- `NON_BLOCKED_BCE_REJECT_PASS`
- `BCE_FORCED_REPAIR_PASS`
- `VE_SIGN_RECONSTRUCTION_PASS`
- `VE_CONFLICT_DETECTION_PASS`
- `CROSS_COMPONENT_SPLIT_REJECT_PASS`
- `EMPTY_FORMULA_SAT_PASS`
- `TAUTOLOGY_NORMALIZATION_PASS`
- `ABSENT_DIMACS_VARIABLE_PASS`
- `C_ZERO_PASS`
- `NO_BRUTE_FORCE_NO_COLLAPSE_PASS`
- `VERIFIER_NEGATIVE_TESTS_PASS`

## Known Limitations

- Exact bounded-width search is intended for small fixed `c`; v0 enforces `c <= 4`.
- No Bodlaender-style linear-time treewidth algorithm is implemented.
- No LRAT or FRAT proof output is emitted.
- The verifier is internal to the Python implementation and is not an independently checked external proof format.
- Variable elimination may grow formulas quickly even when bounded by the configured width cap.
- DIMACS header variables that disappear during normalization or simplification are handled deterministically, but the solver verifies only the original clauses.
- Component solving is recursive at the component level after simplification, but v0 does not attempt advanced interleavings beyond the fixed collapse grammar.

## No P vs NP Claims

This release makes no claim that P = NP, no claim that SAT is solved in polynomial time in general, and no claim that unresolved formulas are hard.

`NO_COLLAPSE_FOUND_UNDER_CURRENT_GRAMMAR_AND_C` means only that Witnora-Core v0.0.1 did not find a certified collapse path under the implemented grammar and selected `c` budget.

The implementation does not use an external SAT solver and does not brute-force arbitrary CNF formulas.

## Next Milestones

- Add an independently checkable proof export format such as LRAT or FRAT.
- Expand certificate replay tooling and external audit utilities.
- Add more adversarial regression tests for malformed DIMACS and corrupted certificates.
- Improve bounded-treewidth search performance without weakening exact verification.
- Add richer component-level reporting and certificate inspection commands.
- Package as an installable Python distribution with versioned CLI entry points.
