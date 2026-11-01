import Witnora.G5ResidualNormalForm

/-!
# Back-substitution foundation: toggling a pivot variable

A sparse parity equation containing v and measured with a bound above v
changes truth value when only a(v) is flipped. Every equation not
containing v is unaffected. These universal lemmas are the foundation
for constructing models by reverse traversal of Gaussian pivot rows.
-/

namespace Witnora.G5BackSubstitution

open Witnora.G5Trace
open Witnora.G5Certificate
open Witnora.SparseParity

/-- A single-bit assignment modification. -/
def flipAt (v : Nat) (a : Nat → Bool) : Nat → Bool :=
  fun w => if w = v then !a w else a w

theorem flipAt_other (v w : Nat) (a : Nat → Bool)
    (h : w ≠ v) : flipAt v a w = a w := by
  simp [flipAt, h]

theorem flipAt_self (v : Nat) (a : Nat → Bool) :
    flipAt v a v = !a v := by
  simp [flipAt]

/-- Finite XOR folding respects pointwise equality below its bound. -/
theorem xorFold_ext (n : Nat) (f g : Nat → Bool)
    (h : ∀ w, w < n → f w = g w) :
    xorFold n f = xorFold n g := by
  induction n with
  | zero => rfl
  | succ k ih =>
      have hp : ∀ w, w < k → f w = g w := by
        intro w hw
        exact h w (Nat.lt_trans hw (Nat.lt_succ_self k))
      rw [xorFold, xorFold, ih hp, h k (Nat.lt_succ_self k)]

/-- Flipping one indexed input below the bound complements the XOR fold. -/
theorem xorFold_flip_index
    (n v : Nat) (f : Nat → Bool) (hv : v < n) :
    xorFold n (fun w => if w = v then !f w else f w) =
      !(xorFold n f) := by
  induction n with
  | zero =>
      exact False.elim (Nat.not_lt_zero v hv)
  | succ k ih =>
      by_cases he : v = k
      · subst v
        have hprefix : xorFold k
            (fun w => if w = k then !f w else f w) =
            xorFold k f := by
          apply xorFold_ext k
          intro w hw
          have hn : w ≠ k := Nat.ne_of_lt hw
          simp [hn]
        simp only [xorFold, hprefix, if_pos rfl]
        cases hp : xorFold k f <;> cases hb : f k <;> decide
      · have hlt : v < k := by
          exact (Nat.lt_succ_iff_lt_or_eq.mp hv).resolve_right he
        have hk : k ≠ v := Ne.symm he
        simp only [xorFold, if_neg hk]
        rw [ih hlt]
        cases hp : xorFold k f <;> cases hb : f k <;> decide

/-- A sparse equation is insensitive to changes outside its support. -/
theorem sparseParity_congr_on_support
    (bound : Nat) (coeff : List Nat) (a b : Nat → Bool)
    (hag : ∀ v ∈ coeff, a v = b v) :
    sparseParity bound coeff a = sparseParity bound coeff b := by
  unfold sparseParity
  apply xorFold_ext bound
  intro w _
  by_cases hw : w ∈ coeff
  · simp [hw, hag w hw]
  · simp [hw]

/-- Flipping a present pivot variable below the sparse evaluation bound
    toggles the entire row parity. -/
theorem sparseParity_flip_present
    (bound v : Nat) (coeff : List Nat) (a : Nat → Bool)
    (hv : v < bound) (hmem : v ∈ coeff) :
    sparseParity bound coeff (flipAt v a) =
      !(sparseParity bound coeff a) := by
  unfold sparseParity
  have hfun : (fun w => (decide (w ∈ coeff)) && flipAt v a w) =
      (fun w => if w = v then !((decide (w ∈ coeff)) && a w)
        else (decide (w ∈ coeff)) && a w) := by
    funext w
    by_cases he : w = v
    · subst w
      simp [flipAt, hmem]
    · simp [flipAt, he]
  rw [hfun]
  exact xorFold_flip_index bound v
    (fun w => (decide (w ∈ coeff)) && a w) hv

/-- A row with an in-range pivot variable can always be made true by
    assigning that one variable appropriately. -/
theorem solve_one_pivot
    (bound v : Nat) (row : Row) (a : Nat → Bool)
    (hv : v < bound) (hmem : v ∈ row.coefficients) :
    ∃ b : Nat → Bool,
      (∀ w, w ≠ v → b w = a w) ∧ RowHolds bound row b := by
  by_cases h : RowHolds bound row a
  · exact ⟨a, by intros; rfl, h⟩
  · refine ⟨flipAt v a, ?_, ?_⟩
    · intro w hw
      exact flipAt_other v w a hw
    · unfold RowHolds at h ⊢
      rw [sparseParity_flip_present bound v row.coefficients a hv hmem]
      cases hp : sparseParity bound row.coefficients a <;>
        cases hr : row.rhs <;> simp_all

#print axioms Witnora.G5BackSubstitution.xorFold_flip_index
#print axioms Witnora.G5BackSubstitution.sparseParity_flip_present
#print axioms Witnora.G5BackSubstitution.solve_one_pivot

/-- Changing one variable does not affect a row that excludes it. -/
theorem rowHolds_preserved_outside
    (bound v : Nat) (row : Row) (a b : Nat → Bool)
    (hnot : v ∉ row.coefficients)
    (hagree : ∀ w, w ≠ v → b w = a w)
    (hholds : RowHolds bound row a) :
    RowHolds bound row b := by
  have heq : sparseParity bound row.coefficients b =
      sparseParity bound row.coefficients a := by
    apply sparseParity_congr_on_support bound row.coefficients b a
    intro w hw
    have hn : w ≠ v := by
      intro h
      subst w
      exact hnot hw
    exact hagree w hn
  unfold RowHolds at hholds ⊢
  exact heq.trans hholds

/-- An explicitly tagged list of pivots is triangular if each pivot
    variable occurs in its own row and no later pivot row mentions it. -/
def Triangular : List (Nat × Row) → Prop
  | [] => True
  | (v, row) :: rest =>
      v ∈ row.coefficients ∧
      (∀ entry ∈ rest, v ∉ entry.2.coefficients) ∧
      Triangular rest

/-- Every triangular row system has a simultaneous satisfying assignment,
    provided each pivot variable lies inside the sparse-parity bound.
    Back-substitution solves the tail first, then adjusts only the head
    pivot variable, leaving the tail solutions unchanged. -/
theorem triangular_has_model
    (bound : Nat) (pivots : List (Nat × Row))
    (htri : Triangular pivots)
    (hbound : ∀ entry ∈ pivots, entry.1 < bound) :
    ∃ a : Nat → Bool,
      ∀ entry ∈ pivots, RowHolds bound entry.2 a := by
  induction pivots with
  | nil =>
      exact ⟨fun _ => false, by simp⟩
  | cons entry tail ih =>
      cases entry with
      | mk v row =>
          have hp : v ∈ row.coefficients := htri.1
          have hdis : ∀ entry ∈ tail,
              v ∉ entry.2.coefficients := htri.2.1
          have ht : Triangular tail := htri.2.2
          have htb : ∀ entry ∈ tail, entry.1 < bound := by
            intro entry hmem
            exact hbound entry (by simp [hmem])
          obtain ⟨a, ha⟩ := ih ht htb
          have hv : v < bound := hbound (v, row) (by simp)
          obtain ⟨b, hagree, hrow⟩ :=
            solve_one_pivot bound v row a hv hp
          refine ⟨b, ?_⟩
          intro entry hmem
          rcases List.mem_cons.mp hmem with heq | htail
          · subst entry
            exact hrow
          · exact rowHolds_preserved_outside bound v entry.2
              a b (hdis entry htail) hagree (ha entry htail)

#print axioms Witnora.G5BackSubstitution.triangular_has_model

/-- The same deterministic elimination driver with every selected pivot
    tagged by its variable. This records data used by back-substitution
    without changing the underlying elimination algorithm. -/
def eliminateTagged : List Nat → List Row → List (Nat × Row) × List Row
  | [], rows => ([], rows)
  | v :: remaining, rows =>
      match Witnora.G5TerminatingPivot.extractPivot v rows with
      | none => eliminateTagged remaining rows
      | some (pivot, otherRows) =>
          let (pivots, residual) :=
            eliminateTagged remaining
              (Witnora.G5TerminatingPivot.eliminatePass v pivot otherRows)
          ((v, pivot) :: pivots, residual)

/-- Tagging pivots is observationally equivalent to the verified untagged
    elimination driver, including the exact residual row sequence. -/
theorem eliminateTagged_matches_driver
    (vars : List Nat) (rows : List Row) :
    ((eliminateTagged vars rows).1.map Prod.snd,
      (eliminateTagged vars rows).2) =
      Witnora.G5TerminatingPivot.eliminateVariables vars rows := by
  induction vars generalizing rows with
  | nil =>
      rfl
  | cons v rest ih =>
      cases hp : Witnora.G5TerminatingPivot.extractPivot v rows with
      | none =>
          simpa [eliminateTagged,
            Witnora.G5TerminatingPivot.eliminateVariables, hp]
            using ih rows
      | some result =>
          cases result with
          | mk pivot others =>
              cases ht : eliminateTagged rest
                  (Witnora.G5TerminatingPivot.eliminatePass v pivot others) with
              | mk pivots residual =>
                  have hrec := ih
                    (Witnora.G5TerminatingPivot.eliminatePass v pivot others)
                  simp only [ht] at hrec
                  simpa [eliminateTagged,
                    Witnora.G5TerminatingPivot.eliminateVariables,
                    hp, ht] using congrArg
                    (fun p : List Row × List Row =>
                      (pivot :: p.1, p.2)) hrec

#print axioms Witnora.G5BackSubstitution.eliminateTagged_matches_driver

/-- An absent variable remains absent from all *tagged* retained pivots. -/
theorem tagged_preserves_absence
    (vars : List Nat) (rows : List Row) (v : Nat)
    (ha : Witnora.G5ResidualNormalForm.AbsentFrom v rows) :
    ∀ entry ∈ (eliminateTagged vars rows).1,
      v ∉ entry.2.coefficients := by
  have hmodels :=
    Witnora.G5ResidualNormalForm.eliminateVariables_preserves_absence
      vars rows v ha
  have hmatch := eliminateTagged_matches_driver vars rows
  have hmap : (eliminateTagged vars rows).1.map Prod.snd =
      (Witnora.G5TerminatingPivot.eliminateVariables vars rows).1 :=
    congrArg Prod.fst hmatch
  intro entry hentry
  have hmem : entry.2 ∈ (eliminateTagged vars rows).1.map Prod.snd :=
    List.mem_map.mpr ⟨entry, hentry, rfl⟩
  rw [hmap] at hmem
  exact hmodels entry.2 (List.mem_append.mpr (Or.inl hmem))

/-- The actual elimination driver produces a triangular list of pivots:
    every pivot contains its tag, and all subsequently retained pivots
    exclude that earlier pivot variable. -/
theorem eliminateTagged_triangular
    (vars : List Nat) (rows : List Row) :
    Triangular (eliminateTagged vars rows).1 := by
  induction vars generalizing rows with
  | nil =>
      trivial
  | cons v rest ih =>
      cases hp : Witnora.G5TerminatingPivot.extractPivot v rows with
      | none =>
          simpa [eliminateTagged, hp] using ih rows
      | some result =>
          cases result with
          | mk pivot others =>
              let remainingRows :=
                Witnora.G5TerminatingPivot.eliminatePass v pivot others
              have hvar : v ∈ pivot.coefficients :=
                Witnora.G5ResidualNormalForm.extractPivot_some_contains
                  v rows pivot others hp
              have hpass : Witnora.G5ResidualNormalForm.AbsentFrom v
                  remainingRows := by
                intro row hr
                exact Witnora.G5TerminatingPivot.eliminatePass_clears_variable
                  v pivot others hvar row hr
              have htail := ih remainingRows
              have habsent := tagged_preserves_absence rest remainingRows v hpass
              cases ht : eliminateTagged rest remainingRows with
              | mk pivots residual =>
                  have htri : Triangular pivots := by
                    simpa [ht] using htail
                  have hdis : ∀ entry ∈ pivots,
                      v ∉ entry.2.coefficients := by
                    simpa [ht] using habsent
                  have hresult : Triangular ((v, pivot) :: pivots) :=
                    ⟨hvar, hdis, htri⟩
                  simpa [eliminateTagged, hp, remainingRows, ht]
                    using hresult

#print axioms Witnora.G5BackSubstitution.tagged_preserves_absence
#print axioms Witnora.G5BackSubstitution.eliminateTagged_triangular

/-- Every tag emitted by the driver is one of the requested variables. -/
theorem tagged_pivots_from_schedule
    (vars : List Nat) (rows : List Row) :
    ∀ entry ∈ (eliminateTagged vars rows).1, entry.1 ∈ vars := by
  induction vars generalizing rows with
  | nil =>
      intro entry h
      simp [eliminateTagged] at h
  | cons v rest ih =>
      cases hp : Witnora.G5TerminatingPivot.extractPivot v rows with
      | none =>
          intro entry h
          have hrest : entry ∈ (eliminateTagged rest rows).1 := by
            simpa [eliminateTagged, hp] using h
          exact List.mem_cons_of_mem v (ih rows entry hrest)
      | some result =>
          cases result with
          | mk pivot others =>
              cases ht : eliminateTagged rest
                  (Witnora.G5TerminatingPivot.eliminatePass v pivot others) with
              | mk pivots residual =>
                  intro entry h
                  have hmem : entry ∈ (v, pivot) :: pivots := by
                    simpa [eliminateTagged, hp, ht] using h
                  rcases List.mem_cons.mp hmem with heq | htail
                  · subst entry
                    simp
                  · have hrest : entry.1 ∈ rest := by
                      apply ih (Witnora.G5TerminatingPivot.eliminatePass
                        v pivot others) entry
                      simpa [ht] using htail
                    exact List.mem_cons_of_mem v hrest

/-- Universal contradiction-discovery theorem for complete in-range
    variable schedules. If the original row system is UNSAT, elimination
    must leave a true RHS in the zero-support residual system. This is
    the converse of the existing contradiction-soundness result. -/
theorem unsat_forces_residual_contradiction
    (bound : Nat) (vars : List Nat) (rows : List Row)
    (hcoverage : ∀ row ∈ rows,
      ∀ v ∈ row.coefficients, v ∈ vars)
    (hvars : ∀ v ∈ vars, v < bound)
    (hunsat : ¬ ∃ a : Nat → Bool,
      ∀ row ∈ rows, RowHolds bound row a) :
    ∃ row ∈ (Witnora.G5TerminatingPivot.eliminateVariables vars rows).2,
      row.coefficients = [] ∧ row.rhs = true := by
  classical
  by_cases htrue : ∃ row ∈
      (Witnora.G5TerminatingPivot.eliminateVariables vars rows).2,
      row.rhs = true
  · obtain ⟨row, hr, hright⟩ := htrue
    exact ⟨row, hr,
      Witnora.G5ResidualNormalForm.complete_schedule_residual_empty_support
        vars rows hcoverage row hr, hright⟩
  · exfalso
    have hfalse : ∀ row ∈
        (Witnora.G5TerminatingPivot.eliminateVariables vars rows).2,
        row.rhs = false := by
      intro row hr
      cases hv : row.rhs with
      | false => rfl
      | true => exact False.elim (htrue ⟨row, hr, hv⟩)
    have htri := eliminateTagged_triangular vars rows
    have htags : ∀ entry ∈ (eliminateTagged vars rows).1,
        entry.1 < bound := by
      intro entry he
      exact hvars entry.1
        (tagged_pivots_from_schedule vars rows entry he)
    obtain ⟨a, hpivots⟩ :=
      triangular_has_model bound (eliminateTagged vars rows).1 htri htags
    have htagmatch := eliminateTagged_matches_driver vars rows
    have htagrows :
        (eliminateTagged vars rows).1.map Prod.snd =
          (Witnora.G5TerminatingPivot.eliminateVariables vars rows).1 :=
      congrArg Prod.fst htagmatch
    have hresidual :
        (eliminateTagged vars rows).2 =
          (Witnora.G5TerminatingPivot.eliminateVariables vars rows).2 :=
      congrArg Prod.snd htagmatch
    have hfinal : ∀ row ∈
        (Witnora.G5TerminatingPivot.eliminateVariables vars rows).1 ++
        (Witnora.G5TerminatingPivot.eliminateVariables vars rows).2,
        RowHolds bound row a := by
      intro row hr
      rcases List.mem_append.mp hr with hp | hres
      · rw [← htagrows] at hp
        obtain ⟨entry, he, heq⟩ := List.mem_map.mp hp
        subst row
        exact hpivots entry he
      · have hcoeff :=
          Witnora.G5ResidualNormalForm.complete_schedule_residual_empty_support
            vars rows hcoverage row hres
        have hright := hfalse row hres
        unfold RowHolds
        simp [hcoeff, hright, sparseParity_empty]
    have hsource :=
      (Witnora.G5TerminatingPivot.eliminateVariables_models_iff
        bound vars rows a).mpr hfinal
    exact hunsat ⟨a, hsource⟩

#print axioms Witnora.G5BackSubstitution.unsat_forces_residual_contradiction

/-- Exact completeness of contradiction *discovery* for the verified
    finite sparse Gaussian-elimination driver. An accepted indexed G5
    DAG trace constructor is a separate, still-open proof obligation. -/
theorem residual_contradiction_iff_unsat
    (bound : Nat) (vars : List Nat) (rows : List Row)
    (hcoverage : ∀ row ∈ rows,
      ∀ v ∈ row.coefficients, v ∈ vars)
    (hvars : ∀ v ∈ vars, v < bound) :
    (∃ row ∈
        (Witnora.G5TerminatingPivot.eliminateVariables vars rows).2,
        row.coefficients = [] ∧ row.rhs = true) ↔
    (¬ ∃ a : Nat → Bool,
      ∀ row ∈ rows, RowHolds bound row a) := by
  constructor
  · rintro ⟨row, hmem, hcoeff, hrhs⟩
    exact Witnora.G5TerminatingPivot.eliminateVariables_contradiction_unsat
      bound vars rows
      ⟨row, List.mem_append.mpr (Or.inr hmem), hcoeff, hrhs⟩
  · intro hunsat
    exact unsat_forces_residual_contradiction
      bound vars rows hcoverage hvars hunsat

#print axioms Witnora.G5BackSubstitution.residual_contradiction_iff_unsat

end Witnora.G5BackSubstitution
