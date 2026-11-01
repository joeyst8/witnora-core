import Witnora.G14PythonConditioningLoop

/-!
# Universal G14 clause routing with no loss or duplication

The residual components are constructed by routing every clause to its
first matching component ID. The only premise is that every clause's
owner is present in the provided finite index list. This proof does not
assume that Python's primal graph finds the correct owner; that structural
correspondence remains a separate obligation.
-/

namespace Witnora.G14ComponentRouting

open Witnora.Concrete
open Witnora.ComponentPartition
open Witnora.G5Extraction

/-- Split clauses by a decidable predicate, retaining original order. -/
theorem filter_split_perm {α : Type} (xs : List α)
    (p : α → Bool) :
    ((xs.filter p) ++ (xs.filter (fun x => !p x))).Perm xs := by
  induction xs with
  | nil => simp
  | cons x rest ih =>
      cases hp : p x with
      | true =>
          simpa [List.filter_cons, hp] using (List.Perm.cons x ih)
      | false =>
          have hmove :
              (rest.filter p ++ x :: rest.filter (fun y => !p y)).Perm
                (x :: rest.filter p ++ rest.filter (fun y => !p y)) :=
            (List.Perm.middle x (rest.filter p)
              (rest.filter (fun y => !p y))).symm
          simpa [List.filter_cons, hp] using
            hmove.trans (List.Perm.cons x ih)

/-- Route residual clauses to the first component matching their owner.
    Rows that remain unassigned after all listed IDs are not emitted. -/
def routeClauses (owner : List Literal → Nat) :
    List Nat → CNF → List CNF
  | [], _ => []
  | component :: rest, clauses =>
      clauses.filter (fun c => decide (owner c = component)) ::
      routeClauses owner rest
        (clauses.filter (fun c => decide (owner c ≠ component)))

/-- Every routed residual clause belongs to its declared component. -/
theorem routeClauses_head_owner
    (owner : List Literal → Nat) (component : Nat) (rest : List Nat)
    (clauses : CNF) (clause : List Literal)
    (h : clause ∈ (routeClauses owner (component :: rest) clauses).head!) :
    owner clause = component := by
  have hm : clause ∈ clauses.filter
      (fun c => decide (owner c = component)) := by
    simpa [routeClauses] using h
  exact of_decide_true (List.mem_filter.mp hm).2

/-- A finite list of owners covers all the initial residual clauses. -/
def OwnersCovered (owner : List Literal → Nat)
    (indices : List Nat) (clauses : CNF) : Prop :=
  ∀ clause ∈ clauses, owner clause ∈ indices

/-- Under the explicit owner-coverage premise, routing creates exactly
    the input clause multiset, including duplicate or empty clauses.
    No satisfiability test or clause-count assumption is used. -/
theorem routeClauses_perm
    (owner : List Literal → Nat) (indices : List Nat)
    (clauses : CNF)
    (hcover : OwnersCovered owner indices clauses) :
    (routeClauses owner indices clauses).flatten.Perm clauses := by
  induction indices generalizing clauses with
  | nil =>
      have hempty : clauses = [] := by
        cases clauses with
        | nil => rfl
        | cons clause rest =>
            have hmem := hcover clause (by simp)
            simp [OwnersCovered] at hmem
      simp [routeClauses, hempty]
  | cons component rest ih =>
      let p : List Literal → Bool :=
        fun clause => decide (owner clause = component)
      let remainder := clauses.filter (fun clause => !p clause)
      have hrest : OwnersCovered owner rest remainder := by
        intro clause hm
        have hparts := List.mem_filter.mp hm
        have hnot : owner clause ≠ component := by
          have hfalse : p clause = false := by
            cases hp : p clause <;> simp_all
          simpa [p] using hfalse
        have horig := hcover clause hparts.1
        exact (List.mem_cons.mp horig).resolve_left hnot
      have htail := ih remainder hrest
      calc
        (routeClauses owner (component :: rest) clauses).flatten =
            clauses.filter p ++ (routeClauses owner rest remainder).flatten := by
              simp [routeClauses, p, remainder]
        _ ~ clauses.filter p ++ remainder := by
              exact List.Perm.append_left (clauses.filter p) htail
        _ ~ clauses := filter_split_perm clauses p

/-- The exact original multiplicities make the existing production
    certificate checker accept every fully covered routing result. -/
theorem routed_partition_check_passes
    (owner : List Literal → Nat) (indices : List Nat)
    (clauses : CNF)
    (hcover : OwnersCovered owner indices clauses) :
    checkPartition clauses (routeClauses owner indices clauses) = true := by
  exact decide_eq_true (routeClauses_perm owner indices clauses hcover).symm

/-- Every model of a fully routed residual matches exactly all component
    models, for arbitrary owners, CNFs and finite index lists. -/
theorem routed_models_iff
    (owner : List Literal → Nat) (indices : List Nat)
    (clauses : CNF)
    (hcover : OwnersCovered owner indices clauses)
    (a : Nat → Bool) :
    CNFHolds clauses a ↔
      (routeClauses owner indices clauses).all
        (fun c => c.all (fun clause => clause.any (signedLitTrue a))) = true :=
  checkPartition_sound clauses (routeClauses owner indices clauses)
    (routed_partition_check_passes owner indices clauses hcover) a

/-- Routing preserves duplicate clauses as separate occurrences. -/
example :
    routeClauses (fun _ => 1) [1, 2]
      [[(1, true)], [(1, true)], []] =
      [[[(1, true)], [(1, true)], []], []] := by decide

#print axioms Witnora.G14ComponentRouting.routeClauses_perm
#print axioms Witnora.G14ComponentRouting.routed_models_iff

end Witnora.G14ComponentRouting
