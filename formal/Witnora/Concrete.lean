import Init

/-!
A tiny independent finite-model checker for concrete CNF separator outputs.
This does not trust Witnora's reported checker_status; it reevaluates the
original and all residual clauses under every total assignment up to n.
Exhaustive enumeration is exponential and only used for bounded CI fixtures.
A passing finite check does NOT verify arbitrary-size Python behavior.
-/

namespace Witnora.Concrete

abbrev Literal := Nat × Bool
abbrev CNF := List (List Literal)

def readVar (bits : List Bool) (v : Nat) : Bool :=
  (bits[v - 1]?).getD false

def litTrue (bits : List Bool) (lit : Literal) : Bool :=
  if lit.2 then readVar bits lit.1 else !(readVar bits lit.1)

def cnfTrue (bits : List Bool) (f : CNF) : Bool :=
  f.all (fun clause => clause.any (litTrue bits))

def agrees (bits : List Bool) (fixed : List (Nat × Bool)) : Bool :=
  fixed.all (fun p => readVar bits p.1 == p.2)

def allBits : Nat → List (List Bool)
  | 0 => [[]]
  | n + 1 => (allBits n).flatMap (fun xs => [false :: xs, true :: xs])

/-- Independently evaluate whether the Python-produced residual components
are equivalent to the original CNF on a particular separator branch.
No Python-produced boolean verdict is an input. -/
def checkBranch
    (n : Nat) (original : CNF)
    (fixed : List (Nat × Bool)) (components : List CNF) : Bool :=
  (allBits n).all (fun bits =>
    if agrees bits fixed then
      cnfTrue bits original == components.all (cnfTrue bits)
    else true)

/-- Soundness of the executable checker for every enumerated assignment.
This theorem is general in n and in the supplied CNFs; no assumption about
Python's reported result is used. -/
theorem checkBranch_sound
    (n : Nat) (original : CNF)
    (fixed : List (Nat × Bool)) (components : List CNF)
    (h : checkBranch n original fixed components = true)
    (bits : List Bool) (hbits : bits ∈ allBits n)
    (hag : agrees bits fixed = true) :
    cnfTrue bits original = components.all (cnfTrue bits) := by
  unfold checkBranch at h
  have hrow := List.all_eq_true.mp h bits hbits
  simp [hag] at hrow
  exact eq_of_beq hrow

#print axioms Witnora.Concrete.checkBranch_sound

end Witnora.Concrete
