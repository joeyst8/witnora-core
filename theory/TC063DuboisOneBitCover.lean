import Dubois20SourceUnsat

/-!
  TC-063 G14 single-bit exact-substitution / UNSAT-cover bridge.

  This specializes one Boolean split, not the SAF(c,r) separator theorem:
  no claim is made that {DIMACS variable 1} separates the primal graph,
  or that independently solved affine residual components have been found.

  Variable 1 (bit 0) occurs in exactly sourceGroup0 and sourceGroup1.
  The other 38 source-clause groups are retained unchanged. Branch refutations
  use the kernel-checked G5 source CNF-to-XOR and trace certificate, not an
  assumed solver result; the source DIMACS parser boundary remains external.
-/

namespace Witnora.TC063

open Witnora.Dubois20

-- General G14 Boolean cover rule: exact branch semantics + a refutation of
-- every branch imply a refutation of the original proposition.
theorem two_branch_unsat_cover
    {Model : Type} (separator : Model → Bool)
    (original : Model → Prop) (residual : Bool → Model → Prop)
    (hexact : ∀ m, original m ↔ residual (separator m) m)
    (false_refuted : ∀ m, separator m = false → ¬ residual false m)
    (true_refuted : ∀ m, separator m = true → ¬ residual true m) :
    ∀ m, ¬ original m := by
  intro m hm
  have hr : residual (separator m) m := (hexact m).mp hm
  cases hs : separator m with
  | false =>
      apply false_refuted m hs
      simpa only [hs] using hr
  | true =>
      apply true_refuted m hs
      simpa only [hs] using hr

-- These are the actual four DIMACS clauses of each affected source group,
-- with all occurrences of original DIMACS variable 1 replaced by `branch`.
def residualGroup0 (branch : Bool) (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 40)) || (!(bits.getLsbD 1)) || branch) &&
  ((!(bits.getLsbD 40)) || (!branch) || (bits.getLsbD 1)) &&
  ((!(bits.getLsbD 1)) || (!branch) || (bits.getLsbD 40)) &&
  (branch || (bits.getLsbD 1) || (bits.getLsbD 40))

def residualGroup1 (branch : Bool) (bits : BitVec 60) : Bool :=
  ((!(bits.getLsbD 39)) || (!(bits.getLsbD 38)) || branch) &&
  ((!(bits.getLsbD 39)) || (!branch) || (bits.getLsbD 38)) &&
  ((!(bits.getLsbD 38)) || (!branch) || (bits.getLsbD 39)) &&
  (branch || (bits.getLsbD 38) || (bits.getLsbD 39))

-- The remaining 38 groups contain no occurrence of DIMACS variable 1.
def residualCNF (branch : Bool) (bits : BitVec 60) : Prop :=
    residualGroup0 branch bits = true ∧
    residualGroup1 branch bits = true ∧
    sourceGroup2 bits = true ∧
    sourceGroup3 bits = true ∧
    sourceGroup4 bits = true ∧
    sourceGroup5 bits = true ∧
    sourceGroup6 bits = true ∧
    sourceGroup7 bits = true ∧
    sourceGroup8 bits = true ∧
    sourceGroup9 bits = true ∧
    sourceGroup10 bits = true ∧
    sourceGroup11 bits = true ∧
    sourceGroup12 bits = true ∧
    sourceGroup13 bits = true ∧
    sourceGroup14 bits = true ∧
    sourceGroup15 bits = true ∧
    sourceGroup16 bits = true ∧
    sourceGroup17 bits = true ∧
    sourceGroup18 bits = true ∧
    sourceGroup19 bits = true ∧
    sourceGroup20 bits = true ∧
    sourceGroup21 bits = true ∧
    sourceGroup22 bits = true ∧
    sourceGroup23 bits = true ∧
    sourceGroup24 bits = true ∧
    sourceGroup25 bits = true ∧
    sourceGroup26 bits = true ∧
    sourceGroup27 bits = true ∧
    sourceGroup28 bits = true ∧
    sourceGroup29 bits = true ∧
    sourceGroup30 bits = true ∧
    sourceGroup31 bits = true ∧
    sourceGroup32 bits = true ∧
    sourceGroup33 bits = true ∧
    sourceGroup34 bits = true ∧
    sourceGroup35 bits = true ∧
    sourceGroup36 bits = true ∧
    sourceGroup37 bits = true ∧
    sourceGroup38 bits = true ∧
    sourceGroup39 bits = true

-- An exact syntactic substitution, proved by kernel reduction.
theorem source_residual_exact (bits : BitVec 60) :
    sourceCNF bits ↔ residualCNF (bits.getLsbD 0) bits := by
  rfl

theorem assigned_residual_exact (bits : BitVec 60) (branch : Bool)
    (assigned : bits.getLsbD 0 = branch) :
    sourceCNF bits ↔ residualCNF branch bits := by
  rw [← assigned]
  exact source_residual_exact bits

-- Each branch is refuted through the already-proven *source-exact* G5
-- certificate, retaining the same original 160 clauses throughout.
theorem false_branch_refuted (bits : BitVec 60)
    (assigned : bits.getLsbD 0 = false) : ¬ residualCNF false bits := by
  intro hr
  have hs : sourceCNF bits := (assigned_residual_exact bits false assigned).mpr hr
  exact certificate_inconsistent bits ((source_iff_certificate bits).mp hs)

theorem true_branch_refuted (bits : BitVec 60)
    (assigned : bits.getLsbD 0 = true) : ¬ residualCNF true bits := by
  intro hr
  have hs : sourceCNF bits := (assigned_residual_exact bits true assigned).mpr hr
  exact certificate_inconsistent bits ((source_iff_certificate bits).mp hs)

theorem dubois20_one_bit_unsat_cover (bits : BitVec 60) :
    ¬ sourceCNF bits :=
  two_branch_unsat_cover (fun bits => bits.getLsbD 0)
    sourceCNF residualCNF source_residual_exact
    false_branch_refuted true_branch_refuted bits

end Witnora.TC063

#print axioms Witnora.TC063.dubois20_one_bit_unsat_cover
