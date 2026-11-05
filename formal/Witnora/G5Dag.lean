import Witnora.G5Certificate

/-!
# Shared-row DAG G5 certificate checking

Each operation appends the XOR of two existing rows, referenced by indices.
Proof size is linear in the operation count rather than duplicating
expression subtrees. The checker never enumerates assignments.

Source-level SWAP_ROWS operations can be represented by remapping references
during conversion to this append-only format; validating that conversion
universally remains a separate refinement obligation.
-/

namespace Witnora.G5Dag

open Witnora.G5Trace
open Witnora.G5Certificate

abbrev XorRef := Nat × Nat

def replayDag (rows : List Row) : List XorRef → Option (List Row)
  | [] => some rows
  | (i, j) :: rest => do
      let left ← rows[i]?
      let right ← rows[j]?
      replayDag (rows ++ [xorRow left right]) rest

def checkDagContradiction (inputs : List Row) (steps : List XorRef) : Bool :=
  match replayDag inputs steps with
  | none => false
  | some rows => rows.any (fun r => r.coefficients.isEmpty && r.rhs)

/-- Every successful indexed lookup returns a member of the input list. -/
theorem getElem?_mem {α : Type} (xs : List α) (i : Nat) (x : α)
    (h : xs[i]? = some x) : x ∈ xs := by
  induction xs generalizing i with
  | nil => cases i <;> simp at h
  | cons head tail ih =>
      cases i with
      | zero =>
          simp at h
          cases h
          simp
      | succ j =>
          simp at h
          exact List.mem_cons_of_mem head (ih j h)

def AllHold (bound : Nat) (rows : List Row) (a : Nat → Bool) : Prop :=
  ∀ row, row ∈ rows → RowHolds bound row a

/-- Every valid indexed DAG step extends the known equations by a logical
consequence; no assignment search is involved. -/
theorem replayDag_sound (bound : Nat) (initial : List Row)
    (steps : List XorRef) (final : List Row)
    (hreplay : replayDag initial steps = some final)
    (a : Nat → Bool)
    (hinput : AllHold bound initial a) :
    AllHold bound final a := by
  induction steps generalizing initial with
  | nil =>
      simp [replayDag] at hreplay
      cases hreplay
      exact hinput
  | cons step rest ih =>
      rcases step with ⟨i, j⟩
      cases hi : initial[i]? with
      | none => simp [replayDag, hi] at hreplay
      | some left =>
          cases hj : initial[j]? with
          | none => simp [replayDag, hi, hj] at hreplay
          | some right =>
              have hleft : RowHolds bound left a :=
                hinput left (getElem?_mem initial i left hi)
              have hright : RowHolds bound right a :=
                hinput right (getElem?_mem initial j right hj)
              have hnext : AllHold bound (initial ++ [xorRow left right]) a := by
                intro row hmem
                rcases List.mem_append.mp hmem with hprev | hnew
                · exact hinput row hprev
                · have heq : row = xorRow left right := by
                    simpa using hnew
                  subst row
                  exact xorRow_holds bound left right a hleft hright
              apply ih (initial ++ [xorRow left right])
              · simpa [replayDag, hi, hj] using hreplay
              · exact hnext

/-- A successful indexed-DAG contradiction certificate proves UNSAT under
the explicitly stated sound-extraction contract. -/
theorem checkDagContradiction_unsat (bound : Nat)
    (cnfHolds : (Nat → Bool) → Prop)
    (inputs : List Row) (steps : List XorRef)
    (hextract : ∀ a, cnfHolds a → AllHold bound inputs a)
    (hcheck : checkDagContradiction inputs steps = true) :
    ¬ ∃ a, cnfHolds a := by
  rintro ⟨a, hmodel⟩
  unfold checkDagContradiction at hcheck
  cases hrep : replayDag inputs steps with
  | none => simp [hrep] at hcheck
  | some rows =>
      have hrows := replayDag_sound bound inputs steps rows hrep a
        (hextract a hmodel)
      have hcontr : ∃ r, r ∈ rows ∧
          (r.coefficients.isEmpty && r.rhs) = true := by
        have ht : rows.any (fun r => r.coefficients.isEmpty && r.rhs) = true := by
          simpa [hrep] using hcheck
        exact List.any_eq_true.mp ht
      rcases hcontr with ⟨r, hrmem, hr⟩
      have hvalid := hrows r hrmem
      have hempty : r.coefficients = [] := by
        cases hcoeff : r.coefficients with
        | nil => rfl
        | cons x xs => simp [hcoeff] at hr
      have hrhs : r.rhs = true := by
        simpa [hempty] using hr
      unfold RowHolds at hvalid
      rw [hempty, sparseParity_empty, hrhs] at hvalid
      cases hvalid

example :
    checkDagContradiction
      [⟨[1], true⟩, ⟨[1], false⟩]
      [(0, 1)] = true := by decide

example :
    checkDagContradiction
      [⟨[1], true⟩]
      [(0, 9)] = false := by decide

#print axioms Witnora.G5Dag.replayDag_sound
#print axioms Witnora.G5Dag.checkDagContradiction_unsat

end Witnora.G5Dag
