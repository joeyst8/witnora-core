import Witnora.Concrete

/-!
Executable replay of G5's SWAP_ROWS and ADD_ROW_XOR trace shape.
This bounded checker independently checks UNSAT of the original CNF by
exhaustive enumeration. Thus its theorem does *not* depend on the row
operations being semantically correct; a future scalable checker must prove
their sparse-row semantics and CNF-to-XOR extraction separately.
-/
namespace Witnora.G5Trace
open Witnora.Concrete

structure Row where
  coefficients : List Nat
  rhs : Bool
  deriving DecidableEq, Repr

inductive Step where
  | swap (a b : Nat)
  | addXor (target source : Nat)
  deriving DecidableEq, Repr

def xorCoefficients (left right : List Nat) : List Nat :=
  (left.filter (fun x => decide (x ∉ right))) ++
  (right.filter (fun x => decide (x ∉ left)))

/-- The concrete sparse coefficient update has exactly the support of the
GF(2) symmetric difference (for all indices, not merely tested examples). -/
theorem mem_xorCoefficients (left right : List Nat) (v : Nat) :
    v ∈ xorCoefficients left right ↔
      (v ∈ left ∧ v ∉ right) ∨ (v ∈ right ∧ v ∉ left) := by
  simp [xorCoefficients]

def xorRow (a b : Row) : Row :=
  ⟨xorCoefficients a.coefficients b.coefficients, Bool.xor a.rhs b.rhs⟩

def applyStep (rows : List Row) : Step → Option (List Row)
  | .swap a b => do
      let ra ← rows[a]?
      let rb ← rows[b]?
      return (rows.set a rb).set b ra
  | .addXor target source => do
      if target == source then none else pure ()
      let rt ← rows[target]?
      let rs ← rows[source]?
      return rows.set target (xorRow rt rs)

/-- Executable indexed SWAP_ROWS matches its specification for every
list, legal pair of indices and row values. -/
theorem applyStep_swap_exact (rows : List Row) (a b : Nat) (ra rb : Row)
    (ha : rows[a]? = some ra) (hb : rows[b]? = some rb) :
    applyStep rows (.swap a b) = some ((rows.set a rb).set b ra) := by
  simp [applyStep, ha, hb]

/-- Executable indexed ADD_ROW_XOR matches its specification when the source
and target indices differ and both rows exist. -/
theorem applyStep_addXor_exact (rows : List Row) (target source : Nat)
    (rt rs : Row) (hneq : target ≠ source)
    (ht : rows[target]? = some rt) (hs : rows[source]? = some rs) :
    applyStep rows (.addXor target source) =
      some (rows.set target (xorRow rt rs)) := by
  simp [applyStep, hneq, ht, hs]

def replay (rows : List Row) : List Step → Option (List Row)
  | [] => some rows
  | op :: rest => do
      let next ← applyStep rows op
      replay next rest

def wellFormedRow (n : Nat) (r : Row) : Bool :=
  (r.coefficients.length == r.coefficients.eraseDups.length) &&
  r.coefficients.all (fun v => decide (0 < v) && decide (v ≤ n))

def sameRow (a b : Row) : Bool :=
  (a.rhs == b.rhs) && (a.coefficients.length == b.coefficients.length) &&
  (a.coefficients.length == a.coefficients.eraseDups.length) &&
  (b.coefficients.length == b.coefficients.eraseDups.length) &&
  a.coefficients.all (fun x => b.coefficients.contains x) &&
  b.coefficients.all (fun x => a.coefficients.contains x)

def sameRows (a b : List Row) : Bool :=
  (a.length == b.length) && (List.zipWith sameRow a b).all id

/-- Independently check each intermediate row-table snapshot emitted by Python.
The snapshots must correspond to the actual indexed update at every step. -/
def checkSnapshots (rows : List Row) : List Step → List (List Row) → Bool
  | [], [] => true
  | step :: steps, snapshot :: snapshots =>
      match applyStep rows step with
      | none => false
      | some actual =>
          sameRows actual snapshot && checkSnapshots actual steps snapshots
  | _, _ => false

def hasContradiction (rows : List Row) : Bool :=
  rows.any (fun r => r.coefficients.isEmpty && r.rhs)

/-- An accepted bounded UNSAT trace has the claimed replay, a contradiction,
and independently verified unsatisfiability of the actual original CNF. -/
def acceptsUnsat
    (n : Nat) (original : CNF) (initial : List Row)
    (steps : List Step) (finalRows : List Row) : Bool :=
  initial.all (wellFormedRow n) &&
  finalRows.all (wellFormedRow n) &&
  (match replay initial steps with
    | none => false
    | some actual => sameRows actual finalRows) &&
  hasContradiction finalRows &&
  isUnsat n original

theorem acceptsUnsat_sound
    (n : Nat) (original : CNF) (initial : List Row)
    (steps : List Step) (finalRows : List Row)
    (h : acceptsUnsat n original initial steps finalRows = true)
    (bits : List Bool) (hlen : bits.length = n) :
    cnfTrue bits original = false := by
  have hunsat : isUnsat n original = true := by
    unfold acceptsUnsat at h
    simp at h
    exact h.2
  exact isUnsat_sound_for_all n original hunsat bits hlen

#print axioms Witnora.G5Trace.applyStep_swap_exact
#print axioms Witnora.G5Trace.applyStep_addXor_exact
#print axioms Witnora.G5Trace.mem_xorCoefficients
#print axioms Witnora.G5Trace.acceptsUnsat_sound

end Witnora.G5Trace
