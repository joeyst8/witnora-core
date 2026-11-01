import Witnora.G14ConcreteBridge

/-!
# Adversarial G14 residual model-transfer experiment

Unlike the already checked two-branch UNSAT example, this source is SAT.
The separator x1 produces different residual requirements on x2 and x3,
with independent x4 in both branches. A deliberately wrong-branch
assignment demonstrates why the agreement premise cannot be dropped.
-/

namespace Witnora.G14ModelTransferExperiment

open Witnora.Concrete
open Witnora.G5Extraction
open Witnora.Conditioning
open Witnora.ComponentPartition
open Witnora.SeparatorAssignments

/-- (x1 OR x2) AND (NOT x1 OR x3) AND x4. -/
def original : CNF :=
  [[(1, true), (2, true)],
   [(1, false), (3, true)],
   [(4, true)]]

def falseBranch : List (Nat × Bool) := [(1, false)]
def trueBranch : List (Nat × Bool) := [(1, true)]

/-- The checked partition has two components in either branch. -/
def components (branch : List (Nat × Bool)) : List CNF :=
  if branch == falseBranch then
    [[[(2, true)]], [[(4, true)]]]
  else
    [[[(3, true)]], [[(4, true)]]]

theorem false_partition_checked :
    checkPartition
      (conditionCNF (fixedOf falseBranch) original)
      (components falseBranch) = true := by decide

theorem true_partition_checked :
    checkPartition
      (conditionCNF (fixedOf trueBranch) original)
      (components trueBranch) = true := by decide

theorem all_branches_checked :
    ∀ branch ∈ enumerate [1],
      checkPartition
        (conditionCNF (fixedOf branch) original)
        (components branch) = true := by
  intro branch hb
  have hcases : branch = falseBranch ∨ branch = trueBranch := by
    simpa [enumerate, falseBranch, trueBranch] using hb
  rcases hcases with hf | ht
  · subst branch
    exact false_partition_checked
  · subst branch
    exact true_partition_checked

/-- The full set of residual models is exactly the set of source models
    within every correctly assigned separator branch. -/
theorem every_branch_preserves_models
    (branch : List (Nat × Bool)) (hb : branch ∈ enumerate [1])
    (a : Nat → Bool) (hag : agreesWith (fixedOf branch) a) :
    CNFHolds original a ↔
      (components branch).all
        (fun c => c.all
          (fun clause => clause.any (signedLitTrue a))) = true := by
  exact conditioned_partition_correct
    (fixedOf branch) original (components branch)
    (all_branches_checked branch hb) a hag

/-- One satisfiable source assignment: x1=false, x2=true, x3=false,
    x4=true. Its proper false branch residual also holds. -/
def witness (v : Nat) : Bool := v == 2 || v == 4

theorem witness_satisfies_source :
    CNFHolds original witness := by decide

theorem witness_agrees_false :
    agreesWith (fixedOf falseBranch) witness := by
  intro v b hv
  have h : (v, b) = (1, false) := by
    cases v with
    | zero => simp [fixedOf, falseBranch] at hv
    | succ n =>
        by_cases heq : Nat.succ n = 1
        · have hv' : v = 1 := heq
          subst v
          simp [fixedOf, falseBranch] at hv
          cases hv
          rfl
        · simp [fixedOf, falseBranch, heq] at hv
  cases h

/-- A second assignment really is a model of the source CNF but not
    a model of the *wrong*, x1=false residual branch. -/
def wrongBranchWitness (v : Nat) : Bool :=
  v == 1 || v == 3 || v == 4

theorem wrong_branch_is_unsound_without_agreement :
    CNFHolds original wrongBranchWitness ∧
    ¬ CNFHolds ((components falseBranch).flatten)
      wrongBranchWitness := by decide

/-- A missing residual component is rejected, even if the other
    component itself is satisfiable. -/
theorem missing_component_rejected :
    checkPartition
      (conditionCNF (fixedOf falseBranch) original)
      [[[(2, true)]]] = false := by decide

/-- Substituting the true-branch component under the false branch fails. -/
theorem swapped_branch_rejected :
    checkPartition
      (conditionCNF (fixedOf falseBranch) original)
      (components trueBranch) = false := by decide

#print axioms Witnora.G14ModelTransferExperiment.every_branch_preserves_models
#print axioms Witnora.G14ModelTransferExperiment.wrong_branch_is_unsound_without_agreement

end Witnora.G14ModelTransferExperiment
