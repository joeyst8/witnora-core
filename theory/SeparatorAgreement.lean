import Init

/-!
  Witnora TC-063: a small Lean 4 SAT-lifting foundation.

  Compilation status is established by running this file with Lean 4.15.

  This models truth of original clauses, complete component-clause coverage,
  and local/global assignment agreement. It does NOT model the Python parser,
  affine extraction certificates, UNSAT cover, or the full G14 constructor.
-/

namespace Witnora.SeparatorAgreement

universe u

abbrev Assignment (Var : Type u) := Var → Bool
abbrev Literal (Var : Type u) := Var × Bool
abbrev Clause (Var : Type u) := List (Literal Var)
abbrev CNF (Var : Type u) := List (Clause Var)

def ClauseSat {Var : Type u} (a : Assignment Var) (c : Clause Var) : Prop :=
  ∃ lit, lit ∈ c ∧ a lit.1 = lit.2

def CNFSat {Var : Type u} (a : Assignment Var) (f : CNF Var) : Prop :=
  ∀ c, c ∈ f → ClauseSat a c

def AgreesOn {Var : Type u} (localModel global : Assignment Var) (f : CNF Var) : Prop :=
  ∀ c, c ∈ f → ∀ lit, lit ∈ c → localModel lit.1 = global lit.1

theorem clauseSat_transport {Var : Type u}
    {a b : Assignment Var} {c : Clause Var}
    (hagree : ∀ lit, lit ∈ c → a lit.1 = b lit.1)
    (hsat : ClauseSat a c) : ClauseSat b c := by
  cases hsat with
  | intro lit hpair =>
    cases hpair with
    | intro hmem hvalue =>
      exact ⟨lit, hmem, (hagree lit hmem).symm.trans hvalue⟩

theorem cnfSat_transport {Var : Type u}
    {a b : Assignment Var} {f : CNF Var}
    (hagree : AgreesOn a b f) (hsat : CNFSat a f) : CNFSat b f := by
  intro c hmem
  exact clauseSat_transport (hagree c hmem) (hsat c hmem)

theorem cnfSat_of_component_cover {Var : Type u}
    {global : Assignment Var} {original left right : CNF Var}
    (hcover : ∀ c, c ∈ original → c ∈ left ∨ c ∈ right)
    (hleft : CNFSat global left) (hright : CNFSat global right) :
    CNFSat global original := by
  intro c hmem
  cases hcover c hmem with
  | inl hl => exact hleft c hl
  | inr hr => exact hright c hr

theorem satLiftTwoComponents {Var : Type u}
    {original left right : CNF Var}
    {leftModel rightModel global : Assignment Var}
    (hcover : ∀ c, c ∈ original → c ∈ left ∨ c ∈ right)
    (hleft : CNFSat leftModel left)
    (hright : CNFSat rightModel right)
    (hleftAgree : AgreesOn leftModel global left)
    (hrightAgree : AgreesOn rightModel global right) :
    CNFSat global original := by
  exact cnfSat_of_component_cover hcover
    (cnfSat_transport hleftAgree hleft)
    (cnfSat_transport hrightAgree hright)

/-! A clause conditioned on a partial separator assignment retains only
    literals whose variables have not been assigned. -/
def ResidualClause {Var : Type u} (fixed : Var → Option Bool)
    (c : Clause Var) : Clause Var :=
  c.filter (fun lit => (fixed lit.1).isNone)

def NoFixedLiteralTrue {Var : Type u} (fixed : Var → Option Bool)
    (global : Assignment Var) (c : Clause Var) : Prop :=
  ∀ lit, lit ∈ c → ∀ v, fixed lit.1 = some v → global lit.1 ≠ lit.2

def FixedAgrees {Var : Type u} (fixed : Var → Option Bool)
    (global : Assignment Var) : Prop :=
  ∀ x v, fixed x = some v → global x = v

def FixedLiteralTrue {Var : Type u} (fixed : Var → Option Bool)
    (c : Clause Var) : Prop :=
  ∃ lit, lit ∈ c ∧ fixed lit.1 = some lit.2

theorem fixedLiteralTrue_implies_original {Var : Type u}
    {fixed : Var → Option Bool} {global : Assignment Var} {c : Clause Var}
    (hagree : FixedAgrees fixed global)
    (htrue : FixedLiteralTrue fixed c) : ClauseSat global c := by
  obtain ⟨lit, hmem, hfixed⟩ := htrue
  exact ⟨lit, hmem, hagree lit.1 lit.2 hfixed⟩

theorem residualSat_implies_original {Var : Type u}
    {fixed : Var → Option Bool} {global : Assignment Var} {c : Clause Var}
    (h : ClauseSat global (ResidualClause fixed c)) : ClauseSat global c := by
  obtain ⟨lit, hmem, hval⟩ := h
  have hbase : lit ∈ c := (List.mem_filter.mp hmem).1
  exact ⟨lit, hbase, hval⟩

theorem originalSat_implies_residual {Var : Type u}
    {fixed : Var → Option Bool} {global : Assignment Var} {c : Clause Var}
    (hfalse : NoFixedLiteralTrue fixed global c)
    (h : ClauseSat global c) : ClauseSat global (ResidualClause fixed c) := by
  obtain ⟨lit, hmem, hval⟩ := h
  have hnone : (fixed lit.1).isNone = true := by
    cases hfix : fixed lit.1 with
    | none => rfl
    | some v =>
      have hcontra := hfalse lit hmem v hfix
      exact False.elim (hcontra hval)
  exact ⟨lit, List.mem_filter.mpr ⟨hmem, hnone⟩, hval⟩

theorem conditionedClause_equiv {Var : Type u}
    {fixed : Var → Option Bool} {global : Assignment Var} {c : Clause Var}
    (hfalse : NoFixedLiteralTrue fixed global c) :
    ClauseSat global (ResidualClause fixed c) ↔ ClauseSat global c := by
  constructor
  · exact residualSat_implies_original
  · exact originalSat_implies_residual hfalse

theorem conditionedClause_complete {Var : Type u}
    {fixed : Var → Option Bool} {global : Assignment Var} {c : Clause Var}
    (hagree : FixedAgrees fixed global) :
    ClauseSat global c ↔
      FixedLiteralTrue fixed c ∨ ClauseSat global (ResidualClause fixed c) := by
  constructor
  · intro hsat
    by_cases hfixed : FixedLiteralTrue fixed c
    · exact Or.inl hfixed
    · apply Or.inr
      apply originalSat_implies_residual
      · intro lit hmem v hv heq
        apply hfixed
        refine ⟨lit, hmem, ?_⟩
        have hag : global lit.1 = v := hagree lit.1 v hv
        have : v = lit.2 := hag.symm.trans heq
        exact this ▸ hv
      · exact hsat
  · intro h
    cases h with
    | inl htrue => exact fixedLiteralTrue_implies_original hagree htrue
    | inr hres => exact residualSat_implies_original hres

/-! Python's `_reduce_clause` omits clauses satisfied by fixed literals,
    and retains a residual clause for every other original clause. The
    following semantic predicate models precisely that rule, independently
    of the Python representation of its result. -/
def ConditionedSat {Var : Type u} (fixed : Var → Option Bool)
    (global : Assignment Var) (original : CNF Var) : Prop :=
  ∀ c, c ∈ original → ¬ FixedLiteralTrue fixed c →
    ClauseSat global (ResidualClause fixed c)

theorem conditionedCNF_equiv {Var : Type u}
    {fixed : Var → Option Bool} {global : Assignment Var}
    {original : CNF Var} (hagree : FixedAgrees fixed global) :
    CNFSat global original ↔ ConditionedSat fixed global original := by
  constructor
  · intro hsat c hmem hnot
    have hcase := (conditionedClause_complete (c := c) hagree).mp (hsat c hmem)
    cases hcase with
    | inl hfixed => exact False.elim (hnot hfixed)
    | inr hres => exact hres
  · intro hcond c hmem
    by_cases hfixed : FixedLiteralTrue fixed c
    · exact fixedLiteralTrue_implies_original hagree hfixed
    · exact residualSat_implies_original (hcond c hmem hfixed)

def BranchSat {Var : Type u} (fixed : Var → Option Bool)
    (original : CNF Var) : Prop :=
  ∃ global, FixedAgrees fixed global ∧ CNFSat global original

def ResidualBranchSat {Var : Type u} (fixed : Var → Option Bool)
    (original : CNF Var) : Prop :=
  ∃ global, FixedAgrees fixed global ∧ ConditionedSat fixed global original

theorem branchSat_iff_residualBranchSat {Var : Type u}
    {fixed : Var → Option Bool} {original : CNF Var} :
    BranchSat fixed original ↔ ResidualBranchSat fixed original := by
  constructor
  · intro h
    obtain ⟨global, hagree, hsat⟩ := h
    exact ⟨global, hagree, (conditionedCNF_equiv hagree).mp hsat⟩
  · intro h
    obtain ⟨global, hagree, hsat⟩ := h
    exact ⟨global, hagree, (conditionedCNF_equiv hagree).mpr hsat⟩

theorem branchUnsat_iff_residualBranchUnsat {Var : Type u}
    {fixed : Var → Option Bool} {original : CNF Var} :
    (¬ BranchSat fixed original) ↔
      (¬ ResidualBranchSat fixed original) := by
  constructor
  · intro h hres
    exact h ((branchSat_iff_residualBranchSat).mpr hres)
  · intro h hbranch
    exact h ((branchSat_iff_residualBranchSat).mp hbranch)

/-! A G14-style UNSAT cover is sound if the recorded branches cover every
    total assignment and each conditioned branch is UNSAT. Coverage is an
    explicit hypothesis, not inferred from the certificate metadata. -/
theorem unsat_of_complete_residual_branch_cover {Var : Type u}
    {original : CNF Var} {branches : List (Var → Option Bool)}
    (hcover : ∀ global : Assignment Var,
      ∃ fixed, fixed ∈ branches ∧ FixedAgrees fixed global)
    (hunsat : ∀ fixed, fixed ∈ branches →
      ¬ ResidualBranchSat fixed original) :
    ¬ ∃ global : Assignment Var, CNFSat global original := by
  intro hsat
  obtain ⟨global, hmodel⟩ := hsat
  obtain ⟨fixed, hmem, hagree⟩ := hcover global
  apply hunsat fixed hmem
  exact (branchSat_iff_residualBranchSat).mp ⟨global, hagree, hmodel⟩

/-! Explicit two-way enumeration of each separator variable. This mirrors
    `_all_assignments` in the Python builder, but the Python/Lean refinement
    obligation remains separate. -/
def ExtendFixed {Var : Type u} [DecidableEq Var] (v : Var) (b : Bool)
    (fixed : Var → Option Bool) : Var → Option Bool :=
  fun x => if x = v then some b else fixed x

def EnumerateSeparator {Var : Type u} [DecidableEq Var] :
    List Var → List (Var → Option Bool)
  | [] => [fun _ => none]
  | v :: rest =>
    (EnumerateSeparator rest).flatMap (fun fixed =>
      [ExtendFixed v false fixed, ExtendFixed v true fixed])

theorem extendFixed_agrees {Var : Type u} [DecidableEq Var]
    {fixed : Var → Option Bool} {global : Assignment Var} (v : Var)
    (hagree : FixedAgrees fixed global) :
    FixedAgrees (ExtendFixed v (global v) fixed) global := by
  intro x b hfixed
  by_cases hx : x = v
  · subst x
    simp [ExtendFixed] at hfixed
    exact hfixed
  · simp [ExtendFixed, hx] at hfixed
    exact hagree x b hfixed

theorem enumerateSeparator_covers {Var : Type u} [DecidableEq Var]
    (separator : List Var) (global : Assignment Var) :
    ∃ fixed, fixed ∈ EnumerateSeparator separator ∧
      FixedAgrees fixed global ∧
      ∀ v, v ∈ separator → fixed v = some (global v) := by
  induction separator with
  | nil =>
    refine ⟨fun _ => none, ?_, ?_, ?_⟩
    · simp [EnumerateSeparator]
    · intro x b h
      simp at h
    · intro v h
      cases h
  | cons v rest ih =>
    obtain ⟨fixed, hmem, hagree, hspecified⟩ := ih
    refine ⟨ExtendFixed v (global v) fixed, ?_,
      extendFixed_agrees v hagree, ?_⟩
    · cases hv : global v with
      | false =>
        apply List.mem_flatMap.mpr
        exact ⟨fixed, hmem, by simp [hv]⟩
      | true =>
        apply List.mem_flatMap.mpr
        exact ⟨fixed, hmem, by simp [hv]⟩
    · intro x hx
      simp only [List.mem_cons] at hx
      cases hx with
      | inl h =>
        subst x
        simp [ExtendFixed]
      | inr h =>
        by_cases heq : x = v
        · subst x
          simp [ExtendFixed]
        · simp [ExtendFixed, heq, hspecified x h]

theorem unsat_of_enumerated_residual_branches {Var : Type u}
    [DecidableEq Var] {original : CNF Var} (separator : List Var)
    (hunsat : ∀ fixed, fixed ∈ EnumerateSeparator separator →
      ¬ ResidualBranchSat fixed original) :
    ¬ ∃ global : Assignment Var, CNFSat global original := by
  apply unsat_of_complete_residual_branch_cover
    (branches := EnumerateSeparator separator)
  · intro global
    obtain ⟨fixed, hmem, hagree, _⟩ :=
      enumerateSeparator_covers separator global
    exact ⟨fixed, hmem, hagree⟩
  · exact hunsat

/-! Executable partial-clause reducer: `none` means some fixed literal is
    true, and `some residual` means the clause must still be checked. -/
def HasFixedTrue {Var : Type u} (fixed : Var → Option Bool)
    (c : Clause Var) : Bool :=
  c.any (fun lit => fixed lit.1 == some lit.2)

def ReduceClause {Var : Type u} (fixed : Var → Option Bool)
    (c : Clause Var) : Option (Clause Var) :=
  if HasFixedTrue fixed c then none else some (ResidualClause fixed c)

theorem hasFixedTrue_iff {Var : Type u} (fixed : Var → Option Bool)
    (c : Clause Var) :
    HasFixedTrue fixed c = true ↔ FixedLiteralTrue fixed c := by
  simp [HasFixedTrue, FixedLiteralTrue, List.any_eq_true]

theorem reduceClause_none_iff {Var : Type u} (fixed : Var → Option Bool)
    (c : Clause Var) :
    ReduceClause fixed c = none ↔ FixedLiteralTrue fixed c := by
  cases h : HasFixedTrue fixed c with
  | false =>
    have hnot : ¬ FixedLiteralTrue fixed c := by
      intro hf
      have ht := (hasFixedTrue_iff fixed c).mpr hf
      simp [h] at ht
    simp [ReduceClause, h, hnot]
  | true =>
    simp [ReduceClause, h, (hasFixedTrue_iff fixed c).mp h]

theorem reduceClause_semantics {Var : Type u}
    {fixed : Var → Option Bool} {global : Assignment Var}
    {c : Clause Var} (hagree : FixedAgrees fixed global) :
    ClauseSat global c ↔
      match ReduceClause fixed c with
      | none => True
      | some residual => ClauseSat global residual := by
  cases h : HasFixedTrue fixed c with
  | false =>
    have hnot : ¬ FixedLiteralTrue fixed c := by
      intro hfixed
      have : HasFixedTrue fixed c = true :=
        (hasFixedTrue_iff fixed c).mpr hfixed
      simp [h] at this
    simpa [ReduceClause, h] using
      (conditionedClause_equiv (fixed := fixed) (global := global)
        (c := c) (by
          intro lit hmem v hv heq
          apply hnot
          have hv' : global lit.1 = v := hagree lit.1 v hv
          have : v = lit.2 := hv'.symm.trans heq
          exact ⟨lit, hmem, this ▸ hv⟩)).symm
  | true =>
    have hfixed : FixedLiteralTrue fixed c :=
      (hasFixedTrue_iff fixed c).mp h
    have hsat : ClauseSat global c :=
      fixedLiteralTrue_implies_original hagree hfixed
    simp [ReduceClause, h, hsat]

-- Executable smoke examples corresponding to `_reduce_clause` behavior.
example : ReduceClause
    (fun x : Nat => if x = 1 then some true else none)
    [(1, true), (2, false)] = none := by decide

example : ReduceClause
    (fun x : Nat => if x = 1 then some true else none)
    [(1, false), (2, true)] = some [(2, true)] := by decide

example : ReduceClause
    (fun _ : Nat => none) ([] : Clause Nat) = some [] := by decide

def ReduceCNF {Var : Type u} (fixed : Var → Option Bool)
    (original : CNF Var) : CNF Var :=
  original.filterMap (ReduceClause fixed)

theorem reduceClause_some_characterization {Var : Type u}
    {fixed : Var → Option Bool} {c r : Clause Var}
    (h : ReduceClause fixed c = some r) :
    ¬ FixedLiteralTrue fixed c ∧ r = ResidualClause fixed c := by
  cases hb : HasFixedTrue fixed c with
  | true =>
    simp [ReduceClause, hb] at h
  | false =>
    have hnot : ¬ FixedLiteralTrue fixed c := by
      intro hf
      have ht := (hasFixedTrue_iff fixed c).mpr hf
      simp [hb] at ht
    have heq : ResidualClause fixed c = r := by
      simpa [ReduceClause, hb] using h
    exact ⟨hnot, heq.symm⟩

theorem reducedCNF_iff_conditioned {Var : Type u}
    {fixed : Var → Option Bool} {global : Assignment Var}
    {original : CNF Var} :
    CNFSat global (ReduceCNF fixed original) ↔
      ConditionedSat fixed global original := by
  constructor
  · intro hsat c hmem hnot
    have hfalse : HasFixedTrue fixed c = false := by
      cases hb : HasFixedTrue fixed c with
      | false => rfl
      | true => exact False.elim (hnot ((hasFixedTrue_iff fixed c).mp hb))
    have hreduce : ReduceClause fixed c = some (ResidualClause fixed c) := by
      simp [ReduceClause, hfalse]
    have hres : ResidualClause fixed c ∈ ReduceCNF fixed original := by
      exact List.mem_filterMap.mpr ⟨c, hmem, hreduce⟩
    exact hsat (ResidualClause fixed c) hres
  · intro hcond r hmem
    obtain ⟨c, hc, hreduced⟩ := List.mem_filterMap.mp hmem
    obtain ⟨hnot, heq⟩ := reduceClause_some_characterization hreduced
    exact heq ▸ hcond c hc hnot

theorem reduceCNF_preserves_satisfaction {Var : Type u}
    {fixed : Var → Option Bool} {global : Assignment Var}
    {original : CNF Var} (hagree : FixedAgrees fixed global) :
    CNFSat global original ↔ CNFSat global (ReduceCNF fixed original) := by
  exact (conditionedCNF_equiv hagree).trans (reducedCNF_iff_conditioned).symm

/-! Component ownership for a two-component residual decomposition. An
    unclassified clause is an explicit failure, never silently discarded. -/
def OwnerComponent {Var : Type u} (owner : Clause Var → Option Bool)
    (component : Bool) (residual : CNF Var) : CNF Var :=
  residual.filter (fun c => owner c == some component)

theorem ownedComponent_cover {Var : Type u}
    {owner : Clause Var → Option Bool} {residual : CNF Var}
    (hclassified : ∀ c, c ∈ residual → ∃ b, owner c = some b) :
    ∀ c, c ∈ residual →
      c ∈ OwnerComponent owner false residual ∨
      c ∈ OwnerComponent owner true residual := by
  intro c hmem
  obtain ⟨b, hb⟩ := hclassified c hmem
  cases b with
  | false =>
    left
    simp [OwnerComponent, hmem, hb]
  | true =>
    right
    simp [OwnerComponent, hmem, hb]

theorem ownedComponent_disjoint {Var : Type u}
    {owner : Clause Var → Option Bool} {residual : CNF Var}
    {c : Clause Var} :
    ¬ (c ∈ OwnerComponent owner false residual ∧
       c ∈ OwnerComponent owner true residual) := by
  intro h
  have hl := (List.mem_filter.mp h.1).2
  have hr := (List.mem_filter.mp h.2).2
  simp [OwnerComponent] at hl hr
  simp [hl] at hr

theorem originalSat_of_conditioned_owned_components {Var : Type u}
    {fixed : Var → Option Bool} {original : CNF Var}
    {owner : Clause Var → Option Bool}
    {global leftModel rightModel : Assignment Var}
    (hfixed : FixedAgrees fixed global)
    (hclassified : ∀ c, c ∈ ReduceCNF fixed original →
      ∃ b, owner c = some b)
    (hleft : CNFSat leftModel
      (OwnerComponent owner false (ReduceCNF fixed original)))
    (hright : CNFSat rightModel
      (OwnerComponent owner true (ReduceCNF fixed original)))
    (hleftAgree : AgreesOn leftModel global
      (OwnerComponent owner false (ReduceCNF fixed original)))
    (hrightAgree : AgreesOn rightModel global
      (OwnerComponent owner true (ReduceCNF fixed original))) :
    CNFSat global original := by
  apply (reduceCNF_preserves_satisfaction hfixed).mpr
  exact satLiftTwoComponents (ownedComponent_cover hclassified)
    hleft hright hleftAgree hrightAgree

end Witnora.SeparatorAgreement
