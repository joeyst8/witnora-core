import Witnora.G5Extraction

/-!
# Exact literal-level canonical XOR-CNF equivalence

Unlike an abstract excluded-pattern predicate, this checks the actual
generated list of signed literal clauses, for arbitrary variable lists,
Boolean assignments and right-hand sides. The generator enumerates wrong
parity patterns; its clauses use the same signed convention as CNF.
-/ 

namespace Witnora.ExactSignedXorCNF

open Witnora.Concrete
open Witnora.FiniteXor
open Witnora.Extraction
open Witnora.G5Extraction

def generatedSignedHolds (vars : List Nat) (rhs : Bool)
    (a : Nat → Bool) : Bool :=
  (generateSignedClauses vars rhs).all
    (fun clause => clause.any (signedLitTrue a))

theorem allBits_member_length (n : Nat) (bad : List Bool)
    (h : bad ∈ allBits n) : bad.length = n := by
  induction n generalizing bad with
  | zero =>
      simp [allBits] at h
      subst bad
      rfl
  | succ n ih =>
      simp only [allBits, List.mem_flatMap] at h
      obtain ⟨xs, hxs, hchoices⟩ := h
      have hchoices' : bad = false :: xs ∨ bad = true :: xs := by
        simpa using hchoices
      rcases hchoices' with heq | heq
      · simp [heq, ih xs hxs]
      · simp [heq, ih xs hxs]

theorem zip_agrees_implies_bits
    (vars : List Nat) (bad : List Bool) (a : Nat → Bool)
    (hlen : bad.length = vars.length)
    (hag : (List.zip vars bad).all (fun p => a p.1 == p.2) = true) :
    bad = vars.map a := by
  induction vars generalizing bad with
  | nil =>
      cases bad with
      | nil => rfl
      | cons b bs => simp at hlen
  | cons v vs ih =>
      cases bad with
      | nil => simp at hlen
      | cons b bs =>
          have hparts :
              (a v == b) = true ∧
              (List.zip vs bs).all (fun p => a p.1 == p.2) = true := by
            simpa only [List.zip_cons_cons, List.all_cons,
              Bool.and_eq_true] using hag
          have hbit : a v = b := by
            exact beq_iff_eq.mp hparts.1
          have htail : bs.length = vs.length := by
            simpa using hlen
          have hrest := ih bs htail hparts.2
          simp [hbit, hrest]

/-- Exact iff for the *concrete signed-literal CNF*, not only an abstract
    forbidden-assignment semantic specification. -/
theorem generatedSignedHolds_iff
    (vars : List Nat) (rhs : Bool) (a : Nat → Bool) :
    generatedSignedHolds vars rhs a = true ↔
      parityVars vars a = rhs := by
  constructor
  · intro hcnf
    by_cases hright : parityVars vars a = rhs
    · exact hright
    · let bad := vars.map a
      have hmem : bad ∈ allBits vars.length := by
        simpa [bad] using allBits_complete bad
      have hbad : bad ∈ generateForbiddenPatterns vars.length rhs := by
        simp [generateForbiddenPatterns, hmem, bad, parityBits_map, hright]
      have hclause : (signForbiddenClause (List.zip vars bad)).any
          (signedLitTrue a) = true := by
        have hmember : signForbiddenClause (List.zip vars bad) ∈
            generateSignedClauses vars rhs := by
          exact List.mem_map.mpr ⟨bad, hbad, rfl⟩
        exact List.all_eq_true.mp hcnf _ hmember
      have hfalse :
          (signForbiddenClause (List.zip vars bad)).any
              (signedLitTrue a) = false := by
        rw [signForbiddenClause_true]
        simp [bad, zip_map_agrees]
      rw [hfalse] at hclause
      cases hclause
  · intro hright
    unfold generatedSignedHolds generateSignedClauses
    simp only [List.all_map]
    apply List.all_eq_true.mpr
    intro bad hbad
    have hmem : bad ∈ allBits vars.length :=
      (List.mem_filter.mp hbad).1
    have hwrong : parityBits bad ≠ rhs := by
      have hp := (List.mem_filter.mp hbad).2
      simpa [generateForbiddenPatterns] using hp
    have hlen : bad.length = vars.length :=
      allBits_member_length vars.length bad hmem
    by_cases hag : (List.zip vars bad).all
        (fun p => a p.1 == p.2) = true
    · have heq := zip_agrees_implies_bits vars bad a hlen hag
      have hsame : parityBits bad = rhs := by
        rw [heq, parityBits_map]
        exact hright
      exact False.elim (hwrong hsame)
    · have hagFalse : (List.zip vars bad).all
          (fun p => a p.1 == p.2) = false := by
        cases hb : (List.zip vars bad).all
            (fun p => a p.1 == p.2) <;> simp_all
      rw [signForbiddenClause_true]
      simp [hagFalse]

example : generatedSignedHolds [1, 2] false
    (fun v => v == 1) = false := by decide

example : generatedSignedHolds [1, 2] false
    (fun _ => true) = true := by decide

#print axioms Witnora.ExactSignedXorCNF.generatedSignedHolds_iff

end Witnora.ExactSignedXorCNF
