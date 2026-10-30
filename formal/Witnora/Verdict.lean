import Witnora.Concrete

/-!
A small executable verdict checker with a Lean theorem about its acceptance.
The checker reevaluates the *original* CNF instead of trusting a Python status.
It is exponential and intended for bounded G5/G14 regression certificates;
this is not a polynomial-time verifier of arbitrary UNSAT certificates.
-/

namespace Witnora.Verdict

open Witnora.Concrete

/-- true means an SAT claim; false means an UNSAT claim. -/
def accepts (n : Nat) (original : CNF) (claimedSat : Bool) : Bool :=
  if claimedSat then isSat n original else isUnsat n original

/-- An accepted UNSAT verdict rules out every length-n model. -/
theorem accepted_unsat
    (n : Nat) (original : CNF)
    (h : accepts n original false = true)
    (bits : List Bool) (hlen : bits.length = n) :
    cnfTrue bits original = false := by
  exact isUnsat_sound_for_all n original (by simpa [accepts] using h) bits hlen

/-- An accepted SAT verdict provides a witness in the exhaustive enumeration. -/
theorem accepted_sat
    (n : Nat) (original : CNF)
    (h : accepts n original true = true) :
    ∃ bits, bits ∈ allBits n ∧ cnfTrue bits original = true := by
  simp only [accepts, if_true, isSat] at h
  exact List.any_eq_true.mp h

#print axioms Witnora.Verdict.accepted_unsat
#print axioms Witnora.Verdict.accepted_sat

end Witnora.Verdict
