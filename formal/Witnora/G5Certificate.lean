import Witnora.SparseParity

/-!
# Certificate-only G5 contradiction checking

A derivation is a finite tree of referenced input rows and row XORs. The
checker never enumerates assignments or calls the bounded SAT oracle.
It proves UNSAT of the source CNF when a separate sound-extraction contract
shows that every CNF model satisfies the input rows.

This expression-tree format is a simple verified certificate format; adapting
the actual Python indexed trace to a shared DAG remains separate work.
-/

namespace Witnora.G5Certificate

open Witnora.G5Trace
open Witnora.SparseParity
open Witnora.Affine

inductive Derivation where
  | input (row : Row)
  | xor (left right : Derivation)
  deriving Repr

def derive (inputs : List Row) : Derivation → Option Row
  | .input row =>
      if row ∈ inputs then some row else none
  | .xor left right => do
      let l ← derive inputs left
      let r ← derive inputs right
      return xorRow l r

def RowHolds (bound : Nat) (r : Row) (a : Nat → Bool) : Prop :=
  sparseParity bound r.coefficients a = r.rhs

theorem xorRow_holds (bound : Nat) (left right : Row) (a : Nat → Bool)
    (hl : RowHolds bound left a) (hr : RowHolds bound right a) :
    RowHolds bound (xorRow left right) a := by
  unfold RowHolds at *
  change sparseParity bound (xorCoefficients left.coefficients right.coefficients) a =
    Bool.xor left.rhs right.rhs
  rw [sparseParity_xor, hl, hr]

theorem derive_sound (bound : Nat) (inputs : List Row)
    (d : Derivation) (r : Row)
    (hderive : derive inputs d = some r)
    (a : Nat → Bool)
    (hinput : ∀ row, row ∈ inputs → RowHolds bound row a) :
    RowHolds bound r a := by
  induction d generalizing r with
  | input row =>
      by_cases hmem : row ∈ inputs
      · simp [derive, hmem] at hderive
        cases hderive
        exact hinput row hmem
      · simp [derive, hmem] at hderive
  | xor left right ihl ihr =>
      cases hl : derive inputs left with
      | none => simp [derive, hl] at hderive
      | some l =>
          cases hr : derive inputs right with
          | none => simp [derive, hl, hr] at hderive
          | some rr =>
              simp [derive, hl, hr] at hderive
              cases hderive
              exact xorRow_holds bound l rr a
                (ihl l hl) (ihr rr hr)

theorem xorFold_false (bound : Nat) :
    xorFold bound (fun _ => false) = false := by
  induction bound with
  | zero => rfl
  | succ n ih => simp [xorFold, ih]

theorem sparseParity_empty (bound : Nat) (a : Nat → Bool) :
    sparseParity bound [] a = false := by
  simp [sparseParity, xorFold_false]

def checkContradiction (inputs : List Row) (d : Derivation) : Bool :=
  match derive inputs d with
  | none => false
  | some r => r.coefficients.isEmpty && r.rhs

/-- The certificate checker is sound for all assignments without search.
The source CNF must soundly entail the certified input equations. -/
theorem checkContradiction_unsat (bound : Nat)
    (cnfHolds : (Nat → Bool) → Prop)
    (inputs : List Row) (d : Derivation)
    (hextract : ∀ a, cnfHolds a →
      ∀ row, row ∈ inputs → RowHolds bound row a)
    (hcheck : checkContradiction inputs d = true) :
    ¬ ∃ a, cnfHolds a := by
  intro hex
  rcases hex with ⟨a, hcnf⟩
  unfold checkContradiction at hcheck
  cases hder : derive inputs d with
  | none => simp [hder] at hcheck
  | some r =>
      simp [hder] at hcheck
      have hrow := derive_sound bound inputs d r hder a (hextract a hcnf)
      have hempty : r.coefficients = [] := by
        cases hcoeff : r.coefficients with
        | nil => rfl
        | cons x xs => simp [hcoeff] at hcheck
      have hrhs : r.rhs = true := by
        simpa [hempty] using hcheck
      unfold RowHolds at hrow
      rw [hempty, sparseParity_empty, hrhs] at hrow
      cases hrow

/-- Genuine contradiction from two conflicting input rows. -/
example :
    checkContradiction
      [⟨[1], true⟩, ⟨[1], false⟩]
      (.xor (.input ⟨[1], true⟩) (.input ⟨[1], false⟩)) = true := by decide

/-- A fabricated contradiction cannot be introduced as an input row. -/
example :
    checkContradiction []
      (.input ⟨[], true⟩) = false := by decide

/-- Two equal affine rows cancel to the tautology, not a contradiction. -/
example :
    checkContradiction [⟨[2], true⟩]
      (.xor (.input ⟨[2], true⟩) (.input ⟨[2], true⟩)) = false := by decide

#print axioms Witnora.G5Certificate.derive_sound
#print axioms Witnora.G5Certificate.checkContradiction_unsat

end Witnora.G5Certificate
