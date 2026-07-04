# Witnora-Core v0.0.1

Witnora-Core v0.0.1 is a certified collapse-path prototype for CNF SAT formulas. It is not a general SAT solver and makes no `P = NP` claim. Its primary artifact is a deterministic, replay-verifiable collapse path: a sequence of satisfiability-preserving transformations, tractable solves, SAT witness reconstruction, and final verification against the original CNF.

No external SAT solver, GNN, MCTS, LRAT/FRAT emitter, or brute-force solver for arbitrary formulas is included.

## Implemented Theorem Scope

For a fixed `c` with v0 support for `0 <= c <= 4`, Witnora implements the accepted 2-SAT collapse theorem route:

- apply a fixed deterministic simplifier `S`
- split disconnected incidence-graph components
- solve each component if it is 2-CNF or has primal graph treewidth at most `c`
- reconstruct a full original assignment for SAT results
- replay-verify the logged certificate

`S` is deterministic by implementation order, not mathematically canonical.

## Collapse Routes

The deterministic simplifier applies, in order:

- Unit Propagation
- Pure Literal Elimination
- Subsumption
- Blocked Clause Elimination
- Component Decomposition

Component decomposition uses the incidence graph. Bounded-width reasoning uses the primal graph only.

## COMPONENTS_SOLVED

If a formula splits into more than one component and every component is solved, the full result uses:

```json
"final_class": "COMPONENTS_SOLVED"
```

The output includes:

```json
"component_results": [
  {
    "component_id": "0",
    "status": "SAT",
    "final_class": "2SAT",
    "formula_hash": "...",
    "assignment": {"1": true}
  }
]
```

Status priority is:

- if any component is `UNSAT`, the full formula is `UNSAT`
- else if any component is `NO_COLLAPSE_FOUND_UNDER_CURRENT_GRAMMAR_AND_C`, the full formula returns that no-collapse status
- else all components are `SAT`, so the full formula is `SAT`

The runner never returns partial SAT for a failed component set.

## NO_COLLAPSE_FOUND Is Not HARD

`NO_COLLAPSE_FOUND_UNDER_CURRENT_GRAMMAR_AND_C` means only that the implemented grammar and current `c` budget did not find a certified collapse route. It is not a hardness claim and must not be read as `HARD`, `UNKNOWN`, or probabilistic UNSAT.

## certificate_hash

Every JSON result includes a deterministic `certificate_hash` computed from stable certificate fields:

- original formula hash
- `c`
- collapse path
- final class
- final assignment
- reconstructed original assignment
- original verification flag
- component results

Runtime stats such as `stats.time_ms` are excluded.

## SAT Reconstruction

SAT reconstruction reverses the collapse path:

- UP and PLE assign their logged literals
- SUB needs no assignment action
- BCE sets the blocked literal to true if the removed clause is falsified
- VE uses the sign-correct reconstruction rule:
  - falsified `(x or ...)` requires `x = True`
  - falsified `(not x or ...)` requires `x = False`

Remaining original variables are filled deterministically as `False`. Every SAT result must verify against the original normalized CNF.

## Verifier

The verifier replays:

- formula hashes
- UP, PLE, SUB, BCE
- incidence-graph component splits
- component assignment merges
- exact primal-treewidth order verification
- VE resolvents and width caps
- 2-SAT SCC results
- final SAT assignment or UNSAT contradiction

## Adversarial Tests

`tests/test_adversarial_correctness.py` covers:

- non-blocked BCE rejection
- forced BCE reconstruction repair
- VE sign reconstruction
- VE reconstruction conflict detection
- fake cross-component split rejection
- empty formula SAT
- tautological clause normalization
- absent DIMACS variables
- `c=0` simplification behavior
- no-collapse without brute-force fallback
- verifier negative tests for corrupted hashes, BCE, VE, CD, and final assignment

## Run Tests

```bash
python -m unittest discover
```

Expected pass markers include:

- `BCE_RECONSTRUCTION_PASS`
- `TREEWIDTH_COLLAPSE_PASS`
- `RECONSTRUCTION_PASS`
- `UNSAT_PASS`
- `NO_COLLAPSE_PASS`
- `DETERMINISM_PASS`
- `COMPONENT_SOLVE_PASS`
- `COMPONENT_NO_COLLAPSE_PASS`
- adversarial markers from `tests/test_adversarial_correctness.py`

## Run Examples

```bash
python -m witnora_core.runner examples/bce_demo.dimacs --c 2
python -m witnora_core.runner examples/treewidth_demo.dimacs --c 2
python -m witnora_core.runner examples/treewidth_demo.dimacs --c 1
python -m witnora_core.runner examples/multi_component_demo.dimacs --c 2
python -m witnora_core.runner examples/unsat_demo.dimacs --c 2
```
