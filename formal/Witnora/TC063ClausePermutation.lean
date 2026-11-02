import Witnora.ExactAffineMembership
import Witnora.SparseBridge

/-!
# TC-063 exact clause-coverage invariance under literal permutation

The boolean source-coverage gate must not depend on literal ordering:
a source clause subsumes a proposed forbidden clause exactly when it
subsumes any permutation of the same literal multiset. This is the first
checker-level lemma needed for full canonical affine witness normalization.
Semantic parity invariance alone does not establish this result.
-/

namespace Witnora.TC063ClausePermutation

open Witnora.Concrete
open Witnora.FiniteXor
open Witnora.G5Extraction

theorem clauseSubsumes_expected_perm
    (source expected other : List Literal)
    (hperm : expected.Perm other) :
    clauseSubsumes source expected = clauseSubsumes source other := by
  have heq : (fun lit : Literal => decide (lit ∈ expected)) =
      (fun lit : Literal => decide (lit ∈ other)) := by
    funext lit
    simp [hperm.mem_iff]
  unfold clauseSubsumes
  rw [heq]

theorem checkClauseCoverage_expected_perm
    (cnf : CNF) (expected other : List Literal)
    (hperm : expected.Perm other) :
    checkClauseCoverage cnf expected =
      checkClauseCoverage cnf other := by
  have heq :
      (fun source => clauseSubsumes source expected) =
      (fun source => clauseSubsumes source other) := by
    funext source
    exact clauseSubsumes_expected_perm source expected other hperm
  unfold checkClauseCoverage
  rw [heq]

theorem signForbiddenClause_perm
    (fixed other : List (Nat × Bool))
    (hperm : fixed.Perm other) :
    (signForbiddenClause fixed).Perm (signForbiddenClause other) := by
  unfold signForbiddenClause
  exact hperm.map _

theorem checkClauseCoverage_permuted_forbidden
    (cnf : CNF) (fixed other : List (Nat × Bool))
    (hperm : fixed.Perm other) :
    checkClauseCoverage cnf (signForbiddenClause fixed) =
      checkClauseCoverage cnf (signForbiddenClause other) := by
  exact checkClauseCoverage_expected_perm cnf _ _
    (signForbiddenClause_perm fixed other hperm)

/-- A permutation of variable positions can transport every same-length
    Boolean pattern, keeping the zipped variable/bit pairs and the bits
    themselves permuted. This requires no assignment enumeration. -/
theorem zip_pattern_transport
    {vars other : List Nat} (hperm : vars.Perm other)
    (bitsOther : List Bool) (hlen : bitsOther.length = other.length) :
    ∃ bits : List Bool,
      bits.length = vars.length ∧
      (List.zip vars bits).Perm (List.zip other bitsOther) ∧
      bits.Perm bitsOther := by
  induction hperm generalizing bitsOther with
  | nil =>
      cases bitsOther with
      | nil => exact ⟨[], rfl, List.Perm.nil, List.Perm.nil⟩
      | cons b rest => simp at hlen
  | @cons v xs ys hp ih =>
      cases bitsOther with
      | nil => simp at hlen
      | cons b bs =>
          have htail : bs.length = ys.length := by
            simpa using hlen
          obtain ⟨bits, hbLen, hpairs, hbits⟩ := ih bs htail
          refine ⟨b :: bits, ?_, ?_, ?_⟩
          · simp [hbLen]
          · simpa using (List.Perm.cons (v, b) hpairs)
          · exact List.Perm.cons b hbits
  | @swap x y xs =>
      cases bitsOther with
      | nil => simp at hlen
      | cons b rest =>
          cases rest with
          | nil => simp at hlen
          | cons d tail =>
              have htail : tail.length = xs.length := by
                simpa using hlen
              refine ⟨d :: b :: tail, by simp [htail], ?_, ?_⟩
              · simpa using (List.Perm.swap (x, b) (y, d)
                  (List.zip xs tail))
              · exact List.Perm.swap b d tail
  | @trans xs ys zs hxy hyz ihxy ihyz =>
      obtain ⟨mid, hmidlen, hmiddle, hmidbits⟩ :=
        ihyz bitsOther hlen
      obtain ⟨bits, hbitsLen, hfirst, hfirstBits⟩ :=
        ihxy mid hmidlen
      exact ⟨bits, hbitsLen, hfirst.trans hmiddle,
        hfirstBits.trans hmidbits⟩

/-- XOR of forbidden Boolean patterns is invariant under any reordering. -/
theorem parityBits_perm
    {bits other : List Bool} (hperm : bits.Perm other) :
    parityBits bits = parityBits other := by
  induction hperm with
  | nil => rfl
  | cons b hp ih =>
      simpa only [parityBits] using congrArg (Bool.xor b) ih
  | swap b d xs =>
      cases b <;> cases d <;> simp [parityBits, Bool.xor]
  | trans hp hq ihp ihq =>
      exact ihp.trans ihq

/-- Every forbidden assignment of the permuted variable row has an
    equally forbidden assignment of the original row with identical
    signed-literal coverage. Thus the actual Boolean extraction checker
    is sound under arbitrary variable-order permutations. -/
theorem checkPattern_true_of_perm
    (cnf : CNF) {vars other : List Nat}
    (hperm : vars.Perm other) (rhs : Bool)
    (hcheck : checkPattern cnf vars rhs = true) :
    checkPattern cnf other rhs = true := by
  unfold checkPattern at hcheck ⊢
  apply List.all_eq_true.mpr
  intro bitsOther hbadOther
  have hmemberOther : bitsOther ∈ allBits other.length :=
    (List.mem_filter.mp hbadOther).1
  have hwrongOther : parityBits bitsOther ≠ rhs := by
    simpa using (List.mem_filter.mp hbadOther).2
  have hlen : bitsOther.length = other.length :=
    Witnora.ExactSignedXorCNF.allBits_member_length
      other.length bitsOther hmemberOther
  obtain ⟨bits, hbitsLen, hpair, hbitsPerm⟩ :=
    zip_pattern_transport hperm bitsOther hlen
  have hmember : bits ∈ allBits vars.length := by
    simpa [hbitsLen] using allBits_complete bits
  have hwrong : parityBits bits ≠ rhs := by
    rw [parityBits_perm hbitsPerm]
    exact hwrongOther
  have hbad : bits ∈ generateForbiddenPatterns vars.length rhs := by
    simp [generateForbiddenPatterns, hmember, hwrong]
  have hcovered :
      checkClauseCoverage cnf
        (signForbiddenClause (List.zip vars bits)) = true :=
    List.all_eq_true.mp hcheck bits hbad
  rw [← checkClauseCoverage_permuted_forbidden cnf
    (List.zip vars bits) (List.zip other bitsOther) hpair]
  exact hcovered

/-- The source checker verdict itself is invariant under any variable
    permutation, not merely the mathematical parity equation. -/
theorem checkPattern_perm
    (cnf : CNF) {vars other : List Nat}
    (hperm : vars.Perm other) (rhs : Bool) :
    checkPattern cnf vars rhs = checkPattern cnf other rhs := by
  by_cases h : checkPattern cnf vars rhs = true
  · have hr := checkPattern_true_of_perm cnf hperm rhs h
    simp [h, hr]
  · have hl : checkPattern cnf vars rhs = false := by
      cases hx : checkPattern cnf vars rhs with
      | false => rfl
      | true => exact False.elim (h hx)
    have hr : checkPattern cnf other rhs = false := by
      cases hx : checkPattern cnf other rhs with
      | false => rfl
      | true =>
          have hback := checkPattern_true_of_perm cnf hperm.symm rhs hx
          exact False.elim (h hback)
    simp [hl, hr]

/-- A forbidden signed clause generated from a row stays present up
    to literal ordering after any variable permutation. This is the
    source-set bridge required to normalize full affine components. -/
theorem generated_signed_clause_perm_exists
    {vars other : List Nat} (hperm : vars.Perm other)
    (rhs : Bool) (clause : List Literal)
    (hmem : clause ∈ generateSignedClauses vars rhs) :
    ∃ translated ∈ generateSignedClauses other rhs,
      clause.Perm translated := by
  change clause ∈ (generateForbiddenPatterns vars.length rhs).map
    (fun bad => signForbiddenClause (List.zip vars bad)) at hmem
  obtain ⟨bad, hbad, rfl⟩ := List.mem_map.mp hmem
  have hbits : bad ∈ allBits vars.length :=
    (List.mem_filter.mp hbad).1
  have hwrong : parityBits bad ≠ rhs := by
    simpa using (List.mem_filter.mp hbad).2
  have hlen : bad.length = vars.length :=
    Witnora.ExactSignedXorCNF.allBits_member_length vars.length bad hbits
  obtain ⟨translatedBits, htranslatedLen, hpairs, hbitsPerm⟩ :=
    zip_pattern_transport hperm.symm bad hlen
  have htranslatedMember : translatedBits ∈ allBits other.length := by
    simpa [htranslatedLen] using allBits_complete translatedBits
  have htranslatedWrong : parityBits translatedBits ≠ rhs := by
    rw [parityBits_perm hbitsPerm]
    exact hwrong
  have hbadOther :
      translatedBits ∈ generateForbiddenPatterns other.length rhs := by
    simp [generateForbiddenPatterns, htranslatedMember, htranslatedWrong]
  refine ⟨signForbiddenClause (List.zip other translatedBits), ?_, ?_⟩
  · exact List.mem_map.mpr ⟨translatedBits, hbadOther, rfl⟩
  · exact (signForbiddenClause_perm _ _ hpairs).symm


/-- Boolean membership tests in a clause are unaffected by changing
    the order of its source literals. -/
private theorem all_perm_local {α : Type} (p : α → Bool)
    {xs ys : List α} (h : xs.Perm ys) :
    xs.all p = ys.all p := by
  induction h with
  | nil => rfl
  | cons _ _ ih => simp [List.all_cons, ih]
  | swap x y l =>
      simp [List.all_cons, Bool.and_comm, Bool.and_left_comm, Bool.and_assoc]
  | trans _ _ ih₁ ih₂ => exact ih₁.trans ih₂

theorem clauseSubsumes_source_perm
    (source translated expected : List Literal)
    (hperm : source.Perm translated) :
    clauseSubsumes source expected =
      clauseSubsumes translated expected := by
  exact all_perm_local (fun lit => decide (lit ∈ expected)) hperm

/-- The coverage gate depends only on which clauses are present
    up to literal permutation, in both directions. -/
theorem checkClauseCoverage_source_transport
    (original normalized : CNF)
    (hforward : ∀ clause ∈ original,
      ∃ translated ∈ normalized, clause.Perm translated)
    (hbackward : ∀ clause ∈ normalized,
      ∃ translated ∈ original, clause.Perm translated)
    (expected : List Literal) :
    checkClauseCoverage original expected =
      checkClauseCoverage normalized expected := by
  have htrue : checkClauseCoverage original expected = true ↔
      checkClauseCoverage normalized expected = true := by
    constructor
    · intro h
      obtain ⟨clause, hmem, hsub⟩ :=
        (List.any_eq_true).mp h
      obtain ⟨translated, hmemOther, hp⟩ := hforward clause hmem
      apply (List.any_eq_true).mpr
      refine ⟨translated, hmemOther, ?_⟩
      exact (clauseSubsumes_source_perm clause translated expected hp).symm ▸ hsub
    · intro h
      obtain ⟨clause, hmem, hsub⟩ :=
        (List.any_eq_true).mp h
      obtain ⟨translated, hmemOther, hp⟩ := hbackward clause hmem
      apply (List.any_eq_true).mpr
      refine ⟨translated, hmemOther, ?_⟩
      exact (clauseSubsumes_source_perm clause translated expected hp).symm ▸ hsub
  cases hx : checkClauseCoverage original expected with
  | false =>
      cases hy : checkClauseCoverage normalized expected with
      | false => rfl
      | true =>
          have hc := htrue.mpr hy
          simp [hx] at hc
  | true =>
      cases hy : checkClauseCoverage normalized expected with
      | false =>
          have hc := htrue.mp hx
          simp [hy] at hc
      | true => rfl


/-- Normalize only the representation order of a G5 row. -/
def normalizeRow (row : Witnora.G5Trace.Row) : Witnora.G5Trace.Row :=
  { row with coefficients := sortVariables row.coefficients }

private theorem expanded_cons_iff
    (row : Witnora.G5Trace.Row)
    (rows : List Witnora.G5Trace.Row) (clause : List Literal) :
    clause ∈ Witnora.ExactAffineMembership.expanded (row :: rows) ↔
      clause ∈ Witnora.ExactAffineMembership.rowClauses row ∨
      clause ∈ Witnora.ExactAffineMembership.expanded rows := by
  simp [Witnora.ExactAffineMembership.expanded]

theorem expanded_normalized_forward
    (rows : List Witnora.G5Trace.Row) (clause : List Literal)
    (hmem : clause ∈ Witnora.ExactAffineMembership.expanded rows) :
    ∃ translated ∈ Witnora.ExactAffineMembership.expanded
      (rows.map normalizeRow), clause.Perm translated := by
  induction rows with
  | nil =>
      simp [Witnora.ExactAffineMembership.expanded] at hmem
  | cons row rest ih =>
      have hsplit := (expanded_cons_iff row rest clause).mp hmem
      rcases hsplit with hrow | hrest
      · have hp : row.coefficients.Perm
            (sortVariables row.coefficients) :=
          (sortVariables_perm row.coefficients).symm
        obtain ⟨translated, htrans, hpClause⟩ :=
          generated_signed_clause_perm_exists hp row.rhs clause
            (by simpa [Witnora.ExactAffineMembership.rowClauses] using hrow)
        refine ⟨translated, ?_, hpClause⟩
        apply (expanded_cons_iff
          (normalizeRow row) (rest.map normalizeRow) translated).mpr
        left
        simpa [Witnora.ExactAffineMembership.rowClauses, normalizeRow]
          using htrans
      · obtain ⟨translated, htrans, hpClause⟩ := ih hrest
        refine ⟨translated, ?_, hpClause⟩
        apply (expanded_cons_iff
          (normalizeRow row) (rest.map normalizeRow) translated).mpr
        exact Or.inr htrans

theorem expanded_normalized_backward
    (rows : List Witnora.G5Trace.Row) (clause : List Literal)
    (hmem : clause ∈ Witnora.ExactAffineMembership.expanded
      (rows.map normalizeRow)) :
    ∃ translated ∈ Witnora.ExactAffineMembership.expanded rows,
      clause.Perm translated := by
  induction rows with
  | nil =>
      simp [Witnora.ExactAffineMembership.expanded] at hmem
  | cons row rest ih =>
      have hsplit : clause ∈ Witnora.ExactAffineMembership.rowClauses
          (normalizeRow row) ∨
          clause ∈ Witnora.ExactAffineMembership.expanded
            (rest.map normalizeRow) :=
        (expanded_cons_iff
          (normalizeRow row) (rest.map normalizeRow) clause).mp hmem
      rcases hsplit with hrow | hrest
      · have hp : (normalizeRow row).coefficients.Perm row.coefficients := by
          simpa [normalizeRow] using sortVariables_perm row.coefficients
        obtain ⟨translated, htrans, hpClause⟩ :=
          generated_signed_clause_perm_exists hp row.rhs clause
            (by simpa [Witnora.ExactAffineMembership.rowClauses, normalizeRow]
              using hrow)
        refine ⟨translated, ?_, hpClause⟩
        apply (expanded_cons_iff row rest translated).mpr
        left
        simpa [Witnora.ExactAffineMembership.rowClauses] using htrans
      · obtain ⟨translated, htrans, hpClause⟩ := ih hrest
        refine ⟨translated, ?_, hpClause⟩
        exact (expanded_cons_iff row rest translated).mpr (Or.inr htrans)

/-- The entire generated multirow CNF has the same Boolean source
    coverage checks after row-variable normalization. -/
theorem expanded_normalized_coverage
    (rows : List Witnora.G5Trace.Row) (expected : List Literal) :
    checkClauseCoverage (Witnora.ExactAffineMembership.expanded rows) expected =
      checkClauseCoverage
        (Witnora.ExactAffineMembership.expanded (rows.map normalizeRow))
        expected := by
  apply checkClauseCoverage_source_transport
  · exact expanded_normalized_forward rows
  · exact expanded_normalized_backward rows


/-- The supported-row gate is invariant under representation sorting.
    Sorting cannot evade the arity, distinctness or positivity checks. -/
theorem rowSupported_normalize
    (r : Nat) (row : Witnora.G5Trace.Row) :
    Witnora.ExactAffineMembership.rowSupported r row =
      Witnora.ExactAffineMembership.rowSupported r (normalizeRow row) := by
  have hp := sortVariables_perm row.coefficients
  have hlen : (sortVariables row.coefficients).length =
      row.coefficients.length := hp.length_eq
  have hnodup : (sortVariables row.coefficients).Nodup ↔
      row.coefficients.Nodup := hp.nodup_iff
  have hall : (sortVariables row.coefficients).all
      (fun v => decide (v > 0)) =
      row.coefficients.all (fun v => decide (v > 0)) :=
    all_perm_local (fun v : Nat => decide (v > 0)) hp
  simp [Witnora.ExactAffineMembership.rowSupported, normalizeRow,
    hlen, hnodup, hall]

private theorem all_normalized_rows (p : Witnora.G5Trace.Row → Bool)
    (hp : ∀ row, p row = p (normalizeRow row))
    (rows : List Witnora.G5Trace.Row) :
    rows.all p = (rows.map normalizeRow).all p := by
  induction rows with
  | nil => rfl
  | cons row rest ih =>
      simp [List.all_cons, hp row, ih]

theorem checkInitialRows_normalize
    (cnf : CNF) (rows : List Witnora.G5Trace.Row) :
    checkInitialRows cnf rows =
      checkInitialRows cnf (rows.map normalizeRow) := by
  exact all_normalized_rows
    (fun row => checkPattern cnf row.coefficients row.rhs)
    (fun row => by
      simpa [normalizeRow] using checkPattern_perm cnf
        ((sortVariables_perm row.coefficients).symm) row.rhs)
    rows

/-- All three executable semantic-affine validation gates agree
    before and after sorting each row's variables. -/
theorem checkSemanticExactAffine_normalize
    (r : Nat) (cnf : CNF) (rows : List Witnora.G5Trace.Row) :
    Witnora.ExactAffineMembership.checkSemanticExactAffine r cnf rows =
      Witnora.ExactAffineMembership.checkSemanticExactAffine
        r cnf (rows.map normalizeRow) := by
  have hs : rows.all (Witnora.ExactAffineMembership.rowSupported r) =
      (rows.map normalizeRow).all (Witnora.ExactAffineMembership.rowSupported r) :=
    all_normalized_rows _ (rowSupported_normalize r) rows
  have hi := checkInitialRows_normalize cnf rows
  have hc : cnf.all
      (checkClauseCoverage (Witnora.ExactAffineMembership.expanded rows)) =
      cnf.all (checkClauseCoverage
        (Witnora.ExactAffineMembership.expanded (rows.map normalizeRow))) := by
    have hf : (checkClauseCoverage
        (Witnora.ExactAffineMembership.expanded rows)) =
        (checkClauseCoverage
          (Witnora.ExactAffineMembership.expanded (rows.map normalizeRow))) := by
      funext clause
      exact expanded_normalized_coverage rows clause
    rw [hf]
  simp only [Witnora.ExactAffineMembership.checkSemanticExactAffine]
  rw [hs, hi, hc]


/-- The sparse canonical support contains exactly the input variables
    strictly below the exclusive upper bound. -/
theorem canonicalSupport_mem_iff
    (bound : Nat) (coeff : List Nat) (v : Nat) :
    v ∈ Witnora.SparseBridge.canonicalSupport bound coeff ↔
      v < bound ∧ v ∈ coeff := by
  induction bound with
  | zero =>
      simp [Witnora.SparseBridge.canonicalSupport]
  | succ n ih =>
      have hsplit :
          v ∈ Witnora.SparseBridge.canonicalSupport (n + 1) coeff ↔
          v ∈ Witnora.SparseBridge.canonicalSupport n coeff ∨
            (n ∈ coeff ∧ v = n) := by
        by_cases h : n ∈ coeff
        · simp [Witnora.SparseBridge.canonicalSupport, h, eq_comm]
        · simp [Witnora.SparseBridge.canonicalSupport, h]
      rw [hsplit, ih]
      constructor
      · rintro (⟨hlt, hmem⟩ | ⟨hmem, heq⟩)
        · exact ⟨Nat.lt_succ_of_lt hlt, hmem⟩
        · constructor
          · simpa only [heq] using Nat.lt_succ_self n
          · simpa only [heq] using hmem
      · rintro ⟨hlt, hmem⟩
        rcases Nat.lt_or_eq_of_le (Nat.le_of_lt_succ hlt) with hsmall | heq
        · exact Or.inl ⟨hsmall, hmem⟩
        · refine Or.inr ⟨?_, heq⟩
          simpa only [heq] using hmem

/-- Sparse canonical support never contains repeated coefficients. -/
theorem canonicalSupport_nodup (bound : Nat) (coeff : List Nat) :
    (Witnora.SparseBridge.canonicalSupport bound coeff).Nodup := by
  induction bound with
  | zero =>
      simp [Witnora.SparseBridge.canonicalSupport]
  | succ n ih =>
      by_cases h : n ∈ coeff
      · have hnot : n ∉ Witnora.SparseBridge.canonicalSupport n coeff := by
          intro hm
          have hlt := (canonicalSupport_mem_iff n coeff n).mp hm |>.1
          exact Nat.lt_irrefl n hlt
        have hn : (n :: Witnora.SparseBridge.canonicalSupport n coeff).Nodup :=
          List.nodup_cons.mpr ⟨hnot, ih⟩
        have hp : (n :: Witnora.SparseBridge.canonicalSupport n coeff).Perm
            (Witnora.SparseBridge.canonicalSupport n coeff ++ [n]) := by
          simpa using (List.perm_middle
            (l₁ := Witnora.SparseBridge.canonicalSupport n coeff)
            (l₂ := []) (a := n)).symm
        simpa [Witnora.SparseBridge.canonicalSupport, h] using hn.perm hp
      · simpa [Witnora.SparseBridge.canonicalSupport, h] using ih

/-- Distinct finite lists with exactly the same members are permutations.
    This local lemma avoids assuming a library theorem about set equality. -/
private theorem nodup_perm_of_mem_iff
    (left right : List Nat)
    (hnLeft : left.Nodup) (hnRight : right.Nodup)
    (hmem : ∀ v : Nat, v ∈ left ↔ v ∈ right) :
    left.Perm right := by
  induction left generalizing right with
  | nil =>
      cases right with
      | nil => exact List.Perm.nil
      | cons y rest =>
          have hc : y ∈ ([] : List Nat) := (hmem y).mpr (by simp)
          simp at hc
  | cons x xs ih =>
      have hxs : x ∉ xs ∧ xs.Nodup := List.nodup_cons.mp hnLeft
      have hx : x ∈ right := (hmem x).mp (by simp)
      apply (List.cons_perm_iff_perm_erase).mpr
      refine ⟨hx, ?_⟩
      apply ih (right.erase x) hxs.2 (hnRight.erase x)
      intro v
      rw [List.Nodup.mem_erase_iff hnRight]
      constructor
      · intro hv
        have hne : v ≠ x := by
          intro heq
          subst v
          exact hxs.1 hv
        exact ⟨hne, (hmem v).mp (by simp [hv])⟩
      · rintro ⟨hne, hv⟩
        have hc : v ∈ (x :: xs) := (hmem v).mpr hv
        rcases List.mem_cons.mp hc with heq | htail
        · exact False.elim (hne heq)
        · exact htail

/-- Under a sufficient exclusive bound, the canonical sparse support
    is a *permutation* of a supported duplicate-free input row. -/
theorem canonicalSupport_perm_of_covered
    (bound : Nat) (coeff : List Nat)
    (hn : coeff.Nodup)
    (hbounded : ∀ v ∈ coeff, v < bound) :
    (Witnora.SparseBridge.canonicalSupport bound coeff).Perm coeff := by
  apply nodup_perm_of_mem_iff _ _
    (canonicalSupport_nodup bound coeff) hn
  intro v
  rw [canonicalSupport_mem_iff]
  constructor
  · exact And.right
  · intro hv
    exact ⟨hbounded v hv, hv⟩

/-- Every finite coefficient list has a single exclusive bound large
    enough to contain its entire support. -/
theorem finite_support_bound_exists (coeff : List Nat) :
    ∃ bound : Nat, ∀ v ∈ coeff, v < bound := by
  induction coeff with
  | nil =>
      refine ⟨0, ?_⟩
      intro v hv
      simp at hv
  | cons x rest ih =>
      obtain ⟨bound, hb⟩ := ih
      refine ⟨max (x + 1) bound, ?_⟩
      intro v hv
      rcases List.mem_cons.mp hv with heq | hv
      · have hlt : v < x + 1 := by
          simpa only [heq] using Nat.lt_succ_self x
        exact Nat.lt_of_lt_of_le hlt
          (Nat.le_max_left (x + 1) bound)
      · exact Nat.lt_of_lt_of_le (hb v hv)
          (Nat.le_max_right (x + 1) bound)


/-- Row-wise equivalent reordering induces source-clause transport,
    even if each row chooses a different permutation. -/
theorem expanded_map_perm_forward
    (rows : List Witnora.G5Trace.Row)
    (transform : Witnora.G5Trace.Row → Witnora.G5Trace.Row)
    (hr : ∀ row ∈ rows, row.rhs = (transform row).rhs ∧
      row.coefficients.Perm (transform row).coefficients) :
    ∀ clause ∈ Witnora.ExactAffineMembership.expanded rows,
      ∃ translated ∈ Witnora.ExactAffineMembership.expanded (rows.map transform),
        clause.Perm translated := by
  induction rows with
  | nil =>
      intro clause hmem
      simp [Witnora.ExactAffineMembership.expanded] at hmem
  | cons row rest ih =>
      have hrow := hr row (by simp)
      have hrest : ∀ entry ∈ rest,
          entry.rhs = (transform entry).rhs ∧
          entry.coefficients.Perm (transform entry).coefficients := by
        intro entry hentry
        exact hr entry (by simp [hentry])
      intro clause hmem
      rcases (expanded_cons_iff row rest clause).mp hmem with hsource | htail
      · obtain ⟨translated, hgenerated, hpClause⟩ :=
          generated_signed_clause_perm_exists hrow.2 row.rhs clause
            (by simpa [Witnora.ExactAffineMembership.rowClauses] using hsource)
        refine ⟨translated, ?_, hpClause⟩
        apply (expanded_cons_iff
          (transform row) (rest.map transform) translated).mpr
        left
        simpa [Witnora.ExactAffineMembership.rowClauses, ← hrow.1]
          using hgenerated
      · obtain ⟨translated, htranslated, hpClause⟩ :=
          ih hrest clause htail
        refine ⟨translated, ?_, hpClause⟩
        exact (expanded_cons_iff
          (transform row) (rest.map transform) translated).mpr
          (Or.inr htranslated)

theorem expanded_map_perm_backward
    (rows : List Witnora.G5Trace.Row)
    (transform : Witnora.G5Trace.Row → Witnora.G5Trace.Row)
    (hr : ∀ row ∈ rows, row.rhs = (transform row).rhs ∧
      row.coefficients.Perm (transform row).coefficients) :
    ∀ clause ∈ Witnora.ExactAffineMembership.expanded (rows.map transform),
      ∃ translated ∈ Witnora.ExactAffineMembership.expanded rows,
        clause.Perm translated := by
  induction rows with
  | nil =>
      intro clause hmem
      simp [Witnora.ExactAffineMembership.expanded] at hmem
  | cons row rest ih =>
      have hrow := hr row (by simp)
      have hrest : ∀ entry ∈ rest,
          entry.rhs = (transform entry).rhs ∧
          entry.coefficients.Perm (transform entry).coefficients := by
        intro entry hentry
        exact hr entry (by simp [hentry])
      intro clause hmem
      rcases (expanded_cons_iff
        (transform row) (rest.map transform) clause).mp hmem with
        hsource | htail
      · obtain ⟨translated, hgenerated, hpClause⟩ :=
          generated_signed_clause_perm_exists
            hrow.2.symm (transform row).rhs clause
            (by simpa [Witnora.ExactAffineMembership.rowClauses] using hsource)
        refine ⟨translated, ?_, hpClause⟩
        apply (expanded_cons_iff row rest translated).mpr
        left
        simpa [Witnora.ExactAffineMembership.rowClauses, hrow.1]
          using hgenerated
      · obtain ⟨translated, htranslated, hpClause⟩ :=
          ih hrest clause htail
        refine ⟨translated, ?_, hpClause⟩
        exact (expanded_cons_iff row rest translated).mpr (Or.inr htranslated)

theorem expanded_map_perm_coverage
    (rows : List Witnora.G5Trace.Row)
    (transform : Witnora.G5Trace.Row → Witnora.G5Trace.Row)
    (hr : ∀ row ∈ rows, row.rhs = (transform row).rhs ∧
      row.coefficients.Perm (transform row).coefficients)
    (expected : List Literal) :
    checkClauseCoverage (Witnora.ExactAffineMembership.expanded rows) expected =
      checkClauseCoverage
        (Witnora.ExactAffineMembership.expanded (rows.map transform)) expected := by
  apply checkClauseCoverage_source_transport
  · exact expanded_map_perm_forward rows transform hr
  · exact expanded_map_perm_backward rows transform hr

example :
    checkClauseCoverage
      [[(1, true), (2, false)]]
      [(1, true), (2, false)] =
    checkClauseCoverage
      [[(1, true), (2, false)]]
      [(2, false), (1, true)] := by decide

#print axioms Witnora.TC063ClausePermutation.clauseSubsumes_expected_perm
#print axioms Witnora.TC063ClausePermutation.checkClauseCoverage_expected_perm
#print axioms Witnora.TC063ClausePermutation.signForbiddenClause_perm
#print axioms Witnora.TC063ClausePermutation.zip_pattern_transport
#print axioms Witnora.TC063ClausePermutation.parityBits_perm
#print axioms Witnora.TC063ClausePermutation.checkPattern_perm
#print axioms Witnora.TC063ClausePermutation.generated_signed_clause_perm_exists
#print axioms Witnora.TC063ClausePermutation.checkClauseCoverage_source_transport
#print axioms Witnora.TC063ClausePermutation.expanded_normalized_coverage
#print axioms Witnora.TC063ClausePermutation.checkSemanticExactAffine_normalize
#print axioms Witnora.TC063ClausePermutation.canonicalSupport_perm_of_covered
#print axioms Witnora.TC063ClausePermutation.finite_support_bound_exists
#print axioms Witnora.TC063ClausePermutation.expanded_map_perm_coverage

end Witnora.TC063ClausePermutation
