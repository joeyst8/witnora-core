import Witnora.G5IndexedExecutionInvariant

/-!
# G5 indexed execution: live reference bounds

A valid reference map only points into the row table represented by
initial rows and emitted XOR operations. This file proves the bound
survives all legal swaps and XOR updates, then lifts the invariant to
arbitrary successful source operation sequences.
-/

namespace Witnora.G5IndexedReferenceSafety

open Witnora.G5IndexedBridge
open Witnora.G5Dag

def RefsValid (initialCount : Nat) (state : State) : Prop :=
  ∀ ref ∈ state.1, ref < initialCount + state.2.length

/-- A list replacement preserves any elementwise invariant when the
    replacement itself satisfies that invariant. -/
theorem property_set (xs : List Nat) (P : Nat → Prop)
    (i replacement : Nat)
    (hxs : ∀ x ∈ xs, P x) (hr : P replacement) :
    ∀ x ∈ xs.set i replacement, P x := by
  induction xs generalizing i with
  | nil =>
      intro x hx
      simp at hx
  | cons head tail ih =>
      cases i with
      | zero =>
          intro x hx
          have hh : x = replacement ∨ x ∈ tail := by
            simpa [List.set] using hx
          rcases hh with heq | ht
          · subst x
            exact hr
          · exact hxs x (by simp [ht])
      | succ j =>
          intro x hx
          have hh : x = head ∨ x ∈ tail.set j replacement := by
            simpa [List.set] using hx
          rcases hh with heq | ht
          · subst x
            exact hxs head (by simp)
          · have htail : ∀ y ∈ tail, P y := by
              intro y hy
              exact hxs y (by simp [hy])
            exact ih j htail x ht

/-- Every legal indexed operation preserves live row-reference validity.
    The new target reference points at the row just appended. -/
theorem step_preserves_refs_valid
    (initialCount : Nat) (state next : State) (op : Operation)
    (hvalid : RefsValid initialCount state)
    (hstep : step state op = some next) :
    RefsValid initialCount next := by
  cases op with
  | swapRows i j =>
      cases hi : state.1[i]? with
      | none =>
          simp [step, hi] at hstep
      | some left =>
          cases hj : state.1[j]? with
          | none =>
              simp [step, hi, hj] at hstep
          | some right =>
              simp [step, hi, hj] at hstep
              cases hstep
              unfold RefsValid at hvalid ⊢
              have hl := hvalid left
                (getElem?_mem state.1 i left hi)
              have hr := hvalid right
                (getElem?_mem state.1 j right hj)
              exact property_set _ _ j left
                (property_set _ _ i right hvalid hr) hl
  | addRowXor target source =>
      by_cases heq : target = source
      · subst source
        simp [step] at hstep
      · have hneq : (target == source) = false :=
          decide_eq_false heq
        cases hi : state.1[target]? with
        | none =>
            simp [step, hneq, hi] at hstep
        | some left =>
            cases hj : state.1[source]? with
            | none =>
                simp [step, hneq, hi, hj] at hstep
            | some right =>
                simp [step, hneq, hi, hj] at hstep
                cases hstep
                unfold RefsValid at hvalid ⊢
                have hnew : initialCount + state.2.length <
                    initialCount + (state.2 ++ [(left, right)]).length := by
                  simp
                have hprev : ∀ ref ∈ state.1,
                    ref < initialCount + (state.2 ++ [(left, right)]).length := by
                  intro ref hm
                  have hh := hvalid ref hm
                  have hb : initialCount + state.2.length ≤
                      initialCount + (state.2 ++ [(left, right)]).length := by
                    simp
                  exact Nat.lt_of_lt_of_le hh hb
                exact property_set _ _ target
                  (initialCount + state.2.length) hprev hnew

/-- The reference table starts valid: every element of range(n) is an
    existing row index in the initial n-row table. -/
theorem initial_refs_valid (n : Nat) :
    RefsValid n (List.range n, []) := by
  intro ref href
  simpa using List.mem_range.mp href

/-- Valid reference bounds persist through every accepted operation. -/
theorem foldlM_preserves_refs_valid
    (n : Nat) (operations : List Operation)
    (state next : State)
    (hvalid : RefsValid n state)
    (h : operations.foldlM step state = some next) :
    RefsValid n next := by
  induction operations generalizing state with
  | nil =>
      simp at h
      cases h
      exact hvalid
  | cons op rest ih =>
      cases hs : step state op with
      | none =>
          simp [List.foldlM_cons, hs] at h
      | some updated =>
          have hrest : rest.foldlM step updated = some next := by
            simpa [List.foldlM_cons, hs] using h
          exact ih updated (step_preserves_refs_valid n state updated op
            hvalid hs) hrest

theorem indexed_run_refs_valid
    (n : Nat) (operations : List Operation) (result : State)
    (h : operations.foldlM step (List.range n, []) =
      some result) :
    RefsValid n result :=
  foldlM_preserves_refs_valid n operations (List.range n, [])
    result (initial_refs_valid n) h

#print axioms Witnora.G5IndexedReferenceSafety.step_preserves_refs_valid
#print axioms Witnora.G5IndexedReferenceSafety.indexed_run_refs_valid

end Witnora.G5IndexedReferenceSafety
