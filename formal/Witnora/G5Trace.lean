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
  (left.filter (fun x => !right.contains x)) ++
  (right.filter (fun x => !left.contains x))

def xorRow (a b : Row) : Row :=
  ⟨xorCoefficients a.coefficients b.coefficients, Bool.xor a.rhs b.rhs⟩

def applyStep (rows : List Row) : Step → Option (List Row)
  | .swap a b => do
      let ra ← rows[a]?
      let rb ← rows[b]?
      return (rows.set a rb).set b ra
  | .addXor target source => do
      let rt ← rows[target]?
      let rs ← rows[source]?
      return rows.set target (xorRow rt rs)

def replay (rows : List Row) : List Step → Option (List Row)
  | [] => some rows
  | op :: rest => do
      let next ← applyStep rows op
      replay next rest

def hasContradiction (rows : List Row) : Bool :=
  rows.any (fun r => r.coefficients.isEmpty && r.rhs)

/-- An accepted bounded UNSAT trace has the claimed replay, a contradiction,
and independently verified unsatisfiability of the actual original CNF. -/
def acceptsUnsat
    (n : Nat) (original : CNF) (initial : List Row)
    (steps : List Step) (finalRows : List Row) : Bool :=
  (replay initial steps == some finalRows) &&
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
    exact (Bool.and_eq_true.mp h).2
  exact isUnsat_sound_for_all n original hunsat bits hlen

#print axioms Witnora.G5Trace.acceptsUnsat_sound

end Witnora.G5Trace
