import Witnora.G5IndexedExecutionInvariant

/-!
# Python-style indexed G5 compiler model versus the verified Lean compiler

The production Python `_compile_dag` loop maintains:
  * `refs = list(range(len(rows)))`
  * `next_id = len(refs)`
  * a list of compiled XOR reference pairs.

SWAP_ROWS remaps two live slots. ADD_ROW_XOR appends exactly one pair,
sets the target slot to `next_id`, then increments `next_id`.

This Lean specification models that algorithm on *validated* integer
operations. It is deliberately separate from G5IndexedBridge.compile:
one uses an explicit mutable next_id, the other computes the next row ID
from live-ref arity plus DAG length.

The theorem below is universal for the mathematical Python-style model.
It does not prove that the CPython interpreter implements this model,
nor that the Python JSON/Lean-text serializers are universally correct.
-/

namespace Witnora.TC063PythonCompilerModel

open Witnora.G5IndexedBridge
open Witnora.G5Dag

structure PyState where
  refs : List Nat
  nextId : Nat
  pairs : List XorRef
  deriving Repr

def PyState.start (n : Nat) : PyState :=
  ⟨List.range n, n, []⟩

/-- Independent Python-like interpretation using an explicit next_id. -/
def pyStep (state : PyState) : Operation → Option PyState
  | .swapRows a b => do
      let left ← state.refs[a]?
      let right ← state.refs[b]?
      return { state with refs :=
        (state.refs.set a right).set b left }
  | .addRowXor target source => do
      if target == source then none
      else
        let targetRef ← state.refs[target]?
        let sourceRef ← state.refs[source]?
        return {
          refs := state.refs.set target state.nextId
          nextId := state.nextId + 1
          pairs := state.pairs ++ [(targetRef, sourceRef)]
        }

def pyCompile (n : Nat) (operations : List Operation) :
    Option (List XorRef) := do
  let result ← operations.foldlM pyStep (PyState.start n)
  return result.pairs

/-- next_id is exactly where the next appended DAG row belongs. -/
def PyInvariant (state : PyState) : Prop :=
  state.nextId = state.refs.length + state.pairs.length

theorem start_invariant (n : Nat) : PyInvariant (PyState.start n) := by
  simp [PyInvariant, PyState.start]

/-- One successful Python-style instruction keeps the explicit next_id
    synchronized with the trusted compiler's implicit next index.
    The resulting live-reference updates and DAG pairs agree exactly. -/
theorem pyStep_refines_compiler
    (state next : PyState) (op : Operation)
    (hInv : PyInvariant state)
    (hStep : pyStep state op = some next) :
    PyInvariant next ∧
      step (state.refs, state.pairs) op =
        some (next.refs, next.pairs) := by
  cases op with
  | swapRows a b =>
      cases ha : state.refs[a]? with
      | none => simp [pyStep, ha] at hStep
      | some left =>
          cases hb : state.refs[b]? with
          | none => simp [pyStep, ha, hb] at hStep
          | some right =>
              simp [pyStep, ha, hb] at hStep
              subst next
              constructor
              · simpa [PyInvariant] using hInv
              · simp [step, ha, hb]
  | addRowXor target source =>
      by_cases hEqual : target = source
      · subst source
        simp [pyStep] at hStep
      · have hFalse : (target == source) = false :=
          decide_eq_false hEqual
        cases ha : state.refs[target]? with
        | none => simp [pyStep, hFalse, ha] at hStep
        | some targetRef =>
            cases hb : state.refs[source]? with
            | none => simp [pyStep, hFalse, ha, hb] at hStep
            | some sourceRef =>
                simp [pyStep, hFalse, ha, hb] at hStep
                subst next
                constructor
                · simp [PyInvariant, List.length_append] at hInv ⊢
                  omega
                · simpa [step, hFalse, ha, hb, PyInvariant] using
                    (show
                      step (state.refs, state.pairs)
                        (.addRowXor target source) =
                        some
                          (state.refs.set target state.nextId,
                            state.pairs ++ [(targetRef, sourceRef)]) by
                      simp [step, hFalse, ha, hb, PyInvariant] 
                      rw [hInv])

/-- Arbitrary successful Python-style operation lists agree with the
    trusted indexed compiler, including all intermediate ref updates. -/
theorem pyFold_refines_compiler
    (operations : List Operation)
    (state result : PyState)
    (hInv : PyInvariant state)
    (hRun : operations.foldlM pyStep state = some result) :
    PyInvariant result ∧
      operations.foldlM step (state.refs, state.pairs) =
        some (result.refs, result.pairs) := by
  induction operations generalizing state with
  | nil =>
      simp at hRun
      cases hRun
      exact ⟨hInv, rfl⟩
  | cons op rest ih =>
      cases hs : pyStep state op with
      | none => simp [List.foldlM_cons, hs] at hRun
      | some updated =>
          have hRest : rest.foldlM pyStep updated = some result := by
            simpa [List.foldlM_cons, hs] using hRun
          obtain ⟨hUpdatedInv, hBridge⟩ :=
            pyStep_refines_compiler state updated op hInv hs
          obtain ⟨hResultInv, hRestBridge⟩ :=
            ih updated hUpdatedInv hRest
          refine ⟨hResultInv, ?_⟩
          simpa [List.foldlM_cons, hBridge] using hRestBridge

/-- Universal successful-execution refinement of the explicit-next-ID
    Python algorithm model to the production verified Lean compiler. -/
theorem pyCompile_success_refines
    (n : Nat) (ops : List Operation) (pairs : List XorRef)
    (h : pyCompile n ops = some pairs) :
    compile n ops = some pairs := by
  unfold pyCompile at h
  cases hRun : ops.foldlM pyStep (PyState.start n) with
  | none => simp [hRun] at h
  | some result =>
      simp [hRun] at h
      subst pairs
      obtain ⟨_, hBridge⟩ := pyFold_refines_compiler
        ops (PyState.start n) result (start_invariant n) hRun
      simp [compile, PyState.start] at hBridge ⊢
      simpa [hBridge]

/-- A swap changes only reference mapping and emits no XOR DAG pair. -/
example : pyCompile 2
    [.swapRows 0 1, .addRowXor 0 1] =
      some [(1, 0)] := by decide

/-- Out-of-range references and self-XORs fail closed. -/
example : pyCompile 1 [.swapRows 0 2] = none := by decide
example : pyCompile 1 [.addRowXor 0 0] = none := by decide

#print axioms Witnora.TC063PythonCompilerModel.start_invariant
#print axioms Witnora.TC063PythonCompilerModel.pyStep_refines_compiler
#print axioms Witnora.TC063PythonCompilerModel.pyFold_refines_compiler
#print axioms Witnora.TC063PythonCompilerModel.pyCompile_success_refines


/-- The Python-style algorithm and the verified compiler reject exactly
    the same invalid single operations, independent of next_id. -/
theorem pyStep_fails_iff_compiler_fails
    (state : PyState) (op : Operation) :
    pyStep state op = none ↔
      step (state.refs, state.pairs) op = none := by
  cases op with
  | swapRows a b =>
      cases ha : state.refs[a]? <;>
      cases hb : state.refs[b]? <;>
      simp [pyStep, step, ha, hb]
  | addRowXor target source =>
      by_cases heq : target = source
      · subst source
        simp [pyStep, step]
      · have hFalse : (target == source) = false :=
          decide_eq_false heq
        cases ha : state.refs[target]? <;>
        cases hb : state.refs[source]? <;>
        simp [pyStep, step, hFalse, ha, hb]

/-- The complete Option result agrees across every Python-style run:
    both accepted traces and rejected traces correspond to Lean's source
    compiler, provided next_id is synchronized initially. -/
theorem pyFold_exact
    (operations : List Operation)
    (state : PyState)
    (hInv : PyInvariant state) :
    (operations.foldlM pyStep state).map
      (fun result => (result.refs, result.pairs)) =
    operations.foldlM step (state.refs, state.pairs) := by
  induction operations generalizing state with
  | nil => rfl
  | cons op rest ih =>
      cases hs : pyStep state op with
      | none =>
          have hReject :=
            (pyStep_fails_iff_compiler_fails state op).mp hs
          simp [List.foldlM_cons, hs, hReject]
      | some updated =>
          obtain ⟨hUpdatedInv, hBridge⟩ :=
            pyStep_refines_compiler state updated op hInv hs
          simpa [List.foldlM_cons, hs, hBridge] using
            ih updated hUpdatedInv

/-- Full universal equivalence of the two *formal* compilers, including
    rejected inputs; neither successful-execution nor UNSAT assumptions. -/
theorem pyCompile_eq_compiler
    (n : Nat) (ops : List Operation) :
    pyCompile n ops = compile n ops := by
  have hFold := pyFold_exact ops (PyState.start n) (start_invariant n)
  cases hp : ops.foldlM pyStep (PyState.start n) with
  | none =>
      simp only [PyState.start] at hp
      have hc : ops.foldlM step (List.range n, []) = none := by
        simpa [PyState.start, hp] using hFold.symm
      simp [pyCompile, compile, PyState.start, hp, hc]
  | some result =>
      simp only [PyState.start] at hp
      have hc : ops.foldlM step (List.range n, []) =
          some (result.refs, result.pairs) := by
        simpa [PyState.start, hp] using hFold.symm
      simp [pyCompile, compile, PyState.start, hp, hc]

#print axioms Witnora.TC063PythonCompilerModel.pyStep_fails_iff_compiler_fails
#print axioms Witnora.TC063PythonCompilerModel.pyFold_exact
#print axioms Witnora.TC063PythonCompilerModel.pyCompile_eq_compiler

end Witnora.TC063PythonCompilerModel
