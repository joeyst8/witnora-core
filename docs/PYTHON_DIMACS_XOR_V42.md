# Actual Python-generated XOR DIMACS verified by Lean (v42)

Draft PR #43. CI: https://github.com/joeyst8/witnora-core/actions/runs/41239945930

## Exact result

The generator calls Witnora's actual `xor.canonical_xor_cnf_clauses` and `XorEquation` normalization. Since the Python function returns a set, the emitter explicitly reorders that **returned set** using the bit-vector order of Lean's `Concrete.allBits`; it checks that no clause was inserted, lost or duplicated. It then creates full `p cnf N M` source ASCII bytes and emits them as Lean `List Nat` literals.

Six cases passed:
- positiveUnit
- evenPair
- oddTriple
- duplicateNormalize (raw repeated variables cancel)
- emptyTautology
- emptyContradiction (empty false clause)

For each, Lean proves `checkXorDocument source raw normalized rhs submitted = true` using ordinary `decide`, rejects a document with its first byte damaged, and derives `∀ a, signedCNFHolds submitted a ↔ parityVars raw a = rhs`.

All six exact-model-equivalence proof axiom reports: `[propext, Classical.choice, Quot.sound]`; no `Lean.ofReduceBool`. CI completed successfully. Timed Lean source verification: **1.36 seconds**, peak resident memory **928,608 KiB**.

## Limitations

This is six finite, source-bound instances from the real Python generator. It is not a universal theorem about Python's set iteration, integer coercion, formatter, or operating-system byte reads. The emitted Lean literal list is the trusted transport in these tests. The source parser supports a restricted ASCII DIMACS grammar.

The per-case document corruption replaces only the first byte, so further semantic and structural adversarial mutation coverage is warranted. No G5/G14/TC-063 UNSAT theorem follows solely from this milestone.

Next: independent larger randomized/adversarial XOR-source trials, and prioritizing the remaining G14 residual-model and TC-063 composition obligations.
