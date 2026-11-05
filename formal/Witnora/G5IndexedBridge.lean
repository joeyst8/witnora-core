import Witnora.G5Dag

/-!
# Trusted indexed G5 operation compiler

The source certificate contains a mutable indexed trace. This executable
Lean compiler translates swaps to reference-map updates and XOR operations
to append-only DAG references. The production G5 gate kernel-checks the
compiler result against the Python-emitted DAG for every accepted trace.

This establishes correspondence for checked executions; it does not prove
universal correctness of CPython's execution of the generator.
-/

namespace Witnora.G5IndexedBridge

inductive Operation where
  | swapRows (a b : Nat)
  | addRowXor (target source : Nat)
  deriving DecidableEq, Repr

abbrev State := List Nat × List Witnora.G5Dag.XorRef

def step (state : State) : Operation → Option State
  | .swapRows a b => do
      let refs := state.1
      let left ← refs[a]?
      let right ← refs[b]?
      return ((refs.set a right).set b left, state.2)
  | .addRowXor target source => do
      let refs := state.1
      if target == source then none
      else
        let left ← refs[target]?
        let right ← refs[source]?
        let next := refs.length + state.2.length
        return (refs.set target next, state.2 ++ [(left, right)])

def compile (initialRows : Nat) (operations : List Operation) :
    Option (List Witnora.G5Dag.XorRef) := do
  let final ← operations.foldlM step (List.range initialRows, [])
  return final.2

example : compile 2
    [.swapRows 0 1, .addRowXor 0 1, .swapRows 0 1,
      .addRowXor 0 1] = some [(1, 0), (0, 2)] := by decide

example : compile 1 [.addRowXor 0 0] = none := by decide
example : compile 1 [.swapRows 0 3] = none := by decide

end Witnora.G5IndexedBridge
